. /lib/functions/system.sh

RAMFS_COPY_BIN='fw_printenv fw_setenv'
RAMFS_COPY_DATA='/etc/fw_env.config /var/lock/fw_printenv.lock'

mi_check_image() {
	local ret=0

	local file_type="$(identify "$1")"
	if [ "$file_type" != ubi ]; then
		echo "Unsupport file type: $file_type."
		echo "Please use ubi file."
		ret=1
	fi

	local mtd="$(grep -oE 'ubi.mtd=[a-zA-Z0-9\-\_]*' /proc/cmdline | cut -d'=' -f2)"
	if [[ "$mtd" != "rootfs" ]] && [[ "$mtd" != "rootfs_1" ]]; then
		echo "Unable to determine UBIPART: ubi.mtd=$mtd."
		ret=1
	fi

	if ! fw_printenv >/dev/null; then
		echo "Fail to read env."
		ret=1
	fi

	return $ret
}

mi_do_upgrade() {
	mkdir -p /var/lock
	fw_printenv >/dev/null || return 1

	local mtd="$(grep -oE 'ubi.mtd=[a-zA-Z0-9\-\_]*' /proc/cmdline | cut -d'=' -f2)"
	case $mtd in
		rootfs)
			CI_UBIPART="rootfs_1"
			local current=0
			;;
		rootfs_1)
			CI_UBIPART="rootfs"
			local current=1
			;;
		*)
			echo "Unable to determine UBIPART: ubi.mtd=$mtd"
			return 1
			;;
	esac

	local mtdnum="$(find_mtd_index $CI_UBIPART)"
	ubiformat "/dev/mtd$mtdnum" -f "$1" -y || return 1

	local conf_tar="/tmp/sysupgrade.tgz"
	if [ -f "$conf_tar" ]; then
		ubiattach --mtdn "${mtdnum}"

		CI_UBIPART="$CI_UBIPART"
		CI_ROOTPART="ubi_rootfs"
		nand_restore_config "$conf_tar"
	fi

	# NOTE: u-boot has a bug.
	#   If the target ubi don't contain `kernel` volume,
	#   it will always set `flag_try_sys1_failed` to 1.

	# Clean the failed flag. So we can boot to them.
	fw_setenv flag_try_sys1_failed 0 || return 1
	fw_setenv flag_try_sys2_failed 0 || return 1

	# Tell u-boot that the current is able to boot.
	fw_setenv flag_last_success $current || return 1

	# Tell u-boot to try to boot the other system.
	# If it failed, it will clean this flag.
	fw_setenv flag_ota_reboot 1 || return 1

	# When this flag is set to 0 and the `flag_ota_reboot` is 1,
	# the u-boot will roll back to `flag_last_success`.
	fw_setenv flag_boot_success || return 1
}

platform_check_image() {
	local board=$(board_name)
	case $board in
		redmi,ax3000)
			mi_check_image "$1"
			return $?
			;;
		*)
			echo "Sysupgrade is not supported on your board($board) yet."
			return 1
			;;
	esac
}

platform_do_upgrade() {
	local board=$(board_name)
	case $board in
		redmi,ax3000)
			mi_do_upgrade "$1"
			;;
		*)
			default_do_upgrade "$1"
			;;
	esac
}
