#
# Copyright (C) 2026 The LineageOS Project
#
# SPDX-License-Identifier: Apache-2.0
#

# OEM signature-permission definer (rearchv2 O3 §4). Inherited from
# camera-sm8850-common.mk. Defines the oplus/oppo signature perms whose OOS
# definer (oplus-framework-res.apk) is not shipped; replaces the interim
# frameworks/base d7de0fcf core-manifest defs.
PRODUCT_PACKAGES += OplusPermissionDefiner
