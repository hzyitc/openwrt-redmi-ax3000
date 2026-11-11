#!/usr/bin/env python3
"""Exercise TSENS conversions, register I/O and sequential driver lifecycle paths.

The fixtures run extracted driver functions with mocked kernel services; they
do not model concurrent IRQs, memory ordering or hardware register semantics.
"""
import argparse
from pathlib import Path
import re
import subprocess
import tempfile


def function(text, name):
    match = re.search(r'(?m)^(?:static\s+(?:inline\s+)?)?(?:int|void)\s+(?:__maybe_unused\s+)?' + name + r'\([^;{]*\)\s*\{', text)
    if not match:
        raise ValueError(f'Missing definition: {name}')
    end = text.index('{', match.start()) + 1
    depth = 1
    while depth:
        depth += (text[end] == '{') - (text[end] == '}')
        end += 1
    return text[match.start():end]


FIXTURE = r'''
#include <assert.h>
#include <errno.h>
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>
typedef uint32_t u32;
#define BIT(n) (1U << (n))
#define GENMASK(h, l) ((~0U << (l)) & (~0U >> (31U - (h))))
#define EPROBE_DEFER 517
#define DIV_ROUND_CLOSEST(n, d) (((n) < 0 ? (n) - (d)/2 : (n) + (d)/2) / (d))
#define ERR_PTR(error) ((void *)(intptr_t)(error))
#define PTR_ERR(value) ((long)(intptr_t)(value))
#define IS_ERR(value) ((uintptr_t)(value) >= (uintptr_t)-4095)
#define IORESOURCE_MEM 0
#define IRQF_TRIGGER_RISING 1
#define __iomem
#define mb() ((void)0)
#define dev_err(...) (++device_errors)
#define dev_dbg(...) ((void)0)
#define pr_err(...) ((void)0)
#define pr_debug(...) ((void)0)
#define pr_info(...) ((void)0)
#define smp_store_release(ptr, value) (*(ptr) = (value))
#define smp_load_acquire(ptr) (*(ptr))
#define container_of(ptr, type, member) ((type *)((char *)(ptr) - offsetof(type, member)))
#define INIT_WORK(work, callback) ((void)(work))
#define schedule_work(work) (++notifications)
#define devm_request_irq(dev, irq, handler, flags, name, data) mock_request_irq()
enum { TSENS_EN, SENSOR_EN, LAST_TEMP_0, VALID_0 = 16 };
struct regmap { u32 reg[64]; };
struct regmap_field { unsigned id; };
struct device { void *of_node; };
struct resource { int index; };
struct platform_device { struct device dev; int num_resources; };
struct tsens_ops { int marker; };
struct tsens_features { unsigned max_sensors; };
struct work_struct { int unused; };
struct tsens_priv;
struct tsens_sensor {
    struct tsens_priv *priv;
    unsigned id, hw_id, status;
    int slope, offset;
    struct work_struct notify_work;
};
struct tsens_priv {
    struct device *dev;
    struct regmap *tm_map, *srot_map;
    void *iomem_base;
    unsigned tm_offset, num_sensors;
    struct regmap_field *rf[32];
    const struct tsens_features *feat;
    const int *fields;
    const struct tsens_ops *ops;
    int tsens_irq;
    struct work_struct tsens_work;
    bool ready, irq_requested, irq_wake_enabled;
    struct tsens_sensor sensor[5];
};
static const struct tsens_ops ops_ipq5018 = {1}, generic_ops = {2};
static const struct tsens_features features = {11};
static int fields[32], tsens_config, tsens_srot_config;
static struct regmap tm, srot;
static struct platform_device platform;
static struct regmap_field allocated_fields[32];
static struct resource resources[2] = {{0}, {1}};
static unsigned refs, alloc_calls, map_calls, iomap_calls, reads, writes, irqs;
static unsigned fail_alloc, fail_map, fail_iomap, fail_read, fail_write;
static unsigned notifications;
static unsigned irq_disables, wake_enables, wake_disables, cancellations, calib_frees;
static int wake_error, calib_error;
static bool physical_irq, physical_wake, fail_action, fail_all_writes;
static void (*managed_action)(void *);
static void *managed_data;
static struct tsens_priv *cleanup_target;
static u32 calibration_data[4];
static int device_errors, field_read_error, irq_error;
static bool missing_device, int_clr_deassert_quirk;
static u32 read_values[3];
static unsigned read_values_count, read_values_used;
int code2degc_lut_degc[5][1024];

static struct platform_device *of_find_device_by_node(void *node)
{ (void)node; if (missing_device) return NULL; refs++; return &platform; }
static void put_device(struct device *dev)
{ assert(dev == &platform.dev && refs); refs--; }
static struct resource *platform_get_resource(struct platform_device *pdev, int type, int index)
{ assert(pdev == &platform && type == IORESOURCE_MEM && index < 2); return &resources[index]; }
static void *devm_ioremap_resource(struct device *dev, struct resource *resource)
{
    (void)dev;
    if (++iomap_calls == fail_iomap) return ERR_PTR(-ENOMEM);
    return resource->index ? &srot : &tm;
}
static struct regmap *devm_regmap_init_mmio(struct device *dev, void *base, const int *config)
{
    (void)dev; (void)config;
    if (++map_calls == fail_map) return ERR_PTR(-ENOMEM);
    return base;
}
static struct regmap_field *devm_regmap_field_alloc(struct device *dev, struct regmap *map, int field)
{
    (void)dev;
    assert(map == &srot || map == &tm);
    if (++alloc_calls == fail_alloc) return ERR_PTR(-ENOMEM);
    allocated_fields[alloc_calls].id = field;
    return &allocated_fields[alloc_calls];
}
static int regmap_field_read(struct regmap_field *field, u32 *value)
{
    assert(!IS_ERR(field) && field->id == TSENS_EN);
    if (field_read_error) return field_read_error;
    *value = srot.reg[1] & 1;
    return 0;
}
static int regmap_read(struct regmap *map, unsigned reg, u32 *value)
{
    assert((map == &tm || map == &srot) && reg / 4 < 64);
    if (++reads == fail_read) return -EIO;
    if (map == &tm && reg >= 0x44 && read_values_used < read_values_count)
        *value = read_values[read_values_used++];
    else
        *value = map->reg[reg / 4];
    return 0;
}
static int regmap_write(struct regmap *map, unsigned reg, u32 value)
{
    assert((map == &tm || map == &srot) && reg / 4 < 64);
    if (++writes == fail_write || fail_all_writes) return -EIO;
    map->reg[reg / 4] = value;
    return 0;
}
static int regmap_update_bits(struct regmap *map, unsigned reg, u32 mask, u32 value)
{
    u32 old;
    int ret = regmap_read(map, reg, &old);
    if (ret) return ret;
    u32 next = (old & ~mask) | (value & mask);
    return next == old ? 0 : regmap_write(map, reg, next);
}
static int regmap_write_bits(struct regmap *map, unsigned reg, u32 mask, u32 value)
{
    u32 old;
    int ret = regmap_read(map, reg, &old);
    return ret ? ret : regmap_write(map, reg, (old & ~mask) | (value & mask));
}
static int mock_request_irq(void)
{ irqs++; if (!irq_error) physical_irq = true; return irq_error; }
static int enable_irq_wake(int irq)
{
    (void)irq; wake_enables++;
    assert(physical_irq);
    if (wake_error) return wake_error;
    physical_wake = true; return 0;
}
static void disable_irq(int irq)
{ (void)irq; assert(physical_irq); physical_irq = false; irq_disables++; }
static int disable_irq_wake(int irq)
{ (void)irq; assert(physical_wake); physical_wake = false; wake_disables++; return 0; }
static int cancel_work_sync(struct work_struct *work)
{
    assert(cleanup_target && !cleanup_target->ready && !cleanup_target->irq_requested);
    work->unused = 0; cancellations++; return 0;
}
static int devm_add_action_or_reset(struct device *dev, void (*action)(void *), void *data)
{
    (void)dev;
    assert(physical_irq && !managed_action);
    if (fail_action) { action(data); return -ENOMEM; }
    managed_action = action; managed_data = data; return 0;
}
static char *qfprom_read(struct device *dev, const char *name)
{
    (void)dev; assert(strcmp(name, "calib") == 0);
    return calib_error ? ERR_PTR(calib_error) : (char *)calibration_data;
}
static void kfree(void *ptr) { assert(ptr == calibration_data); calib_frees++; }
static bool device_property_read_bool(struct device *dev, const char *name)
{ (void)dev; (void)name; return false; }
'''

CASES = r'''
static struct tsens_priv priv;
static void reset(void)
{
    memset(&priv, 0, sizeof(priv)); memset(&tm, 0, sizeof(tm)); memset(&srot, 0, sizeof(srot));
    refs = alloc_calls = map_calls = iomap_calls = reads = writes = irqs = 0;
    fail_alloc = fail_map = fail_iomap = fail_read = fail_write = 0;
    device_errors = field_read_error = irq_error = 0; missing_device = false;
    read_values_count = read_values_used = 0;
    notifications = 0; int_clr_deassert_quirk = false;
    irq_disables = wake_enables = wake_disables = cancellations = calib_frees = 0;
    wake_error = calib_error = 0;
    physical_irq = physical_wake = fail_action = fail_all_writes = false;
    managed_action = NULL; managed_data = NULL; cleanup_target = &priv;
    memset(calibration_data, 0, sizeof(calibration_data));
    platform.num_resources = 2; platform.dev.of_node = &platform;
    priv.dev = &platform.dev; priv.tm_map = &tm; priv.srot_map = &srot;
    priv.num_sensors = 5; priv.feat = &features; priv.fields = fields; priv.ops = &ops_ipq5018;
    priv.ready = true;
    for (unsigned i = 0; i < 32; i++) fields[i] = i;
    for (unsigned i = 0; i < 5; i++) {
        priv.sensor[i].priv = &priv; priv.sensor[i].id = priv.sensor[i].hw_id = i;
        priv.sensor[i].status = TSENS_TM_SN_STATUS + i * 4;
        priv.sensor[i].slope = 1000; priv.sensor[i].offset = 300000;
        for (unsigned code = 0; code < 1024; code++) code2degc_lut_degc[i][code] = (int)code - 300;
    }
}
static void thresholds(unsigned sensor, int low, int high)
{ tm.reg[(sensor + 1)] = ((high + 300) << 10) | (low + 300); }
static void release(void)
{
    if (managed_action) {
        void (*action)(void *) = managed_action;
        managed_action = NULL; action(managed_data);
    }
    assert(!physical_irq && !physical_wake && !priv.ready);
}
int main(void)
{
    /* Cold IPQ5018 may start disabled; generic devices still require enable. */
    reset(); assert(init_common(&priv) == 0 && !device_errors && refs == 0 && alloc_calls == 24);
    reset(); priv.ops = &generic_ops;
    assert(init_common(&priv) == -ENODEV && device_errors == 1 && refs == 0);
    reset(); priv.ops = &generic_ops; srot.reg[1] = 1;
    assert(init_common(&priv) == 0 && !device_errors && refs == 0);
    /* The real init path must enable TSENS and propagate every mapping failure. */
    reset(); assert(init_ipq5018(&priv) == 0 && !device_errors && !refs);
    assert((srot.reg[1] & 1) && tm.reg[0] == 0 && irqs == 1 && writes == 5);
    assert(!priv.ready && priv.irq_requested && !priv.irq_wake_enabled && !wake_enables);
    release();
    for (unsigned n = 0; n < 2; n++) {
        reset(); priv.num_sensors = n ? 6 : 0;
        assert(init_ipq5018(&priv) == -EINVAL && !writes && !refs);
    }
    reset(); missing_device = true;
    assert(init_ipq5018(&priv) == -EINVAL && !writes && !irqs && !refs);
    for (unsigned n = 1; n <= 2; n++) {
        reset(); fail_iomap = n;
        assert(init_ipq5018(&priv) == -ENOMEM && !writes && !irqs && !refs);
        reset(); fail_map = n;
        assert(init_ipq5018(&priv) == -ENOMEM && !writes && !irqs && !refs);
    }
    for (unsigned n = 1; n <= 24; n++) {
        reset(); fail_alloc = n;
        assert(init_ipq5018(&priv) == -ENOMEM && !writes && !irqs && !refs);
    }
    reset(); field_read_error = -EIO;
    assert(init_ipq5018(&priv) == -EIO && !writes && !irqs && !refs);
    for (unsigned n = 1; n <= 5; n++) {
        reset(); fail_write = n;
        assert(init_ipq5018(&priv) == -EIO && writes >= n && !refs);
        assert(!priv.ready && !priv.irq_requested && !tm.reg[0] && !(srot.reg[1] & 1));
    }
    reset(); irq_error = -EBUSY;
    assert(init_ipq5018(&priv) == -EBUSY && !tm.reg[0] && !refs);
    reset(); fail_action = true;
    assert(init_ipq5018(&priv) == -ENOMEM && !physical_irq && !priv.ready && cancellations == 6);
    /* ADC readings use milliCelsius on every sensor, including negative values. */
    const int values[] = {-77, -20, 0, 45, 100, 243};
    for (unsigned id = 0; id < 5; id++) {
        for (unsigned n = 0; n < sizeof(values)/sizeof(values[0]); n++) {
            reset(); int result = 123456;
            tm.reg[0x44/4 + id] = (1U << 14) | (values[n] + 300);
            assert(get_temp_ipq5018(&priv, id, &result) == 0 && result == values[n] * 1000);
        }
    }
    /* Retry reads retain units; bus failures do not overwrite the output. */
    reset(); int result = 123456;
    read_values_count = 2; read_values[0] = 340; read_values[1] = (1U << 14) | 345;
    assert(get_temp_ipq5018(&priv, 0, &result) == 0 && result == 45000);
    reset(); fail_read = 1; result = 123456;
    assert(get_temp_ipq5018(&priv, 0, &result) == -EIO && result == 123456);
    /* Millidegree writes must preserve the opposite hardware threshold. */
    reset(); thresholds(0, 70, 80);
    assert(set_trip_temp_ipq5018(&priv.sensor[0], TSENS_TRIP_STAGE2, 85000) == 0);
    assert(tm.reg[1] == ((385U << 10) | 370U));
    assert(set_trip_temp_ipq5018(&priv.sensor[0], TSENS_TRIP_STAGE1, 65000) == 0);
    assert(tm.reg[1] == ((385U << 10) | 365U) && tm.reg[0] == 1);
    reset(); thresholds(0, -77, 80);
    assert(set_trip_temp_ipq5018(&priv.sensor[0], TSENS_TRIP_STAGE2, 243000) == 0);
    assert((tm.reg[1] >> 10) == 543);
    reset(); thresholds(0, -77, 80);
    assert(set_trip_temp_ipq5018(&priv.sensor[0], TSENS_TRIP_STAGE1, -76500) == 0);
    assert((tm.reg[1] & 0x3ff) == 223);
    for (unsigned n = 0; n < 2; n++) {
        reset(); thresholds(0, 70, 80);
        assert(set_trip_temp_ipq5018(&priv.sensor[0], TSENS_TRIP_STAGE2,
                                    n ? 243001 : -77001) == -EINVAL && !writes);
    }
    reset(); thresholds(0, 70, 80);
    assert(set_trip_temp_ipq5018(NULL, TSENS_TRIP_STAGE2, 85000) == -EINVAL);
    assert(set_trip_temp_ipq5018(&priv.sensor[0], TSENS_TRIP_STAGE2, 60000) == -EINVAL);
    assert(set_trip_temp_ipq5018(&priv.sensor[0], TSENS_TRIP_STAGE3, 100000) == -EINVAL);
    /* Failed trip reads/writes must not report successful programming. */
    reset(); thresholds(0, 70, 80); fail_read = 1;
    assert(set_trip_temp_ipq5018(&priv.sensor[0], TSENS_TRIP_STAGE2, 85000) == -EIO && !writes);
    for (unsigned n = 1; n <= 3; n++) {
        reset(); thresholds(0, 70, 80); tm.reg[0] = 1; fail_write = n;
        assert(set_trip_temp_ipq5018(&priv.sensor[0], TSENS_TRIP_STAGE2, 85000) == -EIO);
        if (n < 3) assert(tm.reg[0] == 1);
        if (n < 3) assert(tm.reg[1] == ((380U << 10) | 370U));
    }
    reset(); thresholds(0, 70, 80);
    for (unsigned code = 0; code < 1024; code++) code2degc_lut_degc[0][code] = 50;
    assert(set_trip_temp_ipq5018(&priv.sensor[0], TSENS_TRIP_STAGE2, 85000) == -ERANGE && !writes);
    /* Alarm acknowledgements share a register with both trip thresholds. */
    for (unsigned quirk = 0; quirk < 2; quirk++) {
        const u32 alarms[] = {TSENS_TM_SN_STATUS_UPPER_STATUS,
                             TSENS_TM_SN_STATUS_LOWER_STATUS,
                             TSENS_TM_SN_STATUS_UPPER_STATUS | TSENS_TM_SN_STATUS_LOWER_STATUS};
        for (unsigned n = 0; n < 3; n++) {
            reset(); thresholds(0, 70, 80); srot.reg[1] = 1;
            int_clr_deassert_quirk = quirk;
            tm.reg[0x44/4] = TSENS_TM_SN_STATUS_VALID_BIT | alarms[n] | 390;
            tsens_scheduler_fn(&priv.tsens_work);
            assert((tm.reg[1] & 0xfffff) == ((380U << 10) | 370U));
            assert(notifications == 1);
            if (!quirk) {
                tsens_scheduler_fn(&priv.tsens_work);
                assert(notifications == 2 && writes == 2);
            }
            if (quirk) assert(tm.reg[1] == ((380U << 10) | 370U));
        }
    }
    for (unsigned n = 1; n <= 3; n++) {
        reset(); thresholds(0, 70, 80); srot.reg[1] = 1; fail_read = n;
        tm.reg[0x44/4] = TSENS_TM_SN_STATUS_VALID_BIT | TSENS_TM_SN_STATUS_UPPER_STATUS | 390;
        tsens_scheduler_fn(&priv.tsens_work);
        assert(!writes && !notifications && tm.reg[1] == ((380U << 10) | 370U));
    }
    /* Before calibration, queued IRQ work and public readers must stay gated. */
    reset(); assert(init_ipq5018(&priv) == 0);
    unsigned reads_before = reads, writes_before = writes;
    tm.reg[0x44/4] = TSENS_TM_SN_STATUS_VALID_BIT | TSENS_TM_SN_STATUS_UPPER_STATUS | 390;
    tsens_scheduler_fn(&priv.tsens_work);
    assert(reads == reads_before && writes == writes_before && !notifications);
    result = 123456;
    assert(get_temp_ipq5018(&priv, 0, &result) == -EAGAIN && result == 123456);
    assert(set_trip_temp_ipq5018(&priv.sensor[0], TSENS_TRIP_STAGE2, 85000) == -EAGAIN);
    /* Real calibration builds the lookup before publishing readiness/enabling alarms. */
    calibration_data[0] = (TWO_PT_CALIB << CAL_SEL_SHIFT) | (100U << BASE0_SHIFT) | (170U << BASE1_SHIFT);
    assert(calibrate_ipq5018(&priv) == 0 && priv.ready && tm.reg[0] == 1 && calib_frees == 1);
    assert(priv.irq_wake_enabled && wake_enables == 1);
    tm.reg[0x44/4] = TSENS_TM_SN_STATUS_VALID_BIT | 400;
    assert(get_temp_ipq5018(&priv, 0, &result) == 0 && result == 30000);
    /* Removal quiesces IRQs and queued work; devres can call stop again safely. */
    priv.tsens_work.unused = 1; priv.sensor[1].notify_work.unused = 1;
    disable_ipq5018(&priv);
    assert(!priv.ready && !physical_irq && !physical_wake && cancellations == 6);
    assert(!priv.tsens_work.unused && !priv.sensor[1].notify_work.unused);
    release(); assert(irq_disables == 1 && wake_disables == 1);
    /* Provider deferral and invalid zero/negative slopes unwind without a divide by zero. */
    reset(); assert(init_ipq5018(&priv) == 0); calib_error = -EPROBE_DEFER;
    assert(calibrate_ipq5018(&priv) == -EPROBE_DEFER && !priv.ready && !tm.reg[0] && !calib_frees);
    release();
    for (unsigned n = 0; n < 2; n++) {
        reset(); assert(init_ipq5018(&priv) == 0);
        calibration_data[0] = (TWO_PT_CALIB << CAL_SEL_SHIFT) | (100U << BASE0_SHIFT) | ((n ? 80U : 100U) << BASE1_SHIFT);
        assert(calibrate_ipq5018(&priv) == -EINVAL && !priv.ready && !tm.reg[0]);
        assert(calib_frees == 1 && !wake_enables); release();
    }
    reset(); assert(init_ipq5018(&priv) == 0);
    calibration_data[0] = (TWO_PT_CALIB << CAL_SEL_SHIFT) | (100U << BASE0_SHIFT) | (120U << BASE1_SHIFT);
    calibration_data[2] = 20U << S4_P1_SHIFT;
    assert(calibrate_ipq5018(&priv) == -EINVAL && !priv.ready && !tm.reg[0]);
    assert(priv.sensor[0].slope > 0 && priv.sensor[4].slope == 0); release();
    for (unsigned n = 0; n < 2; n++) {
        reset(); assert(init_ipq5018(&priv) == 0);
        calibration_data[0] = n ? ((ONE_PT_CALIB2 << CAL_SEL_SHIFT) | (100U << BASE0_SHIFT)) : 0;
        assert(calibrate_ipq5018(&priv) == 0 && priv.ready);
        for (unsigned sensor = 0; sensor < 5; sensor++) assert(priv.sensor[sensor].slope == SLOPE_DEFAULT);
        release();
    }
    reset(); assert(init_ipq5018(&priv) == 0); fail_write = writes + 1;
    assert(calibrate_ipq5018(&priv) == -EIO && !priv.ready && !physical_wake); release();
    reset(); assert(init_ipq5018(&priv) == 0); wake_error = -EINVAL;
    assert(calibrate_ipq5018(&priv) == 0 && priv.ready && !priv.irq_wake_enabled);
    fail_all_writes = true; release(); assert(!wake_disables && !physical_irq);
    /* Invalid/unstable reads must never fabricate temperatures or divide by zero. */
    reset(); priv.sensor[0].slope = 0; result = 123456;
    assert(get_temp_ipq5018(&priv, 0, &result) == -EINVAL && result == 123456);
    reset(); result = 123456; read_values_count = 3;
    read_values[0] = 345; read_values[1] = 346; read_values[2] = 347;
    assert(get_temp_ipq5018(&priv, 0, &result) == -EAGAIN && result == 123456);
    reset(); read_values_count = 3;
    read_values[0] = 344; read_values[1] = read_values[2] = 345;
    assert(get_temp_ipq5018(&priv, 0, &result) == 0 && result == 45000);
    assert(get_temp_ipq5018(&priv, -1, &result) == -EINVAL);
    assert(get_temp_ipq5018(&priv, 5, &result) == -EINVAL);
    puts("PASS: calibration gating, invalid samples/slopes, IRQ/work teardown and deferred-probe cleanup");
    puts("PASS: TSENS units, cold start, trip I/O errors, unavailable ADC codes and alarm threshold preservation");
    return 0;
}
'''

HWMON_FIXTURE = r'''
#include <assert.h>
#include <errno.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#define ERR_PTR(error) ((void *)(intptr_t)(error))
#define IS_ERR(value) ((uintptr_t)(value) >= (uintptr_t)-4095)
#define PTR_ERR(value) ((long)(intptr_t)(value))
#define EPROBE_DEFER 517
#define __maybe_unused
#define dev_warn(...) (++warnings)
#define dev_err(...) ((void)0)
#define GFP_KERNEL 0
#define struct_size(ptr, member, count) sizeof(*(ptr))
typedef uint32_t u32;
struct device { uintptr_t non_driver_data; void *driver_data, *of_node; struct device *parent; };
struct platform_device { struct device dev; };
struct device_node;
struct thermal_zone_params { bool no_hwmon; };
struct thermal_zone_device { int id; struct thermal_zone_params *tzp; };
struct tsens_priv;
struct tsens_sensor { struct tsens_priv *priv; int id, hw_id; struct thermal_zone_device *tzd; };
struct tsens_ops {
    int marker;
    int (*init)(struct tsens_priv *);
    int (*calibrate)(struct tsens_priv *);
    int (*get_temp)(struct tsens_priv *, int, int *);
    void (*disable)(struct tsens_priv *);
    int (*enable)(struct tsens_priv *, int);
    int (*suspend)(struct tsens_priv *);
    int (*resume)(struct tsens_priv *);
};
struct tsens_priv {
    struct device *dev;
    int num_sensors, tsens_irq;
    const struct tsens_ops *ops;
    const int *feat, *fields;
    struct tsens_sensor sensor[5];
};
struct tsens_plat_data {
    u32 num_sensors;
    const int *hw_ids, *feat, *fields;
    const struct tsens_ops *ops;
};
struct of_device_id { const struct tsens_plat_data *data; };
static int mock_init(struct tsens_priv *priv);
static int mock_calibrate(struct tsens_priv *priv);
static int mock_get_temp(struct tsens_priv *priv, int id, int *temp);
static void mock_disable(struct tsens_priv *priv);
static const struct tsens_ops ops_ipq5018 = {
    .marker = 1, .init = mock_init, .calibrate = mock_calibrate,
    .get_temp = mock_get_temp, .disable = mock_disable,
}, generic_ops = {.marker = 2};
static const struct tsens_plat_data platform_data = {.num_sensors = 5, .ops = &ops_ipq5018};
static const struct of_device_id match = {.data = &platform_data};
static const int tsens_of_ops = 0, tsens_table[] = {0};
static struct tsens_priv priv;
static struct platform_device platform;
static struct thermal_zone_params params[5];
static struct thermal_zone_device zones[5];
static bool active[5], attached[5];
static unsigned actions, warnings, added, removed, fail_add, fail_action;
static int fail_sensor, init_error, calibration_error, irq_error;
static bool no_sensors, driver_running;
static unsigned resources;
static void (*cleanup[16])(void *);
static void *cleanup_data[16];
static void add_resource(void (*action)(void *), void *data)
{
    assert(resources < 16);
    cleanup[resources] = action; cleanup_data[resources++] = data;
}
static void detach_sensor(void *data)
{
    struct thermal_zone_device *tz = data;
    assert(!driver_running && attached[tz->id] && !active[tz->id]);
    attached[tz->id] = false;
}
static struct thermal_zone_device *devm_thermal_zone_of_sensor_register(
    struct device *dev, int id, struct tsens_sensor *sensor, const int *ops)
{
    (void)dev; (void)sensor; (void)ops;
    if (!id || no_sensors) return ERR_PTR(-ENODEV);
    if (id == fail_sensor) return ERR_PTR(-EPROBE_DEFER);
    attached[id] = true;
    add_resource(detach_sensor, &zones[id]);
    return &zones[id];
}
static int thermal_add_hwmon_sysfs(struct thermal_zone_device *tz)
{
    assert(!active[tz->id]);
    if ((unsigned)tz->id == fail_add) return -EIO;
    active[tz->id] = true; added++;
    return 0;
}
static void thermal_remove_hwmon_sysfs(struct thermal_zone_device *tz)
{
    assert(active[tz->id] && attached[tz->id]);
    active[tz->id] = false; removed++;
}
static int devm_add_action_or_reset(struct device *dev, void (*action)(void *), void *data)
{
    (void)dev;
    struct thermal_zone_device *tz = data;
    if ((unsigned)tz->id == fail_action) { action(data); return -ENOMEM; }
    add_resource(action, data); actions++;
    return 0;
}
static void *dev_get_drvdata(struct device *dev) { return dev->driver_data; }
static void mock_disable(struct tsens_priv *data)
{ assert(data == &priv); driver_running = false; }
static void stop_driver(void *data) { mock_disable(data); }
static int mock_init(struct tsens_priv *data)
{
    if (init_error) return init_error;
    driver_running = true; add_resource(stop_driver, data); return 0;
}
static int mock_calibrate(struct tsens_priv *data)
{ assert(data == &priv); return calibration_error; }
static int mock_get_temp(struct tsens_priv *data, int id, int *temp)
{ (void)data; (void)id; *temp = 45000; return 0; }
static const struct of_device_id *of_match_node(const int *table, struct device_node *node)
{ (void)table; (void)node; return &match; }
static int of_property_read_u32(struct device_node *node, const char *name, u32 *value)
{ (void)node; (void)name; (void)value; return -EINVAL; }
static void *devm_kzalloc(struct device *dev, size_t size, int flags)
{ (void)dev; (void)flags; assert(size == sizeof(priv)); memset(&priv, 0, sizeof(priv)); return &priv; }
static int platform_get_irq(struct platform_device *pdev, int index)
{ (void)pdev; (void)index; return irq_error ? irq_error : 5; }
static void platform_set_drvdata(struct platform_device *pdev, void *data)
{ pdev->dev.driver_data = data; }
static void *platform_get_drvdata(struct platform_device *pdev)
{ return pdev->dev.driver_data; }
'''

HWMON_CASES = r'''
static void reset(void)
{
    memset(&priv, 0, sizeof(priv)); memset(active, 0, sizeof(active));
    memset(attached, 0, sizeof(attached));
    actions = warnings = added = removed = fail_add = fail_action = 0;
    fail_sensor = init_error = calibration_error = irq_error = 0;
    no_sensors = driver_running = false; resources = 0;
    memset(&platform, 0, sizeof(platform)); platform.dev.of_node = &platform;
    priv.num_sensors = 5; priv.ops = &ops_ipq5018;
    for (int i = 0; i < 5; i++) { zones[i].id = i; zones[i].tzp = &params[i]; params[i].no_hwmon = true; }
}
static void release(void)
{
    while (resources) { resources--; cleanup[resources](cleanup_data[resources]); }
    assert(!driver_running);
    for (int i = 1; i < 5; i++) {
        assert(!active[i] && !attached[i] && params[i].no_hwmon);
    }
}
static int suspend_calls, resume_calls;
static int suspend_callback(struct tsens_priv *data)
{ assert(data == &priv); suspend_calls++; return -EBUSY; }
static int resume_callback(struct tsens_priv *data)
{ assert(data == &priv); resume_calls++; return 7; }
int main(void)
{
    reset(); assert(tsens_register(&priv) == 0 && added == 4 && actions == 4 && !warnings);
    release(); assert(removed == 4);
    reset(); fail_add = 2;
    assert(tsens_register(&priv) == 0 && added == 3 && actions == 3 && warnings == 1);
    assert(params[2].no_hwmon && !active[2]); release(); assert(removed == 3);
    reset(); fail_action = 3;
    assert(tsens_register(&priv) == 0 && added == 4 && actions == 3 && removed == 1 && warnings == 1);
    assert(params[3].no_hwmon && !active[3]); release(); assert(removed == 4);
    reset(); priv.ops = &generic_ops;
    assert(tsens_register(&priv) == 0 && !added && !actions && !warnings); release();
    reset(); fail_sensor = 2;
    assert(tsens_register(&priv) == -EPROBE_DEFER && added == 1 && actions == 1); release();
    reset(); no_sensors = true;
    assert(tsens_register(&priv) == -ENODEV && !added && !actions); release();
    struct device dev = {.non_driver_data = 1, .driver_data = &priv};
    const struct tsens_ops pm_ops = {.marker = 3, .suspend = suspend_callback, .resume = resume_callback};
    reset(); priv.ops = &pm_ops;
    assert(tsens_suspend(&dev) == -EBUSY && suspend_calls == 1);
    assert(tsens_resume(&dev) == 7 && resume_calls == 1);
    priv.ops = &generic_ops;
    assert(tsens_suspend(&dev) == 0 && tsens_resume(&dev) == 0);
    dev.driver_data = NULL;
    assert(tsens_suspend(&dev) == 0 && tsens_resume(&dev) == 0);
    /* Exercise the actual probe/remove call sites, before releasing devres. */
    reset(); irq_error = -EPROBE_DEFER;
    assert(tsens_probe(&platform) == -EPROBE_DEFER && !driver_running); release();
    reset(); init_error = -EIO;
    assert(tsens_probe(&platform) == -EIO && !driver_running); release();
    reset(); calibration_error = -EPROBE_DEFER;
    assert(tsens_probe(&platform) == -EPROBE_DEFER && !driver_running); release();
    reset(); fail_sensor = 2;
    assert(tsens_probe(&platform) == -EPROBE_DEFER && !driver_running); release();
    reset(); no_sensors = true;
    assert(tsens_probe(&platform) == -ENODEV && !driver_running); release();
    reset(); assert(tsens_probe(&platform) == 0 && driver_running);
    assert(platform.dev.driver_data == &priv && added == 4);
    assert(tsens_remove(&platform) == 0 && !driver_running); release();
    puts("PASS: sensor deferral/absence and PM callbacks use the actual device driver data");
    puts("PASS: probe failures and removal stop the driver before managed hwmon/sensor cleanup");
    return 0;
}
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('kernel_source', type=Path)
    parser.add_argument('--cc', default='cc')
    parser.add_argument('--runner')
    args = parser.parse_args()
    drivers = args.kernel_source / 'drivers/thermal/qcom'
    ipq = (drivers / 'tsens-ipq5018.c').read_text()
    common = (drivers / 'tsens-common.c').read_text()
    defines = '\n'.join(line for line in ipq.splitlines() if line.startswith('#define ')) + '\n'
    header = (drivers / 'tsens.h').read_text()
    defines += '\n'.join(line for line in header.splitlines()
                         if re.match(r'#define\s+(?:ONE_PT_CALIB2?|TWO_PT_CALIB|CAL_DEGC_PT[12]|SLOPE_FACTOR|SLOPE_DEFAULT)\s', line)) + '\n'
    trip_enum = re.search(r'enum tsens_trip_type \{.*?\};', ipq, re.S).group(0)
    functions = '\n'.join(function(ipq, name) for name in
                          ('code_to_degc', 'degc_to_code', 'set_trip_temp',
                           'set_trip_temp_ipq5018', 'get_temp_ipq5018', 'tsens_scheduler_fn'))
    functions += '\n' + function(ipq, 'disable_ipq5018') + '\n' + function(ipq, 'stop_ipq5018')
    functions += '\n' + function(common, 'init_common') + '\n' + function(ipq, 'init_ipq5018')
    functions += '\n' + function(common, 'compute_intercept_slope') + '\n' + function(ipq, 'calibrate_ipq5018')
    with tempfile.TemporaryDirectory(prefix='ipq5018-thermal-') as directory:
        registration = (drivers / 'tsens.c').read_text()
        hwmon = (HWMON_FIXTURE + function(registration, 'tsens_remove_hwmon') +
                 function(registration, 'tsens_register') + function(registration, 'tsens_suspend') +
                 function(registration, 'tsens_resume') + function(registration, 'tsens_probe') +
                 function(registration, 'tsens_remove') + HWMON_CASES)
        for name, fixture in (('io', defines + trip_enum + FIXTURE + functions + CASES), ('hwmon', hwmon)):
            source = Path(directory) / f'{name}.c'
            binary = Path(directory) / name
            source.write_text(fixture)
            command = [args.cc, '-std=c11', '-Wall', '-Wextra', '-Werror',
                       '-Wno-unused-parameter', '-Wno-unused-function', '-Wno-sign-compare',
                       str(source), '-o', str(binary)]
            if args.runner:
                command.append('-static')
            subprocess.run(command, check=True)
            subprocess.run(([args.runner] if args.runner else []) + [str(binary)], check=True)
    dt = (args.kernel_source / 'arch/arm64/boot/dts/qcom/ipq5018-thermal.dtsi').read_text()
    assert [int(n) for n in re.findall(r'temperature = <(\d+)>', dt)] == [100000, 80000, 70000, 0] * 4
    assert [int(n) for n in re.findall(r'hysteresis = <(\d+)>', dt)] == [2000] * 16
    print('PASS: all four thermal zones retain physical trip thresholds and hysteresis in milliCelsius')


if __name__ == '__main__':
    main()
