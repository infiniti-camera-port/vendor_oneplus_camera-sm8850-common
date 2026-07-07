# Blob dependencies
PRODUCT_PACKAGES += \
    android.hardware.graphics.common-V3-ndk.vendor

# Framework
# PRODUCT_BOOT_JARS += \
#    oplus-framework

# Init
#PRODUCT_PACKAGES += \
#    init.oplus.camera.rc

# Permissions
PRODUCT_COPY_FILES += \
    $(LOCAL_PATH)/configs/permissions/oplus_google_lens_config.xml:$(TARGET_COPY_OUT_SYSTEM_EXT)/etc/permissions/oplus_google_lens_config.xml \
    $(LOCAL_PATH)/configs/permissions/privapp-permissions-oplus.xml:$(TARGET_COPY_OUT_SYSTEM_EXT)/etc/permissions/privapp-permissions-oplus.xml \
    $(LOCAL_PATH)/configs/sysconfig/hiddenapi-package-oplus-whitelist.xml:$(TARGET_COPY_OUT_SYSTEM)/etc/sysconfig/hiddenapi-package-oplus-whitelist.xml

# Properties
PRODUCT_PRODUCT_PROPERTIES += \
    persist.vendor.camera.privapp.list=com.oplus.camera \
    persist.sys.feature.dolby_vision=1 \
    persist.sys.feature.dolby_vision_app=1 \
    persist.sys.feature.hdr_vision_app=1 \
    persist.sys.feature.localhdr_version=2 \
    persist.sys.feature.support.edrlistener=true \
    persist.sys.feature.uhdr.support=true \
    persist.sys.camera.private.log.enable=debug,pre,mp \
    ro.build.version.module.sub_api=2 \
    ro.build.version.oplus.api=38 \
    ro.build.version.oplus.sub_api=47 \
    ro.build.version.oplusrom=V16.1.0 \
    ro.build.version.oplusrom.confidential=V16.1.0 \
    ro.build.version.oplusrom.display=16.0.8 \
    ro.com.google.lens.oem_camera_package=com.oplus.camera \
    ro.com.google.lens.oem_image_package=com.oneplus.gallery,com.oplus.screenshot \
    ro.oplus.fusionlight=true \
    ro.oplus.camera.defercap.support=1 \
    ro.oplus.system.gallery.name=com.oneplus.gallery \
    ro.oplus.system.camera.name=com.oplus.camera \
    ro.oplus.camera.defercap.all.quick.visible.support=1 \
    ro.vendor.oplus.hdr.uniform=1 \
    ro.vendor.oplus.vendorxml.enable=1 \
    vendor.oplus.hdr.uniform.debug=1 \
    oplus.software.camera.10bit=1 \
    vendor.camera.aux.packagelist=com.oplus.camera \
    ro.oplus.camera.facing.front.need.disable.nfc=1 \
    ro.oplus.camera.portrait.center.switch=oplus.switch.portrait.center \
    ro.oplus.camera.portrait_center.prefix=oplus.portrait.center. \
    ro.oplus.camera.video.beauty.switch=oplus.switch.video.beauty \
    ro.oplus.camera.video_beauty.prefix=oplus.video.beauty. \
    ro.oplus.camera.speechassist=true \
    ro.oplus.system.camera.flashlight=com.oplus.motor.flashlight \
    ro.camera.privileged.3rdpartyApp=com.mediatek.expert.mtkcamhelper;com.aiunit.aon; \
    persist.logd.log.load.camerahalserver.lower_limit=1000 \
    persist.logd.log.load.camerahalserver.threshold=800000 \
    persist.logd.log.load.camerahalserver.upper_limit=3000 \
    persist.logd.log.load.com.oplus.camera.lower_limit=1000 \
    persist.logd.log.load.com.oplus.camera.threshold=800000 \
    persist.logd.log.load.com.oplus.camera.upper_limit=3000 \
    persist.logd.log.load.vendor.qti.camera.provider-service_64.lower_limit=500 \
    persist.logd.log.load.vendor.qti.camera.provider-service_64.threshold=400000 \
    persist.logd.log.load.vendor.qti.camera.provider-service_64.upper_limit=1500 \

# Photo
$(call soong_config_set,camera,package_name,com.oplus.packageName)
$(call soong_config_set,camera,allow_nonincreasing_timestamps,true)

# Video
$(call soong_config_set_bool,camera,override_format_from_reserved,true)

# SEpolicy
include vendor/oneplus/camera-sm8850-common/sepolicy/SEPolicy.mk

# Inherit from camera-vendor.mk
$(call inherit-product, vendor/oneplus/camera-sm8850-common/camera/camera-vendor.mk)

# SoC-common camera props (order-only across the sm8850 family; absorbed from the
# task-8 device/oneplus/sm8850-common-camera scaffold that rearchv2 supersedes).
PRODUCT_VENDOR_PROPERTIES += \
    ro.camera.enableCamera1MaxZsl=1 \
    ro.camera.notify_nfc=1 \
    ro.camerax.extensions.enabled=true
