#!/usr/bin/env python3
"""Run the ECM stats workers with a deterministic clock using the compiler's ABI."""
import argparse
from pathlib import Path
import subprocess
import tempfile


def extract(text, signature):
    start = text.index(signature)
    end = text.index('{', start) + 1
    depth = 1
    while depth:
        depth += (text[end] == '{') - (text[end] == '}')
        end += 1
    return text[start:end]


FIXTURE = r'''
#include <assert.h>
#include <limits.h>
#include <stdint.h>
#include <stdio.h>
#define PAGE_SIZE 4096
#define ECM_NSS_IPVX_STATS_SYNC_PERIOD 100U
#define ECM_NSS_IPVX_STATS_SYNC_UDELAY 4000U
#define NSS_TX_SUCCESS 0
#define DEBUG_TRACE(...) ((void)0)
#define spin_lock_bh(lock) ((void)(lock))
#define spin_unlock_bh(lock) ((void)(lock))
#define time_after(a, b) ((long)((unsigned long)(b) - (unsigned long)(a)) < 0)
#define time_is_after_jiffies(a) time_after(a, jiffies)
typedef int nss_tx_status_t;
typedef uint64_t ktime_t;
typedef uint64_t u64;
#define NSEC_PER_USEC 1000U
#define TASK_IDLE 0x402U
#define HRTIMER_MODE_ABS 1
#define __set_current_state(value) (task_state = (value))
struct work_struct { int unused; };
struct nss_ipvX_conn_sync_many_msg { unsigned count, index; };
struct nss_ipvX_msg { struct { struct nss_ipvX_conn_sync_many_msg conn_stats_many; } msg; };
static struct nss_ipvX_msg message;
static struct nss_ipvX_msg *ecm_nss_ipvX_sync_req_msg = &message;
static unsigned long jiffies, ecm_nss_ipvX_next_req_time, ecm_nss_ipvX_roll_check_jiffies;
static int ecm_nss_ipvX_accelerated_count, ecm_ipvX_terminate_pending;
static int ecm_nss_ipvX_lock, ecm_nss_ipvX_workqueue, ecm_nss_ipvX_work;
static int ecm_nss_ipvX_nss_ipvX_mgr;
static unsigned ecm_nss_ipvX_stats_request_success, ecm_nss_ipvX_stats_request_fail;
static unsigned queued, sent, paced, tx_fail;
static unsigned long delay;
static uint64_t clock_us;
static unsigned task_state, spurious_wakeups, timer_calls;
static int queue_delayed_work(int queue, int *work, unsigned long wait)
{
    (void)queue; (void)work;
    assert(wait > 0 && wait <= 100);
    queued++; delay = wait;
    return 1;
}
static ktime_t ktime_get(void)
{
    paced++;
    return clock_us;
}
static ktime_t ktime_add_us(ktime_t now, unsigned long us) { return now + us; }
static int schedule_hrtimeout_range(ktime_t *expires, u64 slack, int mode)
{
    assert(task_state == TASK_IDLE && mode == HRTIMER_MODE_ABS);
    assert(slack == 100U * NSEC_PER_USEC && *expires > clock_us);
    timer_calls++;
    task_state = 0;
    if (spurious_wakeups) {
        spurious_wakeups--;
        clock_us++;
        return -1;
    }
    assert(*expires - clock_us <= 3900);
    clock_us = *expires;
    return 0;
}
static nss_tx_status_t nss_ipvX_tx_with_size(int mgr, struct nss_ipvX_msg *msg, int size)
{
    (void)mgr;
    assert(msg == &message && size == PAGE_SIZE);
    sent++;
    return tx_fail ? 1 : NSS_TX_SUCCESS;
}
/* An ordinary msleep() is a regression, even if requests still progress. */
static void msleep(unsigned value) __attribute__((unused));
static void msleep(unsigned value) { (void)value; assert(!"blocking periodic sleep"); }
static void usleep_range(unsigned low, unsigned high) __attribute__((unused));
static void usleep_range(unsigned low, unsigned high)
{ (void)low; (void)high; assert(!"blocking batch sleep"); }
#define jiffies_to_msecs(value) ((unsigned long)(value) * 10UL)
'''

CASES = r'''
static void reset(unsigned long now)
{
    jiffies = now;
    ecm_nss_ipvX_next_req_time = ecm_nss_ipvX_roll_check_jiffies = 0;
    ecm_nss_ipvX_accelerated_count = 1; ecm_ipvX_terminate_pending = 0;
    message.msg.conn_stats_many.count = 7; message.msg.conn_stats_many.index = 0;
    queued = sent = paced = tx_fail = delay = 0;
    clock_us = task_state = spurious_wakeups = timer_calls = 0;
    ecm_nss_ipvX_stats_request_success = ecm_nss_ipvX_stats_request_fail = 0;
}
static void run(void) { ecm_nss_ipvX_stats_sync_req_work(NULL); }
int main(void)
{
    /* Early wakeups must not shorten or restart the absolute idle deadline. */
    reset(1000); spurious_wakeups = 2;
    ecm_nss_common_stats_sleep(3900, 4000);
    assert(clock_us == 3900 && timer_calls == 3 && paced == 1 && task_state == 0);
    ecm_nss_common_stats_sleep(100, 200);
    assert(clock_us == 4000 && timer_calls == 4 && paced == 2 && task_state == 0);
    /* No connections: reset the batch and wait one period without sending. */
    reset(1000); ecm_nss_ipvX_accelerated_count = 0;
    message.msg.conn_stats_many.index = 9; run();
    assert(queued == 1 && delay == 100 && !sent && !paced);
    assert(!message.msg.conn_stats_many.count && !message.msg.conn_stats_many.index);
    /* A new active round sends now. Completed rounds wait for their deadline. */
    reset(1000); run();
    assert(sent == 1 && !queued && ecm_nss_ipvX_next_req_time == 1100);
    jiffies = 1005; run();
    assert(sent == 1 && queued == 1 && delay == 95);
    /* Early dispatch must not move the deadline further into the future. */
    jiffies = 1099; run();
    assert(sent == 1 && queued == 2 && delay == 1);
    jiffies = 1100; run();
    assert(sent == 2 && ecm_nss_ipvX_next_req_time == 1200);
    /* Continuation batches preserve their index and do not wait a full period. */
    jiffies = 1101; message.msg.conn_stats_many.index = 23; run();
    assert(sent == 3 && queued == 2 && message.msg.conn_stats_many.index == 23);
    /* Linux INITIAL_JIFFIES is negative: the first request must still run. */
    reset(ULONG_MAX - 30000UL); run();
    assert(!sent && queued == 1 && delay == 100);
    jiffies += delay; run();
    assert(sent == 1 && queued == 1);
    /* Exercise wraparound at the same word size as the extracted worker. */
    reset(ULONG_MAX - 40UL);
    ecm_nss_ipvX_roll_check_jiffies = jiffies - 100;
    ecm_nss_ipvX_next_req_time = jiffies + 100;
    run(); assert(!sent && queued == 1 && delay == 100);
    jiffies += delay; run(); assert(sent == 1 && queued == 1);
    /* Transport failure preserves the existing three retries and fresh start. */
    reset(1000); tx_fail = 1; message.msg.conn_stats_many.index = 23; run();
    assert(sent == 3 && queued == 1 && delay == 100);
    assert(ecm_nss_ipvX_stats_request_fail == 3 && !ecm_nss_ipvX_stats_request_success);
    assert(!message.msg.conn_stats_many.index && !message.msg.conn_stats_many.count);
    /* Teardown may not submit or rearm work, including the idle path. */
    for (unsigned active = 0; active < 2; active++) {
        reset(1000); ecm_ipvX_terminate_pending = 1;
        ecm_nss_ipvX_accelerated_count = active; run();
        assert(!sent && !queued && !paced);
    }
    /* Long idle followed by traffic catches up without an extra full-period wait. */
    reset(1000); run(); jiffies = 2000; run();
    assert(sent == 2 && !queued && ecm_nss_ipvX_next_req_time == 2100);
    puts("PASS: ipvX cadence, batches, initial/wrapped jiffies, retries, teardown and TASK_IDLE timing/early wakeups");
    return 0;
}
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('ecm_source', type=Path)
    parser.add_argument('--cc', default='cc')
    parser.add_argument('--runner', help='Run the compiled fixture under this emulator')
    args = parser.parse_args()
    helper = extract((args.ecm_source / 'frontends/nss/ecm_nss_common.h').read_text(),
                     'static inline void ecm_nss_common_stats_sleep(')
    with tempfile.TemporaryDirectory(prefix='ecm-stats-') as directory:
        for version in (4, 6):
            source = args.ecm_source / f'frontends/nss/ecm_nss_ipv{version}.c'
            function = extract(source.read_text(), f'static void ecm_nss_ipv{version}_stats_sync_req_work(')
            fixture = FIXTURE.replace('ipvX', f'ipv{version}').replace('IPVX', f'IPV{version}')
            cases = CASES.replace('ipvX', f'ipv{version}')
            test = Path(directory) / f'ipv{version}.c'
            binary = test.with_suffix('')
            test.write_text(fixture + helper + function + cases)
            command = [args.cc, '-std=c11', '-Wall', '-Wextra', '-Werror',
                       '-Wno-unused-parameter', str(test), '-o', str(binary)]
            if args.runner:
                command.append('-static')
            subprocess.run(command, check=True)
            subprocess.run(([args.runner] if args.runner else []) + [str(binary)], check=True)


if __name__ == '__main__':
    main()
