#!/usr/bin/env -S PYTHONPATH=../../../tools/extract-utils python3
#
# SPDX-FileCopyrightText: 2016 The CyanogenMod Project
# SPDX-FileCopyrightText: 2017-2024 The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

from extract_utils.fixups_lib import (
    lib_fixup_remove,
    lib_fixups,
    lib_fixups_user_type,
)
from extract_utils.fixups_blob import (
    apktool_path,
    blob_fixup,
    blob_fixups_user_type,
    java_path,
)
from extract_utils.main import (
    ExtractUtils,
    ExtractUtilsModule,
)
from extract_utils.utils import run_cmd
from pathlib import Path
import glob
import re

from apk_fixups_op15 import (
    blob_fixup_apktool_unpack_full,
    blob_fixup_cryptoeng_manifest,
    blob_fixup_cryptoeng_permissions_xml,
)
from apk_fixups_camera_op15 import (
    blob_fixup_aiunit_settings_category,
    blob_fixup_aonservice_settings_category,
    blob_fixup_opluscamera_component_safe_permission,
    blob_fixup_opluscamera_heic_quick_flag,
)
from apk_fixups_gallery_op15 import (
    blob_fixup_oppogallery_wallpaper_attach_intent,
)


def lib_fixup_system_ext_suffix(lib: str, partition: str, *args, **kwargs):
    """
    Mirrors lib_to_package_fixup_system_ext_variants from the old setup-makefiles.sh.
    These libs exist as system_ext variants and need a _system_ext suffix
    when pulled from that partition.
    """
    if partition != 'system_ext':
        return None

    system_ext_libs = {
        'libSuperTextWrapper',
        'libXDocProcessSDK',
        'libYTCommon',
        'libmpbase',
        'libextendfile',
    }

    return f'{lib}_system_ext' if lib in system_ext_libs else None


def _replace_smali_method(data: str, signature: str, body: str) -> str:
    # Replace a smali method body by its signature, independent of the (R8-obfuscated,
    # build-drifting) class path. The signature is the stable anchor.
    return re.sub(
        rf'(?ms)^\.method {re.escape(signature)}\n.*?^\.end method',
        f'.method {signature}\n{body}.end method',
        data,
    )


def blob_fixup_opluscamera_unpack(ctx, file, file_path, *args, tmp_dir=None, **kwargs):
    if tmp_dir is None:
        return
    run_cmd([java_path, '-Xmx8g', '-jar', apktool_path, 'd', file_path, '-o', tmp_dir, '-f'])


def blob_fixup_apk_unpack_nosmali(ctx, file, file_path, *args, tmp_dir=None, **kwargs):
    # Resource+manifest decode only (-s keeps the original classes.dex), so large
    # apks (AIUnit) are byte-preserved apart from a manifest edit — no smali
    # roundtrip. apktool_pack() reads apktool.yml and rebuilds with the kept dex.
    if tmp_dir is None:
        return
    run_cmd([java_path, '-Xmx8g', '-jar', apktool_path, 'd', '-s', file_path, '-o', tmp_dir, '-f'])


def blob_fixup_opluscamera_font(ctx, file, file_path, *args, tmp_dir=None, **kwargs):
    # OEM camera font-NPE neutralizer, re-anchored for infiniti: the
    # TypeFaceUtil static a(Context)->Typeface reads OplusBaseConfiguration.
    # mOplusExtraConfiguration.mFontVariationSettings; with the OEM font framework absent that
    # path crashes -> camera force-finishes on open. Return Typeface.DEFAULT to skip it.
    # Anchored on the "TypeFaceUtil" log tag + the method signature (class path drifts
    # between builds), so it stays correct across rebuilds.
    if tmp_dir is None:
        return
    signature = 'public static a(Landroid/content/Context;)Landroid/graphics/Typeface;'
    body = (
        '    .locals 1\n'
        '\n'
        '    sget-object v0, Landroid/graphics/Typeface;->DEFAULT:Landroid/graphics/Typeface;\n'
        '\n'
        '    return-object v0\n'
    )
    for smali in glob.glob(str(Path(tmp_dir) / 'smali*/**/*.smali'), recursive=True):
        try:
            data = open(smali, encoding='utf-8', errors='ignore').read()
        except OSError:
            continue
        if '"TypeFaceUtil"' in data and f'.method {signature}' in data:
            fixed = _replace_smali_method(data, signature, body)
            if fixed != data:
                open(smali, 'w', encoding='utf-8').write(fixed)
            return


def blob_fixup_opluscamera_strip_oem_perms(ctx, file, file_path, *args, tmp_dir=None, **kwargs):
    # Strip the android:permission="<oem>" gate attribute from
    # component declarations (oplus/oppo/heytap perms are undefined on LineageOS, so a gated
    # activity/service/receiver/provider fails to register -> crash-on-open). Components are
    # kept; only the gate attribute is removed. Anchored on the perm-value namespace.
    if tmp_dir is None:
        return
    manifest = Path(tmp_dir) / 'AndroidManifest.xml'
    if not manifest.exists():
        return
    data = manifest.read_text(encoding='utf-8')
    fixed = re.sub(
        r'\s+android:permission="(?:oplus|oppo|com\.oplus|com\.oppo|com\.heytap)[^"]*"',
        '',
        data,
    )
    if fixed != data:
        manifest.write_text(fixed, encoding='utf-8')


def blob_fixup_sdk_facebeauty(ctx, file, file_path, *args, tmp_dir=None, **kwargs):
    # Re-point the guarded ProductJni probe from /product/lib64 to /system_ext/lib64.
    # On LineageOS the lib ships at system_ext (my_product->system_ext remap), so the
    # /product probe fails -> unguarded fallback -> zero FaceBeautyParams -> SIGSEGV.
    # Anchored on the globally unique lib-path string in OplusFaceBeautyPreview;
    # immune to R8/obfuscated class-path drift — no line-context dependency.
    if tmp_dir is None:
        return
    OLD = '/product/lib64/libApsFaceBeautyPreviewProductJni.so'
    NEW = '/system_ext/lib64/libApsFaceBeautyPreviewProductJni.so'
    for smali in glob.glob(str(Path(tmp_dir) / 'smali*/**/*.smali'), recursive=True):
        try:
            data = open(smali, encoding='utf-8', errors='ignore').read()
        except OSError:
            continue
        if OLD in data:
            open(smali, 'w', encoding='utf-8').write(data.replace(OLD, NEW))
            return


lib_fixups: lib_fixups_user_type = {
    # **lib_fixups already includes the clang RT ubsan and proto 3.9.1
    # fixups that were previously handled by the bash helper functions
    # lib_to_package_fixup_clang_rt_ubsan_standalone and
    # lib_to_package_fixup_proto_3_9_1 — no need to add them explicitly.
    **lib_fixups,
    (
        'libSuperTextWrapper',
        'libXDocProcessSDK',
        'libYTCommon',
        'libmpbase',
        'libextendfile',
    ): lib_fixup_system_ext_suffix,
    # DT_NEEDED OEM libs that are not packaged as their own soong modules (they
    # live in other vendor images we don't own). Drop them from the generated
    # shared_libs so the prebuilt modules don't reference undefined modules.
    # Without this, extract-files emits e.g. libskjpegencoderextimpl -> these,
    # and `m nothing` fails with "depends on undefined module".
    (
        'libatlasservice',
        'libimmlistservice',
        'liboplusHeifDecoderImpl',
        'liboplus_imageprocessing',
        'liboplusmmdebug',
    ): lib_fixup_remove,
    # libft2 (freetype) is a defined module but restricts its visibility, so a
    # prebuilt here cannot depend on it. The prebuilt .so resolves libft2 against
    # the platform copy at runtime, so drop it from the generated shared_libs.
    (
        'libft2',
    ): lib_fixup_remove,
}

blob_fixups = {
    'system_ext/framework/com.oplus.camera.unit.sdk.jar': blob_fixup()
        .apktool_unpack('patches-sdk')
        .patch_dir('patches-sdk')
        .call(blob_fixup_sdk_facebeauty)
        .apktool_pack()
        .stripzip(),
    'system_ext/framework/com.oplus.camera.unit.sdk.adapter.jar': blob_fixup()
        .call(blob_fixup_opluscamera_unpack)
        .call(blob_fixup_sdk_facebeauty)
        .apktool_pack()
        .stripzip(),
    # OplusCamera.apk crash-on-open fixes (re-authored to be
    # signature-anchored, verified against the apk bytecode): font-NPE neuter +
    # strip undefined OEM permission gates. apktool unpack -> edit smali/manifest -> repack.
    'system_ext/priv-app/OplusCamera/OplusCamera.apk': blob_fixup()
        .call(blob_fixup_opluscamera_unpack)
        .call(blob_fixup_opluscamera_component_safe_permission)
        .call(blob_fixup_opluscamera_heic_quick_flag)
        .call(blob_fixup_opluscamera_font)
        .call(blob_fixup_opluscamera_strip_oem_perms)
        .apktool_pack()
        .stripzip(),
    'system_ext/priv-app/OppoGallery2/OppoGallery2.apk': blob_fixup()
        .call(blob_fixup_apktool_unpack_full)
        .call(blob_fixup_oppogallery_wallpaper_attach_intent)
        .apktool_pack()
        .stripzip(),
    # AON "EZ Pay" + AIUnit "AI Service Engine" Settings tiles: fix the malformed
    # com.android.settings.category so they land under More security and privacy
    # instead of leaking onto every Settings subpage. Manifest-only edit (no smali
    # roundtrip); these apks are platform-resigned (see Android.bp) so the fixed
    # manifest is signed with the platform key and matches OplusPermissionDefiner.
    'product/app/AONService/AONService.apk': blob_fixup()
        .call(blob_fixup_apk_unpack_nosmali)
        .call(blob_fixup_aonservice_settings_category)
        .apktool_pack()
        .stripzip(),
    'product/priv-app/AIUnit/AIUnit.apk': blob_fixup()
        .call(blob_fixup_apk_unpack_nosmali)
        .call(blob_fixup_aiunit_settings_category)
        .apktool_pack()
        .stripzip(),
    'system_ext/etc/permissions/vendor-oplus-hardware-cryptoeng.xml': blob_fixup()
        .call(blob_fixup_cryptoeng_permissions_xml),
    'odm/etc/permissions/vendor-oplus-hardware-cryptoeng.xml': blob_fixup()
        .call(blob_fixup_cryptoeng_permissions_xml),
    'odm/etc/vintf/manifest/manifest_oplus_cryptoeng.xml': blob_fixup()
        .call(blob_fixup_cryptoeng_manifest),
    'odm/lib64/libAncHumanSegFigureFusion.so': blob_fixup()
        .clear_symbol_version('AHardwareBuffer_acquire')
        .clear_symbol_version('AHardwareBuffer_allocate')
        .clear_symbol_version('AHardwareBuffer_describe')
        .clear_symbol_version('AHardwareBuffer_lock')
        .clear_symbol_version('AHardwareBuffer_lockPlanes')
        .clear_symbol_version('AHardwareBuffer_release')
        .clear_symbol_version('AHardwareBuffer_unlock'),
}  # fmt: skip

namespace_imports = [
    'proprietary/vendor/oneplus/camera-sm8850-common',
    'vendor/oneplus/sm8850-common',
    'hardware/oplus',
]

module = ExtractUtilsModule(
    'camera-sm8850-common',
    'oneplus',
    device_rel_path='vendor/oneplus/camera-sm8850-common',
    blob_fixups=blob_fixups,
    lib_fixups=lib_fixups,
    namespace_imports=namespace_imports,
)
module.vendor_rel_path = 'proprietary/vendor/oneplus/camera-sm8850-common'
module.vendor_path = str(Path(__file__).resolve().parents[3] / module.vendor_rel_path)

if __name__ == '__main__':
    utils = ExtractUtils.device(module)
    utils.run()
