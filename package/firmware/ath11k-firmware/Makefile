include $(TOPDIR)/rules.mk

PKG_NAME:=ath11k-firmware
PKG_VERSION:=2.6.0.1
PKG_RELEASE:=00974

PKG_SOURCE_PROTO:=git
PKG_SOURCE_URL:=https://github.com/quic/upstream-wifi-fw
PKG_SOURCE_VERSION:=main

include $(INCLUDE_DIR)/package.mk

define generate-ath11k-firmware

  define Package/$(PKG_NAME)-$(1)
    SECTION:=firmware
    CATEGORY:=Firmware
    TITLE:=ath11k firmware binaries for $(2)
  endef

  define Package/$(PKG_NAME)-$(1)/description
    ath11k firmware binaries for $(1)
  endef

  define Package/$(PKG_NAME)-$(1)/install
	$$(INSTALL_DIR) $$(1)/lib/firmware/$(3)
	$$(INSTALL_DATA) \
		$$(PKG_BUILD_DIR)/ath11k-firmware/*$(2)*/hw*.0/$(PKG_VERSION)/WLAN.HK.$(PKG_VERSION)-$(PKG_RELEASE)-QCAHKSWPL_SILICONZ-1/$(4)*.* \
		$$(1)/lib/firmware/$(3)/
  endef

  ALL_PACKAGE+=$(PKG_NAME)-$(1)

endef

$(eval $(call generate-ath11k-firmware,ipq5018,IPQ5018,IPQ5018))
$(eval $(call generate-ath11k-firmware,ipq6018,IPQ6018,IPQ6018))
$(eval $(call generate-ath11k-firmware,ipq8074,IPQ8074,IPQ8074))
$(eval $(call generate-ath11k-firmware,qcn6122,QCN6122,qcn6122,qcn6122/))
$(eval $(call generate-ath11k-firmware,qcn9074,QCN9074,qcn9074))

define Build/Compile
endef

$(foreach pkg, $(ALL_PACKAGE), \
	$(eval $(call BuildPackage,$(pkg))) \
)
