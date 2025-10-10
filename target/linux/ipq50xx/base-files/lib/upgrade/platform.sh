. /lib/functions.sh

#RAMFS_COPY_BIN='fw_printenv fw_setenv'
RAMFS_COPY_BIN='dumpimage fw_printenv fw_setenv head seq'
RAMFS_COPY_DATA='/etc/fw_env.config /var/lock/fw_printenv.lock'

remove_oem_ubi_volume() {
	local oem_volume_name="$1"
	local oem_ubivol
	local mtdnum
	local ubidev

	mtdnum=$(find_mtd_index "$CI_UBIPART")
	if [ ! "$mtdnum" ]; then
		return
	fi

	ubidev=$(nand_find_ubi "$CI_UBIPART")
	if [ ! "$ubidev" ]; then
		ubiattach --mtdn="$mtdnum"
		ubidev=$(nand_find_ubi "$CI_UBIPART")
	fi

	if [ "$ubidev" ]; then
		oem_ubivol=$(nand_find_volume "$ubidev" "$oem_volume_name")
		[ "$oem_ubivol" ] && ubirmvol "/dev/$ubidev" --name="$oem_volume_name"
	fi
}


platform_check_image() {
	local board=$(board_name)
	case $board in
		redmi,ax3000|\
		xiaomi,cr881x)
			mi_dualboot_check_image "$1"
			return $?
			;;
		cmcc,pz-l8)
			return 0;
			;;
		*)
			v "Sysupgrade is not supported on your board($board) yet."
			return 1
			;;
	esac
}

platform_do_upgrade() {
	local board=$(board_name)
	case $board in
		cmcc,pz-l8)
			local delay

			delay=$(fw_printenv bootdelay)
			[ -z "$delay" ] || [ "$delay" -eq "0" ] && \
				fw_setenv bootdelay 3

			elecom_upgrade_prepare

			remove_oem_ubi_volume bt_fw
			remove_oem_ubi_volume ubi_rootfs
			remove_oem_ubi_volume wifi_fw
			nand_do_upgrade "$1"
			;;
		redmi,ax3000|\
		xiaomi,cr881x)
			mi_dualboot_do_upgrade "$1"
			;;
		*)
			default_do_upgrade "$1"
			;;
	esac
}
