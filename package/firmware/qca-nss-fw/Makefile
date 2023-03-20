include $(TOPDIR)/rules.mk

PKG_NAME:=qca-nss-fw
PKG_VERSION:=12.0.r1
PKG_RELEASE:=002

include $(INCLUDE_DIR)/package.mk

define generate-qca-nss-fw

  define Package/$(PKG_NAME)-$(1)-$(3)
    SECTION:=firmware
    CATEGORY:=Firmware
    TITLE:=NSS firmware binaries for $(1) - $(3)
    DEPENDS:=@TARGET_$(1)
    CONFLICTS:=$($(PKG_NAME)_PREV_$(1))
  endef

  define Package/$(PKG_NAME)-$(1)-$(3)/description
    NSS firmware binaries for $(1) - $(3)
  endef

  define Download/$(PKG_NAME)-$(1)-$(3)
    URL:=http://qcawebsrvr.qualcomm.com/NSS/NSS.FW/$(PKG_VERSION)/$(2)/$(PKG_RELEASE)/
    URL_FILE:=BIN-NSS.FW.$(PKG_VERSION)-$(PKG_RELEASE)-$(2).$(4).tar.bz2
    FILE:=BIN-NSS.FW.$(PKG_VERSION)-$(PKG_RELEASE)-$(2).$(4).tar.bz2
    HASH:=$(6)
  endef
  $$(if $$(CONFIG_PACKAGE_$(PKG_NAME)-$(1)-$(3)), \
    $$(eval $$(call Download,$(PKG_NAME)-$(1)-$(3))) \
  )

  define Prepare/$(PKG_NAME)-$(1)-$(3)
	bzcat $$(DL_DIR)/BIN-NSS.FW.$(PKG_VERSION)-$(PKG_RELEASE)-$(2).$(4).tar.bz2 \
		| $$(HOST_TAR) -C $$(PKG_BUILD_DIR) $$(TAR_OPTIONS)
  endef

  define Package/$(PKG_NAME)-$(1)-$(3)/install
	$$(INSTALL_DIR) $$(1)/lib/firmware/
	$$(INSTALL_DATA) \
		$$(PKG_BUILD_DIR)/BIN-NSS.FW.$(PKG_VERSION)-$(PKG_RELEASE)-$(2).$(4)/$(5)0.bin \
		$$(1)/lib/firmware/qca-nss0-$(3).bin
	-$$(INSTALL_DATA) \
		$$(PKG_BUILD_DIR)/BIN-NSS.FW.$(PKG_VERSION)-$(PKG_RELEASE)-$(2).$(4)/$(5)1.bin \
		$$(1)/lib/firmware/qca-nss1-$(3).bin
  endef

  $(PKG_NAME)_PREV_$(_SOC)+=$(PKG_NAME)-$(1)-$(3)
  ALL_PACKAGE+=$(PKG_NAME)-$(1)-$(3)

endef

# $(eval $(call generate-qca-nss-fw,ipq50xx,MP,enterprise,E,enterprise_ap,))
$(eval $(call generate-qca-nss-fw,ipq50xx,MP,retail,R,retail_router,ea41c576d4d18758880acc8db22d1cc721e6e294045ddf47a6bb86633309148f))
# $(eval $(call generate-qca-nss-fw,ipq60xx,CP,enterprise,E,enterprise_ap,))
$(eval $(call generate-qca-nss-fw,ipq60xx,CP,retail,R,retail_router,f92d840a9d14d9893eca462e9e29f5ae3b44de7b3faf01daf40eb018d93eed75))
# $(eval $(call generate-qca-nss-fw,ipq806x,AK,enterprise,E,enterprise_ap,))
# $(eval $(call generate-qca-nss-fw,ipq806x,AK,retail,R,retail_router,))
# $(eval $(call generate-qca-nss-fw,ipq807x,HK,enterprise,E,enterprise_ap,))
$(eval $(call generate-qca-nss-fw,ipq807x,HK,retail,R,retail_router,832c895835c9bb4259c238dc01ad872a853838863632801d55cb13267d296ea2))

define Build/Prepare
	$(foreach pkg, $(ALL_PACKAGE),
		$(if $(CONFIG_PACKAGE_$(pkg)),
			$(call Prepare/$(pkg))
		)
	)
endef

define Build/Compile
endef

$(foreach pkg, $(ALL_PACKAGE), \
	$(eval $(call BuildPackage,$(pkg))) \
)
