#!/usr/bin/env python3
"""Exercise the real hostapd station/VLAN message builder against cfg80211's policy."""
import argparse
from pathlib import Path
import subprocess
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('driver_source', type=Path)
parser.add_argument('--cc', default='cc')
parser.add_argument('--runner', help='Run a statically linked fixture under this emulator')
args = parser.parse_args()
text = args.driver_source.read_text()
start = text.index('static int i802_set_sta_vlan(')
brace = text.index('{', start)
depth = 1
end = brace + 1
while depth:
    depth += (text[end] == '{') - (text[end] == '}')
    end += 1
function = text[start:end]
fixture = r'''
#include <errno.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
typedef unsigned char u8;
#define MACSTR "%02x:%02x:%02x:%02x:%02x:%02x"
#define MAC2STR(a) a[0],a[1],a[2],a[3],a[4],a[5]
#define ETH_ALEN 6
#define MSG_DEBUG 0
#define MSG_ERROR 1
#define WPA_DRIVER_FLAGS_VLAN_OFFLOAD 1
#define NL80211_CMD_SET_STATION 1
#define NL80211_ATTR_MAC 2
#define NL80211_ATTR_VLAN_ID 3
#define NL80211_ATTR_STA_VLAN 4
#define wpa_printf(...) ((void)0)
struct wpa_driver_nl80211_data { struct { unsigned flags; } capa; };
struct i802_bss { struct wpa_driver_nl80211_data *drv; const char *ifname; };
struct nl_msg { unsigned has_vlan, vlan, ifindex; };
static struct nl_msg sent;
static unsigned if_nametoindex(const char *name) { (void)name; return 9; }
static struct nl_msg *nl80211_bss_msg(struct i802_bss *bss, int flags, int cmd)
{ (void)bss; (void)flags; (void)cmd; return calloc(1, sizeof(struct nl_msg)); }
static int nla_put(struct nl_msg *msg, int attr, int len, const void *data)
{ (void)msg; (void)attr; (void)len; (void)data; return 0; }
static int nla_put_u16(struct nl_msg *msg, int attr, unsigned value)
{ (void)attr; msg->has_vlan=1; msg->vlan=value; return 0; }
static int nla_put_u32(struct nl_msg *msg, int attr, unsigned value)
{ (void)attr; msg->ifindex=value; return 0; }
static void nlmsg_free(struct nl_msg *msg) { free(msg); }
static int send_and_recv_msgs(struct wpa_driver_nl80211_data *drv,
                             struct nl_msg *msg, void *a, void *b)
{
    (void)drv; (void)a; (void)b;
    sent=*msg; free(msg);
    /* Actual cfg80211 NL80211_ATTR_VLAN_ID policy: 1..4094. */
    return sent.has_vlan && (sent.vlan<1 || sent.vlan>4094) ? -ERANGE : 0;
}
'''
cases = r'''
int main(void)
{
    struct wpa_driver_nl80211_data drv = {0};
    struct i802_bss bss = {&drv, "wlan1"};
    const u8 addr[6] = {0};
    const unsigned vlans[] = {0, 1, 37, 4094};
    for (unsigned offload=0; offload<2; offload++) {
        drv.capa.flags=offload;
        for (unsigned n=0; n<sizeof(vlans)/sizeof(vlans[0]); n++) {
            unsigned vlan=vlans[n];
            int ret=i802_set_sta_vlan(&bss, addr, "wlan1", vlan);
            if (ret || sent.ifindex!=9 || sent.has_vlan!=(offload && vlan!=0) ||
                (sent.has_vlan && sent.vlan!=vlan)) {
                fprintf(stderr, "FAIL: offload=%u vlan=%u result=%d emitted_vlan=%u\n",
                        offload, vlan, ret, sent.has_vlan);
                return 1;
            }
        }
    }
    puts("PASS: untagged and tagged station VLAN messages satisfy cfg80211 policy");
    return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='hostapd-vlan-') as directory:
    source = Path(directory) / 'test.c'
    binary = Path(directory) / 'test'
    source.write_text(fixture + function + cases)
    command = [args.cc, '-std=c11', '-Wall', '-Wextra', '-Werror', str(source), '-o', str(binary)]
    if args.runner:
        command.append('-static')
    subprocess.run(command, check=True)
    subprocess.run(([args.runner] if args.runner else []) + [str(binary)], check=True)
