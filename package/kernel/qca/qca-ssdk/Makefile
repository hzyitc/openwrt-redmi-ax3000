
include $(TOPDIR)/rules.mk
include $(INCLUDE_DIR)/kernel.mk

PKG_NAME:=qca-ssdk
PKG_VERSION:=NHSS.QSDK.11.5.0.5
PKG_RELEASE:=1

PKG_SOURCE_PROTO:=git
PKG_SOURCE_URL:=https://git.codelinaro.org/clo/qsdk/oss/lklm/qca-ssdk
PKG_SOURCE_VERSION:=0d6d410637648b1bea0dede48d3fab791689cfce

ifeq ($(CONFIG_TARGET_ipq),y)
	subtarget:=$(SUBTARGET)
else
	subtarget:=$(CONFIG_TARGET_BOARD)
endif

ifneq (, $(findstring _64, $(subtarget)))
	hal_arch:=$(subst _64,,$(subtarget))
else ifneq (, $(findstring _32, $(subtarget)))
	hal_arch:=$(subst _32,,$(subtarget))
else
	hal_arch:=$(subtarget)
endif

LOCAL_VARIANT=$(patsubst qca-ssdk-%,%,$(patsubst qca-ssdk-%,%,$(BUILD_VARIANT)))
include $(INCLUDE_DIR)/package.mk

define KernelPackage/qca-ssdk/default-nohnat
  SECTION:=kernel
  CATEGORY:=Kernel modules
  SUBMENU:=Network Devices
  TITLE:=Kernel driver for QCA SSDK
  FILES:=$(PKG_BUILD_DIR)/build/bin/qca-ssdk.ko
  AUTOLOAD:=$(call AutoLoad,30,qca-ssdk)
  PROVIDES:=qca-ssdk
endef

define KernelPackage/qca-ssdk-nohnat
$(call KernelPackage/qca-ssdk/default-nohnat)
  DEPENDS:=@(TARGET_ar71xx||TARGET_ipq50xx||TARGET_ipq60xx||TARGET_ipq806x||TARGET_ipq807x||TARGET_ipq95xx)
  VARIANT:=nohnat

  ifneq (, $(findstring $(hal_arch), "ipq50xx"))
    ifeq (, $(CONFIG_LOWMEM_FLASH))
      ifneq ($(LINUX_VERSION),$(filter 5.4%,$(LINUX_VERSION)))
      DEPENDS+=kmod-ipt-filter +kmod-ppp
      QCASSDK_CONFIG_OPTS+= HNAT_FEATURE=enable
      endif
    endif
  endif
endef

define KernelPackage/qca-ssdk-nohnat/Description
This package contains a qca-ssdk driver for QCA chipset
endef

define KernelPackage/qca-ssdk-hnat
$(call KernelPackage/qca-ssdk/default-nohnat)
  DEPENDS:=@(TARGET_ar71xx||TARGET_ipq40xx||TARGET_ipq806x) \
	+kmod-ipt-extra +kmod-ipt-filter +kmod-ppp \
	+(TARGET_ipq40xx||TARGET_ipq806x):kmod-qca-rfs
  TITLE+= (hnat)
  VARIANT:=hnat
endef

define KernelPackage/qca-ssdk-hnat/Description
This package contains a qca-ssdk-hnat driver for QCA chipset
endef

GCC_VERSION=$(shell echo "$(CONFIG_GCC_VERSION)" | sed 's/[^0-9.]*\([0-9.]*\).*/\1/')
GCC_VERSION:=$(shell echo "$(GCC_VERSION)" | sed -E 's/^([0-9]{1,2})([0-9]{2})([0-9]{2})$$/\1.\2.\3/')
GCC_VERSION:=$(shell echo "$(GCC_VERSION)" | sed -E 's/0([0-9])/\1/g')
ifeq ($(GCC_VERSION), 4.8)
	GCC_VERSION=4.8.3
endif

ifdef CONFIG_TOOLCHAIN_BIN_PATH
	TOOLCHAIN_BIN_PATH=$(CONFIG_TOOLCHAIN_BIN_PATH)
else
	TOOLCHAIN_BIN_PATH=$(TOOLCHAIN_DIR)/bin
endif

ifdef CONFIG_TARGET_NAME
QCASSDK_CONFIG_OPTS+= \
		      TARGET_NAME=$(CONFIG_TARGET_NAME)
endif

QCASSDK_CONFIG_OPTS+= TOOL_PATH=$(TOOLCHAIN_BIN_PATH) \
                SYS_PATH=$(LINUX_DIR) \
                TOOLPREFIX=$(TARGET_CROSS) \
                KVER=$(LINUX_VERSION) \
                ARCH=$(LINUX_KARCH) \
		TARGET_SUFFIX=$(CONFIG_TARGET_SUFFIX) \
		GCC_VERSION=$(GCC_VERSION) \
		CFLAGS=-I$(STAGING_DIR)/usr/include

ifeq ($(LOCAL_VARIANT),hnat)
    QCASSDK_CONFIG_OPTS+= HNAT_FEATURE=enable
    ifeq ($(CONFIG_TARGET_ar71xx),)
    	QCASSDK_CONFIG_OPTS+= RFS_FEATURE=enable
    endif
endif

ifneq (, $(findstring $(hal_arch), "ipq95xx"))
    QCASSDK_CONFIG_OPTS+= CHIP_TYPE=APPE
endif

ifneq (, $(findstring $(hal_arch), "ipq60xx" "ipq807x" "ipq95xx"))
    QCASSDK_CONFIG_OPTS+= PTP_FEATURE=enable
endif

# ifneq (, $(findstring $(CONFIG_KERNEL_IPQ_MEM_PROFILE), 256 512)$(CONFIG_LOWMEM_FLASH))
	QCASSDK_CONFIG_OPTS+= MINI_SSDK=enable

	ifneq (, $(findstring $(hal_arch), "ipq807x"))
		QCASSDK_CONFIG_OPTS+= CHIP_TYPE=HPPE
	else ifneq (, $(findstring $(hal_arch), "ipq60xx"))
		QCASSDK_CONFIG_OPTS+= CHIP_TYPE=CPPE
	else ifneq (, $(findstring $(hal_arch), "ipq50xx"))
		QCASSDK_CONFIG_OPTS+= ISISC_ENABLE=enable
		QCASSDK_CONFIG_OPTS+= CHIP_TYPE=MP

		# ifeq (, $(CONFIG_LOWMEM_FLASH))
		# 	ifeq (, $(findstring $(CONFIG_KERNEL_IPQ_MEM_PROFILE), 256))
		# 		QCASSDK_CONFIG_OPTS+= MINI_SSDK=disable
		# 	endif
		# endif
	endif

	QCASSDK_CONFIG_OPTS+= PTP_FEATURE=disable
# endif

# ifeq ($(CONFIG_TARGET_ipq806x_QSDK_Standard),)
# 	QCASSDK_CONFIG_OPTS+= HK_CHIP=enable
# endif

define Build/InstallDev
	$(INSTALL_DIR) $(1)/usr/include/qca-ssdk
	$(INSTALL_DIR) $(1)/usr/include/qca-ssdk/api
	$(INSTALL_DIR) $(1)/usr/include/qca-ssdk/ref
	$(INSTALL_DIR) $(1)/usr/include/qca-ssdk/fal
	$(INSTALL_DIR) $(1)/usr/include/qca-ssdk/sal
	$(INSTALL_DIR) $(1)/usr/include/qca-ssdk/init
	$(CP) -rf $(PKG_BUILD_DIR)/include/api/sw_ioctl.h $(1)/usr/include/qca-ssdk/api
	if [ -f $(PKG_BUILD_DIR)/include/ref/ref_vsi.h ]; then \
	$(CP) -rf $(PKG_BUILD_DIR)/include/ref/ref_vsi.h $(1)/usr/include/qca-ssdk/ref/; \
	fi
	if [ -f $(PKG_BUILD_DIR)/include/ref/ref_fdb.h ]; then \
	$(CP) -rf $(PKG_BUILD_DIR)/include/ref/ref_fdb.h $(1)/usr/include/qca-ssdk/ref/; \
	fi
	if [ -f $(PKG_BUILD_DIR)/include/ref/ref_port_ctrl.h ]; then \
	$(CP) -rf $(PKG_BUILD_DIR)/include/ref/ref_port_ctrl.h $(1)/usr/include/qca-ssdk/ref/; \
	fi
	if [ -f $(PKG_BUILD_DIR)/include/init/ssdk_init.h ]; then \
	$(CP) -rf $(PKG_BUILD_DIR)/include/init/ssdk_init.h $(1)/usr/include/qca-ssdk/init/; \
	fi
	if [ -f $(PKG_BUILD_DIR)/include/init/ssdk_netlink.h ]; then \
	$(CP) -rf $(PKG_BUILD_DIR)/include/init/ssdk_netlink.h $(1)/usr/include/qca-ssdk/init/; \
	fi
	$(CP) -rf $(PKG_BUILD_DIR)/include/fal $(1)/usr/include/qca-ssdk
	$(CP) -rf $(PKG_BUILD_DIR)/include/common/*.h $(1)/usr/include/qca-ssdk
	$(CP) -rf $(PKG_BUILD_DIR)/include/sal/os/linux/*.h $(1)/usr/include/qca-ssdk
	$(CP) -rf $(PKG_BUILD_DIR)/include/sal/os/*.h $(1)/usr/include/qca-ssdk

endef

define Build/Compile
	$(MAKE) -C $(PKG_BUILD_DIR) $(strip $(QCASSDK_CONFIG_OPTS))
endef

define KernelPackage/qca-ssdk-nohnat/install
	$(INSTALL_DIR) $(1)/etc/init.d
	$(INSTALL_BIN) ./files/qca-ssdk $(1)/etc/init.d/qca-ssdk
endef

define KernelPackage/qca-ssdk-hnat/install
	$(INSTALL_DIR) $(1)/etc/init.d
	$(INSTALL_BIN) ./files/qca-ssdk $(1)/etc/init.d/qca-ssdk
endef

$(eval $(call KernelPackage,qca-ssdk-nohnat))
$(eval $(call KernelPackage,qca-ssdk-hnat))
