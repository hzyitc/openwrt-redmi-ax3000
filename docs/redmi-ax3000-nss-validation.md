# Redmi AX3000 NSS validation

Use the QSDK 5.4 branch and `configs/redmi-ax3000-nss.config` as described
in the [build instructions](../README.md#how-to-build).

## Regression checks

After building the profile, run from the repository root:

```bash
python3 scripts/test-redmi-nss.py --rootfs build_dir/target-*/root-ipq50xx
```

The runner finds the prepared kernel, ECM and wpad-basic-wolfssl sources.
With multiple build trees, select them with `--kernel-source`,
`--ecm-source` and `--hostapd-source`; the last option takes the path to
`src/drivers/driver_nl80211.c`. Use `--rootfs /path/to/extracted-rootfs`
to check the root volume extracted from a factory image.

The checks cover:

- Rejection of merged layouts before entering the dual-slot upgrade path.
- Untagged and tagged hostapd VLAN messages.
- ECM request timing, jiffies wraparound and retries using the compiler's ABI.
- TSENS temperature conversion, trip register I/O, repeated alarm
  acknowledgements and sequential probe/remove cleanup paths.
- Packaged NSS modules, firmware, initial module options, startup links
  and permissions needed by the unprivileged ubus daemon.

The C fixtures use mocked kernel services. They do not establish hardware
register behavior, IRQ concurrency or memory-ordering correctness. Rootfs
checks verify packaging; runtime sensors and acceleration require the
checks below.

To run the C fixtures with the target ABI, use the built toolchain and
QEMU (installed separately):

```bash
python3 scripts/test-redmi-nss.py \
  --cc "$PWD"/staging_dir/toolchain-arm_*/bin/arm-openwrt-linux-muslgnueabi-gcc \
  --runner qemu-arm
```

## On-device checks

Check `cat /sys/module/ath11k/parameters/nss_offload` returns `1`. During
wired-to-Wi-Fi traffic, inspect the flow state under `/sys/kernel/debug/ecm`
for bridged flows (`is_routed=0`) in NSS accelerated mode (`accel_mode=2`).

Read the SoC thermal zones and ath11k hwmon temperatures; `45000` means
45°C. The IPQ5018 DT thresholds are 100, 80, 70 and 0°C with 2°C hysteresis.
Automatic CPU cooling and periodic thermal polling are not configured.

## Installation and UART limitations

The default upgrade handler supports the stock dual-slot partition layout.
It rejects merged layouts. A merged-layout installation procedure is not
provided by this repository; verify recovery support before using a custom
partition table or bootloader.

On a CR8809/IPQ5000 unit, cycling router power with a USB-to-UART adapter
attached caused QCN6122 initialization to stall and the kernel to panic.
A power cycle with the adapter disconnected succeeded. The electrical
cause was not established. The maintainer identifies the IPQ5018 UART as
1.8 V with pins shared with boot configuration; verify the adapter's
signal levels. See the [hardware note](https://github.com/hzyitc/openwrt-redmi-ax3000/issues/25#issuecomment-1817547019).
