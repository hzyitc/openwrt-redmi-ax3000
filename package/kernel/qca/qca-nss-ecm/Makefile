include $(TOPDIR)/rules.mk
include $(INCLUDE_DIR)/kernel.mk

PKG_NAME:=qca-nss-ecm
PKG_VERSION:=NHSS.QSDK.11.5.0.5.1
PKG_RELEASE:=2

PKG_SOURCE_PROTO:=git
PKG_SOURCE_URL:=https://git.codelinaro.org/clo/qsdk/oss/lklm/qca-nss-ecm
PKG_SOURCE_VERSION:=2ee73530d3bf7b6c0e00707daf98ce04d7e0503d
PKG_MIRROR_HASH:=skip

LOCAL_VARIANT=$(patsubst qca-nss-ecm-%,%,$(patsubst qca-nss-ecm-%,%,$(BUILD_VARIANT)))
include $(INCLUDE_DIR)/package.mk

ifeq ($(CONFIG_QCA_NSS_ECM_EXAMPLES_PCC),y)
       FILES_EXAMPLES=$(PKG_BUILD_DIR)/examples/ecm_pcc_test.ko
endif

ifeq ($(CONFIG_QCA_NSS_ECM_EXAMPLES_MARK),y)
       FILES_EXAMPLES+=$(PKG_BUILD_DIR)/examples/ecm_mark_test.ko
endif

#Explicitly enable OVS external module, if ovsmgr is enabled.
ifneq ($(CONFIG_PACKAGE_kmod-qca-ovsmgr),)
CONFIG_QCA_NSS_ECM_OVS=y
endif

ifeq ($(CONFIG_QCA_NSS_ECM_OVS),y)
       FILES_EXAMPLES+=$(PKG_BUILD_DIR)/examples/ecm_ovs.ko
endif

define KernelPackage/qca-nss-ecm/Default
  SECTION:=kernel
  CATEGORY:=Kernel modules
  SUBMENU:=Network Support
  DEPENDS:=@(TARGET_ipq50xx||TARGET_ipq60xx||TARGET_ipq806x||TARGET_ipq807x) \
	+kmod-ipt-conntrack +iptables-mod-extra \
	+kmod-qca-nss-drv \
	+kmod-pppoe \
	+PACKAGE_kmod-qca-ovsmgr:kmod-qca-ovsmgr
  TITLE:=QCA NSS Enhanced Connection Manager (ECM)
  FILES:=$(PKG_BUILD_DIR)/*.ko $(FILES_EXAMPLES) $(PKG_BUILD_DIR)/examples/ecm_ae_select.ko
  KCONFIG:= \
	CONFIG_NF_CONNTRACK_EVENTS=y \
	CONFIG_NF_CONNTRACK_CHAIN_EVENTS=y \
	CONFIG_NF_CONNTRACK_DSCPREMARK_EXT=y
  MENU:=1
  PROVIDES:=kmod-qca-nss-ecm
endef

define KernelPackage/qca-nss-ecm-nonss/Default
  SECTION:=kernel
  CATEGORY:=Kernel modules
  SUBMENU:=Network Support
  DEPENDS:=@TARGET_ipq50xx \
	+kmod-ipt-conntrack +iptables-mod-extra \
	+kmod-shortcut-fe-drv \
	+kmod-bonding \
	+kmod-nat46 +kmod-pppoe +kmod-l2tp +kmod-pppol2tp +kmod-pptp \
	+PACKAGE_kmod-qca-ovsmgr:kmod-qca-ovsmgr \
	+PACKAGE_kmod-qca-mcs:kmod-qca-mcs \
	+PACKAGE_kmod-qca-hyfi-bridge:kmod-qca-hyfi-bridge \
	PACKAGE_kmod-emesh-sp:kmod-emesh-sp
  TITLE:=QCA NSS Enhanced Connection Manager (ECM)
  FILES:=$(PKG_BUILD_DIR)/*.ko $(FILES_EXAMPLES) $(PKG_BUILD_DIR)/examples/ecm_ae_select.ko
  KCONFIG:= \
	CONFIG_NF_CONNTRACK_EVENTS=y \
	CONFIG_NF_CONNTRACK_CHAIN_EVENTS=y \
	CONFIG_NF_CONNTRACK_DSCPREMARK_EXT=y
  MENU:=1
  PROVIDES:=kmod-qca-nss-ecm
endef

define KernelPackage/qca-nss-ecm/Description/Default
This package contains the QCA NSS Enhanced Connection Manager
endef

define KernelPackage/qca-nss-ecm/Default/install
	$(INSTALL_DIR) $(1)/etc/init.d $(1)/usr/bin $(1)/lib/netifd/offload $(1)/etc/config $(1)/etc/sysctl.d
	$(INSTALL_BIN) ./files/qca-nss-ecm.init $(1)/etc/init.d/qca-nss-ecm
	$(INSTALL_BIN) ./files/ecm_dump.sh $(1)/usr/bin/
	$(INSTALL_BIN) ./files/on-demand-down $(1)/lib/netifd/offload/on-demand-down
	$(INSTALL_DATA) ./files/qca-nss-ecm.uci $(1)/etc/config/ecm
	$(INSTALL_BIN) ./files/qca-nss-ecm.sysctl $(1)/etc/sysctl.d/qca-nss-ecm.conf
# ifeq ($(CONFIG_KERNEL_IPQ_MEM_PROFILE),256)
# 	echo 'net.netfilter.nf_conntrack_max=2048' >> $(1)/etc/sysctl.d/qca-nss-ecm.conf
# else ifeq ($(CONFIG_LOWMEM_FLASH),y)
# 	echo 'net.netfilter.nf_conntrack_max=2048' >> $(1)/etc/sysctl.d/qca-nss-ecm.conf
# else ifeq ($(CONFIG_KERNEL_IPQ_MEM_PROFILE),512)
# 	echo 'net.netfilter.nf_conntrack_max=8192' >> $(1)/etc/sysctl.d/qca-nss-ecm.conf
# endif
endef

# Variant with additional features enabled for standard profile
define KernelPackage/qca-nss-ecm-standard
  $(call KernelPackage/qca-nss-ecm/Default)
  TITLE+= (with standard features)
  VARIANT:=standard
  DEPENDS+=+PACKAGE_kmod-qca-mcs:kmod-qca-mcs
endef

define KernelPackage/qca-nss-ecm-standard/Description
  $(call KernelPackage/qca-nss-ecm/Description/Default)
endef

define KernelPackage/qca-nss-ecm-standard/install
$(call KernelPackage/qca-nss-ecm/Default/install, $(1))
endef

# Variant with additional features enabled for premium profile
define KernelPackage/qca-nss-ecm-premium/Default
$(call KernelPackage/qca-nss-ecm/Default)
  TITLE+= (with premium features)
  VARIANT:=premium
  DEPENDS+= \
	+kmod-shortcut-fe-drv \
	+kmod-bonding \
	+kmod-nat46 +kmod-l2tp +kmod-pppol2tp +kmod-pptp \
	+PACKAGE_kmod-qca-mcs:kmod-qca-mcs \
	+PACKAGE_kmod-qca-hyfi-bridge:kmod-qca-hyfi-bridge \
	PACKAGE_kmod-emesh-sp:kmod-emesh-sp
endef

define KernelPackage/qca-nss-ecm-nonss
  $(call KernelPackage/qca-nss-ecm-nonss/Default)
  TITLE+= (with no-nss for host mode)
  VARIANT:=nonss
endef

define KernelPackage/qca-nss-ecm-premium/Description/Default
$(call KernelPackage/qca-nss-ecm/Description/Default)
with the premium features enabled
endef

define KernelPackage/qca-nss-ecm-nonss/Description/Default
$(call KernelPackage/qca-nss-ecm/Description/Default)
with the No-NSS features enabled
endef

define KernelPackage/qca-nss-ecm-premium/Default/install
$(call KernelPackage/qca-nss-ecm/install)
endef

define KernelPackage/qca-nss-ecm-nonss/install
$(call KernelPackage/qca-nss-ecm-standard/install, $(1))
endef

define KernelPackage/qca-nss-ecm-premium
$(call KernelPackage/qca-nss-ecm-premium/Default)
endef

define KernelPackage/qca-nss-ecm-premium/Description
$(call KernelPackage/qca-nss-ecm-premium/Description/Default)
endef

define KernelPackage/qca-nss-ecm-premium/install
$(call KernelPackage/qca-nss-ecm-standard/install, $(1))
endef

# Variant with additional features enabled for noload profile
define KernelPackage/qca-nss-ecm-noload
  $(call KernelPackage/qca-nss-ecm/Default)
  TITLE+= (with noload features)
  PROVIDES:=kmod-qca-nss-ecm
  VARIANT:=noload
  DEPENDS+= \
	+kmod-shortcut-fe-drv \
	+kmod-bonding \
	+kmod-l2tp +kmod-pppol2tp +kmod-pptp \
	+PACKAGE_kmod-qca-mcs:kmod-qca-mcs
endef

define KernelPackage/qca-nss-ecm-noload/Description
  $(call KernelPackage/qca-nss-ecm/Description/Default)
  When selected, this package installs the driver but does not load it at init.
endef

define KernelPackage/qca-nss-ecm-noload/install
$(call KernelPackage/qca-nss-ecm/Default/install, $(1))
	#
	# Remove the START line from the init script, so that the symlink
	# in the /etc/rc.d directory is not created.
	#
	sed -i '/START=/d' $(1)/etc/init.d/qca-nss-ecm
endef

define KernelPackage/qca-nss-ecm-premium-noload
  $(call KernelPackage/qca-nss-ecm-premium/Default)
  PROVIDES:=kmod-qca-nss-ecm-premium
endef

define KernelPackage/qca-nss-ecm-premium-noload/Description
  $(call KernelPackage/qca-nss-ecm-premium/Description/Default)
  When selected, this package installs the driver but does not load it at init.
endef

define KernelPackage/qca-nss-ecm-premium-noload/install
$(call KernelPackage/qca-nss-ecm-premium/Default/install, $(1))
endef

define Build/InstallDev/qca-nss-ecm
	$(INSTALL_DIR) $(1)/usr/include/qca-nss-ecm
	$(CP) $(PKG_BUILD_DIR)/exports/* $(1)/usr/include/qca-nss-ecm/
endef

define Build/InstallDev
	$(call Build/InstallDev/qca-nss-ecm,$(1))
endef

ifneq ($(VARIANT), nonss)
EXTRA_CFLAGS+= \
	-I$(STAGING_DIR)/usr/include/qca-nss-drv
endif

EXTRA_CFLAGS+= \
	-I$(STAGING_DIR)/usr/include/qca-nss-drv \
	-I$(STAGING_DIR)/usr/include/shortcut-fe \
	-I$(STAGING_DIR)/usr/include/nat46

ifeq ($(CONFIG_PACKAGE_kmod-qca-hyfi-bridge), y)
ECM_MAKE_OPTS:=ECM_CLASSIFIER_HYFI_ENABLE=y
EXTRA_CFLAGS+= -I$(STAGING_DIR)/usr/include/hyfibr
endif

ifeq ($(CONFIG_PACKAGE_kmod-qca-mcs), y)
ECM_MAKE_OPTS+=ECM_MULTICAST_ENABLE=y
EXTRA_CFLAGS+= -I$(STAGING_DIR)/usr/include/qca-mcs
endif

ifneq ($(LOCAL_VARIANT),standard)
ECM_MAKE_OPTS+=	ECM_INTERFACE_IPSEC_ENABLE=y \
		ECM_INTERFACE_PPTP_ENABLE=y \
		ECM_INTERFACE_L2TPV2_ENABLE=y \
		ECM_INTERFACE_GRE_TAP_ENABLE=y \
		ECM_INTERFACE_GRE_TUN_ENABLE=y \
		ECM_INTERFACE_SIT_ENABLE=y \
		ECM_INTERFACE_TUNIPIP6_ENABLE=y \
		ECM_INTERFACE_RAWIP_ENABLE=y

ifeq ($(CONFIG_TARGET_ipq_ipq40xx)$(CONFIG_TARGET_ipq40xx),)
ECM_MAKE_OPTS+=ECM_INTERFACE_BOND_ENABLE=y
endif
endif

# ifneq ($(CONFIG_KERNEL_IPQ_MEM_PROFILE),256)
# ifneq ($(CONFIG_LOWMEM_FLASH),y)
ifneq ($(CONFIG_XFRM),)
ECM_MAKE_OPTS+=ECM_XFRM_ENABLE=y
endif
# ECM_MAKE_OPTS+=ECM_FRONT_END_SFE_ENABLE=y
ECM_MAKE_OPTS+=ECM_NON_PORTED_SUPPORT_ENABLE=y
# endif
# endif

# ifeq ($(CONFIG_KERNEL_IPQ_MEM_PROFILE),256)
# ECM_MAKE_OPTS+=ECM_FRONT_END_CONN_LIMIT_ENABLE=y
# else ifeq ($(CONFIG_LOWMEM_FLASH),y)
# ECM_MAKE_OPTS+=ECM_FRONT_END_CONN_LIMIT_ENABLE=y
# endif

# ifneq ($(CONFIG_PACKAGE_kmod-nat46),)
# ECM_MAKE_OPTS+=ECM_INTERFACE_MAP_T_ENABLE=y
# endif

ifneq ($(CONFIG_PACKAGE_kmod-qca-nss-drv-ovpn-link),)
ECM_MAKE_OPTS+=ECM_INTERFACE_OVPN_ENABLE=y
endif

ifneq ($(CONFIG_PACKAGE_kmod-qca-nss-drv-vxlanmgr),)
ECM_MAKE_OPTS+=ECM_INTERFACE_VXLAN_ENABLE=y
endif

ifneq ($(CONFIG_PACKAGE_kmod-qca-ovsmgr),)
ECM_MAKE_OPTS+=ECM_INTERFACE_OVS_BRIDGE_ENABLE=y \
		ECM_CLASSIFIER_OVS_ENABLE=y
EXTRA_CFLAGS+= -I$(STAGING_DIR)/usr/include/qca-ovsmgr
endif

ifneq ($(CONFIG_PACKAGE_kmod-qca-nss-drv-igs),)
ECM_MAKE_OPTS+=ECM_CLASSIFIER_DSCP_IGS=y
endif

ifneq ($(CONFIG_PACKAGE_kmod-emesh-sp),)
ECM_MAKE_OPTS+=ECM_CLASSIFIER_EMESH_ENABLE=y
EXTRA_CFLAGS+= -I$(STAGING_DIR)/usr/include/emesh-sp
endif

ifneq ($(CONFIG_PACKAGE_kmod-qca-nss-drv-mscs),)
ECM_MAKE_OPTS+=ECM_CLASSIFIER_MSCS_ENABLE=y
endif

ifneq ($(CONFIG_PACKAGE_kmod-macvlan),)
ECM_MAKE_OPTS+=ECM_INTERFACE_MACVLAN_ENABLE=y
endif

# Disable ECM IPv6 support when global IPv6 support is disabled.
ifneq ($(CONFIG_IPV6),)
ECM_MAKE_OPTS+=ECM_IPV6_ENABLE=y
endif

# Keeping default as ipq806x for branches that does not have subtarget framework
ifeq ($(CONFIG_TARGET_ipq),y)
subtarget:=$(SUBTARGET)
else
subtarget:=$(CONFIG_TARGET_BOARD)
endif

# Enable NSS frontend for all the platforms except ipq40xx
ifeq ($(CONFIG_TARGET_ipq_ipq40xx)$(CONFIG_TARGET_ipq40xx),)
ifneq ($(BUILD_VARIANT), nonss)
ECM_MAKE_OPTS+=ECM_FRONT_END_NSS_ENABLE=y
endif
endif

define Build/InstallDev
	$(INSTALL_DIR) $(1)/usr/include/qca-nss-ecm
	$(CP) $(PKG_BUILD_DIR)/exports/* $(1)/usr/include/qca-nss-ecm
endef

define Build/Compile
	$(MAKE) -C "$(LINUX_DIR)" $(strip $(ECM_MAKE_OPTS)) \
		CROSS_COMPILE="$(TARGET_CROSS)" \
		ARCH="$(LINUX_KARCH)" \
		KBUILD_EXTRA_SYMBOLS="$(wildcard $(PKG_SYMVERS_DIR)/*.symvers)" \
		M="$(PKG_BUILD_DIR)" \
		EXTRA_CFLAGS="$(EXTRA_CFLAGS)" SoC="$(subtarget)" \
		EXAMPLES_BUILD_PCC="$(CONFIG_QCA_NSS_ECM_EXAMPLES_PCC)" \
		EXAMPLES_BUILD_MARK="$(CONFIG_QCA_NSS_ECM_EXAMPLES_MARK)" \
		EXAMPLES_BUILD_OVS="$(CONFIG_QCA_NSS_ECM_OVS)" \
		modules
endef

define KernelPackage/qca-nss-ecm-premium/config
menu "ECM Configuration"
	config QCA_NSS_ECM_EXAMPLES_PCC
		bool "Build PCC usage example"
		help
			Selecting this will build the PCC classifier usage example module.
		default n

	config QCA_NSS_ECM_EXAMPLES_MARK
		bool "Build Mark classifier usage example"
		help
			Selecting this will build the Mark classifier usage example module.
		default n

	config QCA_NSS_ECM_OVS
		bool "Build OVS classifier external module"
		help
			Selecting this will build the OVS classifier external module.
		default n
endmenu
endef

$(eval $(call KernelPackage,qca-nss-ecm-noload))
$(eval $(call KernelPackage,qca-nss-ecm-standard))
$(eval $(call KernelPackage,qca-nss-ecm-premium-noload))
$(eval $(call KernelPackage,qca-nss-ecm-premium))
$(eval $(call KernelPackage,qca-nss-ecm-nonss))
