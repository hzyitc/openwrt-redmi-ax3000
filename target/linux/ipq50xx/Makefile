include $(TOPDIR)/rules.mk

BOARD:=ipq50xx
BOARDNAME:=Qualcomm Atheros IPQ50XX
SUBTARGETS:=arm aarch64

CPU_TYPE:=cortex-a53
FEATURES:=fpu ramdisk nand squashfs pcie

KERNEL_PATCHVER:=5.4

include $(INCLUDE_DIR)/target.mk

KERNELNAME:=Image dtbs

DEFAULT_PACKAGES += \
	uboot-envtools \
	kmod-qca-nss-dp swconfig \
	kmod-qca-nss-drv qca-nss-fw-ipq50xx-retail

$(eval $(call BuildTarget))
