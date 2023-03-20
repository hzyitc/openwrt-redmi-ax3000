include $(TOPDIR)/rules.mk
include $(INCLUDE_DIR)/kernel.mk

PKG_NAME:=qca-nss-drv
PKG_VERSION:=NHSS.QSDK.11.5.0.5
PKG_RELEASE:=2

PKG_SOURCE_PROTO:=git
PKG_SOURCE_URL:=https://git.codelinaro.org/clo/qsdk/oss/lklm/nss-drv
PKG_SOURCE_VERSION:=7563fe37340ec4a28b7821a0ac17608ff30e2a85

NSS_CLIENTS_DIR:=$(TOPDIR)/qca/src/qca-nss-clients

include $(INCLUDE_DIR)/package.mk

define KernelPackage/qca-nss-drv
  SECTION:=kernel
  CATEGORY:=Kernel modules
  SUBMENU:=Network Devices
  DEPENDS:=@(TARGET_ipq50xx||TARGET_ipq60xx||TARGET_ipq806x||TARGET_ipq807x) \
	+PACKAGE_kmod-qca-nss-gmac:kmod-qca-nss-gmac \
	+PACKAGE_kmod-qca-nss-dp:kmod-qca-nss-dp
  TITLE:=Kernel driver for NSS (core driver)
  FILES:=$(PKG_BUILD_DIR)/qca-nss-drv.ko
  AUTOLOAD:=$(call AutoLoad,32,qca-nss-drv)
endef

define KernelPackage/qca-nss-drv/install
	$(INSTALL_DIR) $(1)/lib/debug
	$(INSTALL_DIR) $(1)/etc/init.d
	$(INSTALL_DIR) $(1)/etc/sysctl.d
	$(INSTALL_DIR) $(1)/etc/hotplug.d/firmware
	$(INSTALL_DIR) $(1)/etc/config

	$(INSTALL_BIN) ./files/qca-nss-drv.debug $(1)/lib/debug/qca-nss-drv
	$(INSTALL_BIN) ./files/qca-nss-drv.init $(1)/etc/init.d/qca-nss-drv
	$(INSTALL_BIN) ./files/qca-nss-drv.sysctl $(1)/etc/sysctl.d/qca-nss-drv.conf
	$(INSTALL_BIN) ./files/qca-nss-drv.hotplug $(1)/etc/hotplug.d/firmware/10-qca-nss-fw
	$(INSTALL_BIN) ./files/qca-nss-drv.conf $(1)/etc/config/nss

endef

define KernelPackage/qca-nss-drv/Description
This package contains a NSS driver for QCA chipset
endef

define Build/InstallDev
	mkdir -p $(1)/usr/include/qca-nss-drv
	$(CP) $(PKG_BUILD_DIR)/exports/* $(1)/usr/include/qca-nss-drv/
ifneq (, $(findstring $(subtarget), "ipq807x" "ipq807x_64" "ipq60xx" "ipq60xx_64" "ipq50xx" "ipq50xx_64"))
	$(RM) $(1)/usr/include/qca-nss-drv/nss_ipsecmgr.h
	$(INSTALL_DIR) $(1)/usr/include/qca-nss-clients
	# $(CP) $(NSS_CLIENTS_DIR)/exports/nss_ipsecmgr.h $(1)/usr/include/qca-nss-clients/.
endif
endef

EXTRA_CFLAGS+= -I$(STAGING_DIR)/usr/include/qca-nss-gmac -I$(STAGING_DIR)/usr/include/qca-nss-dp -I$(STAGING_DIR)/usr/include/qca-ssdk

# Keeping default as ipq806x for branches that does not have subtarget framework
ifeq ($(CONFIG_TARGET_ipq),y)
subtarget:=$(SUBTARGET)
else
subtarget:=$(CONFIG_TARGET_BOARD)
endif

# ifeq ($(CONFIG_KERNEL_IPQ_MEM_PROFILE),256)
EXTRA_CFLAGS+= -DNSS_MEM_PROFILE_LOW
LOW_MEM_PROFILE_MAKE_OPTS=y
# else ifeq ($(CONFIG_LOWMEM_FLASH),y)
# EXTRA_CFLAGS+= -DNSS_MEM_PROFILE_LOW
# LOW_MEM_PROFILE_MAKE_OPTS=y
# else ifeq ($(CONFIG_KERNEL_IPQ_MEM_PROFILE),512)
# EXTRA_CFLAGS+= -DNSS_MEM_PROFILE_MEDIUM
# endif

ifeq ($(CONFIG_KERNEL_SKB_FIXED_SIZE_2K),y)
EXTRA_CFLAGS+= -DNSS_SKB_FIXED_SIZE_2K
endif

DRV_MAKE_OPTS:=
ifeq ($(LOW_MEM_PROFILE_MAKE_OPTS),y)
DRV_MAKE_OPTS+=NSS_DRV_C2C_ENABLE=n \
        NSS_DRV_CAPWAP_ENABLE=n \
        NSS_DRV_CLMAP_ENABLE=n \
        NSS_DRV_CRYPTO_ENABLE=n \
        NSS_DRV_DTLS_ENABLE=n \
        NSS_DRV_GRE_ENABLE=n \
        NSS_DRV_GRE_REDIR_ENABLE=n \
        NSS_DRV_GRE_TUNNEL_ENABLE=n \
        NSS_DRV_IGS_ENABLE=n \
        NSS_DRV_IPSEC_ENABLE=n \
        NSS_DRV_LAG_ENABLE=n \
        NSS_DRV_L2TP_ENABLE=n \
        NSS_DRV_MAPT_ENABLE=n \
        NSS_DRV_OAM_ENABLE=n \
        NSS_DRV_PPTP_ENABLE=n \
        NSS_DRV_PORTID_ENABLE=n \
        NSS_DRV_PVXLAN_ENABLE=n \
        NSS_DRV_QRFS_ENABLE=n \
        NSS_DRV_QVPN_ENABLE=n \
        NSS_DRV_RMNET_ENABLE=n \
        NSS_DRV_SHAPER_ENABLE=n \
        NSS_DRV_SJACK_ENABLE=n \
        NSS_DRV_TLS_ENABLE=n \
        NSS_DRV_TRUSTSEC_ENABLE=n \
        NSS_DRV_TSTAMP_ENABLE=n \
        NSS_DRV_TUN6RD_ENABLE=n \
        NSS_DRV_TUNIPIP6_ENABLE=n \
        NSS_DRV_VXLAN_ENABLE=n \
        NSS_DRV_MATCH_ENABLE=n \
        NSS_DRV_MIRROR_ENABLE=n \
        NSS_DRV_WIFI_EXT_VDEV_ENABLE=n \
        NSS_DRV_WIFI_MESH_ENABLE=n \
        NSS_DRV_IPV4_REASM_ENABLE=n \
        NSS_DRV_IPV6_REASM_ENABLE=n
# Disable PPE bridge support for IPQ50xx.
ifneq (, $(findstring $(subtarget), "ipq50xx"))
        DRV_MAKE_OPTS+=NSS_DRV_BRIDGE_ENABLE=n
endif
endif

# Disable DRV IPv6 support when global IPv6 support is disabled.
ifneq ($(CONFIG_IPV6),y)
DRV_MAKE_OPTS+=NSS_DRV_IPV6_ENABLE=n
endif

define Build/Configure
	$(LN) arch/nss_$(subtarget).h $(PKG_BUILD_DIR)/exports/nss_arch.h
endef

define Build/Compile
	$(MAKE) -C "$(LINUX_DIR)" $(strip $(DRV_MAKE_OPTS)) \
		CROSS_COMPILE="$(TARGET_CROSS)" \
		ARCH="$(LINUX_KARCH)" \
		M="$(PKG_BUILD_DIR)" \
		EXTRA_CFLAGS="$(EXTRA_CFLAGS)" SoC="$(subtarget)" \
		modules
endef

$(eval $(call KernelPackage,qca-nss-drv))
