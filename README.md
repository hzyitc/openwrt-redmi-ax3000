# openwrt-redmi-ax3000

`Openwrt` for `Redmi AX3000` / `Xiaomi CR8806` / `Xiaomi CR8808` / `Xiaomi CR8809`

**!!! NOTE: This is the main development branch which using mainline `Linux LTS 5.4` !!!**

If you need more stable versions, please checkout the following branches which using QSDK kernel
- [`ipq50xx-qsdk-kernel-5.4-openwrt-21.02-qsdk-11.5.05.841.1029`](https://github.com/hzyitc/openwrt-redmi-ax3000/tree/ipq50xx-qsdk-kernel-5.4-openwrt-21.02-qsdk-11.5.05.841.1029) 
- [`ipq50xx-qsdk-kernel-4.4-openwrt-21.02-qsdk-11.4.0.5.7418`](https://github.com/hzyitc/openwrt-redmi-ax3000/tree/ipq50xx-qsdk-kernel-4.4-openwrt-21.02-qsdk-11.4.0.5.7418)

| Device        | Boot | Switch | CPU Ethernet | NSS NAT | 2.4G WiFi   | 5G WiFi |
| :-:           | :-:  | :-:    | :-:          | :-:     | :-:         | :-:     |
| Redmi AX3000  | ❓ No test |
| Xiaomi CR8806 | ✔️  | ✔️     | ✔️          | ❌      | ⚠️ Unstable | ✔️¹    |
| Xiaomi CR8808 | ✔️  | ✔️     | ✔️          | ❌      | ⚠️ Unstable | ✔️¹    |
| Xiaomi CR8809 | ❓ No test |
> NOTE¹: For 160MHz, `Country Code` and `Width` need to be set correctly. And wait 1 minute for radar detection, then the WiFi will be appeareed.
>
>	```
>	uci -q batch <<-EOF
>		wireless.radio1.country='CN'
>		wireless.radio1.channel='64'
>	EOF
>	```

## How to build

OS: `Ubuntu 20.04 (focal)`

```bash
# Install dependencies
sudo add-apt-repository ppa:npalix/coccinelle
sudo apt update
sudo apt install build-essential clang flex g++ gawk gcc-multilib gettext \
  git libncurses5-dev libssl-dev python3-distutils rsync unzip zlib1g-dev \
  coccinelle

# Clone this repo
git clone https://github.com/hzyitc/openwrt-redmi-ax3000
cd openwrt-redmi-ax3000

# Update and install feeds
./scripts/feeds update -a
./scripts/feeds install -a

# Configure
make menuconfig

# Download
make -j16 download

# Build
make -j$(nproc)
```

## How to install

### Get `UART` access

> Input from `UART` will be allowed after a successful `TFTP recovery`.

1. Connect `UART` and `LAN`.

2. Download the vendor firmware:

	Offical website: https://www.miwifi.com/miwifi_download.html

	| Device        | URL                                                                                                |
	| :-:           | :-:                                                                                                |
	| Redmi AX3000  | https://cdn.cnbj1.fds.api.mi-img.com/xiaoqiang/rom/ra81/miwifi_ra81_firmware_1dd69c_1.0.33.bin     |
	| Xiaomi CR8806 | https://cdn.cnbj1.fds.api.mi-img.com/xiaoqiang/rom/cr8806/miwifi_cr8806_firmware_fe70b_6.2.14.bin  |
	| Xiaomi CR8808 | https://cdn.cnbj1.fds.api.mi-img.com/xiaoqiang/rom/cr8808/miwifi_cr8808_firmware_9d216_6.2.11.bin  |
	| Xiaomi CR8809 | https://cdn.cnbj1.fds.api.mi-img.com/xiaoqiang/rom/cr8809/miwifi_cr8809_firmware_b814a_6.2.102.bin |

3. Use [`MIWIFIRepairTool`](https://bigota.miwifi.com/xiaoqiang/tools/MIWIFIRepairTool.x86.zip) to recover the device's firmware.

	Offical tutorial: https://www.xiaomi.cn/post/19134127

	> This tool simply does `TFTP recovery`. You can use other `DHCP` and `TFTP` server as well.
	>
	> Here are some useful links:
	>
	>> https://forum.openwrt.org/t/adding-openwrt-support-for-xiaomi-redmi-router-ax6s-xiaomi-router-ax3200/111085/513
	>>
	>> https://github.com/mikeeq/xiaomi_ax3200_openwrt#uart-flash
	>>
	>> https://openwrt.org/inbox/toh/xiaomi/xiaomi_ax3600#tftp_recovery

4. Hold the `reset` button and reboot the router until the `system` LED blink.

5. Wait until the firmware being flashed.

6. Unplug then plug back in the power.

7. Send any key stroke to `UART` to interrupt the `U-boot`.

8. Run the following command inside `U-boot`:

	```shell
	setenv boot_wait on
	setenv uart_en 1
	saveenv
	```

Now we have enabled `UART`.

### Flash Openwrt

#### a. Use `U-boot` to flash

Download [`openwrt-ipq50xx-arm-redmi_ax3000-squashfs-nand-factory.ubi`](https://github.com/hzyitc/openwrt-redmi-ax3000/releases/latest/download/openwrt-ipq50xx-arm-redmi_ax3000-squashfs-nand-factory.ubi) and put it into TFTP root.

Then run the following command inside `U-boot`:

```shell
# This router ip
setenv ipaddr 192.168.1.2
# TFTP server ip
setenv serverip 192.168.1.1

# Download the firmware to the RAM
tftpboot openwrt-ipq50xx-arm-redmi_ax3000-squashfs-nand-factory.ubi

# Flash it as system 2
flash rootfs_1
setenv flag_try_sys2_failed 0
setenv flag_boot_rootfs 1
setenv flag_last_success 1
saveenv

# Flash it as system 1
# flash rootfs
# setenv flag_try_sys1_failed 0
# setenv flag_boot_rootfs 0
# setenv flag_last_success 0
# saveenv

# Reboot
reset
```

#### b. Use `miwifi` (the vendor firmware) to flash

```bash
cd /tmp
wget https://github.com/hzyitc/openwrt-redmi-ax3000/releases/latest/download/openwrt-ipq50xx-arm-redmi_ax3000-squashfs-nand-factory.ubi

# Check your partition table
# cat /proc/mtd
[[ "$(grep '"rootfs"' /proc/mtd | cut -d':' -f1)" == "mtd18" ]] || exit
[[ "$(grep '"rootfs_1"' /proc/mtd | cut -d':' -f1)" == "mtd19" ]] || exit

# Detect the current system slot and flash into the other one
# cat /proc/cmdline
mtd="$(grep -oE 'ubi.mtd=[a-zA-Z0-9\-\_]*' /proc/cmdline | cut -d'=' -f2)"
if [[ "$mtd" == "rootfs" ]]; then
	# Flash it as system 2
	ubiformat /dev/mtd19 -f openwrt-ipq50xx-arm-redmi_ax3000-squashfs-nand-factory.ubi
	nvram set flag_try_sys2_failed=0
	nvram set flag_boot_rootfs=1
	nvram set flag_last_success=1
	nvram commit
else if [[ "$mtd" == "rootfs_1" ]]; then
	# Flash it as system 1
	ubiformat /dev/mtd18 -f openwrt-ipq50xx-arm-redmi_ax3000-squashfs-nand-factory.ubi
	nvram set flag_try_sys1_failed=0
	nvram set flag_boot_rootfs=0
	nvram set flag_last_success=0
	nvram commit
fi

# Reboot
reboot
```

## Related links

[`openwrt/openwrt`](https://github.com/openwrt/openwrt) - Openwrt official repository

[`qsdk`](https://git.codelinaro.org/clo/qsdk) - QSDK official repository

[`quic/qca-sdk-nss-fw`](https://github.com/quic/qca-sdk-nss-fw) - NSS firmware

[`quic/upstream-wifi-fw`](https://github.com/quic/upstream-wifi-fw) - WiFi firmware

[`qca/qca-swiss-army-knife`](https://github.com/qca/qca-swiss-army-knife) - BDF tools

[`Telecominfraproject/wlan-ap`](https://github.com/Telecominfraproject/wlan-ap) - another Openwrt which support `ipq50xx`
