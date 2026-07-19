#!/usr/bin/env -S PYTHONPATH=../../../tools/extract-utils python3
#
# SPDX-FileCopyrightText: 2016 The CyanogenMod Project
# SPDX-FileCopyrightText: 2017-2024 The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

from extract_utils.fixups_lib import (
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
    blob_fixup_inject_compat_uses_library,
)
from apk_fixups_camera_op15 import blob_fixup_opluscamera_component_safe_permission
from apk_fixups_gallery_op15 import (
    blob_fixup_oppogallery_strip_component_safe,
    blob_fixup_oppogallery_strip_search_indexables,
    blob_fixup_oppogallery_wallpaper_attach_intent,
)
from aps_heif_fixup import patch_apsclient_heif_selector_file


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


def blob_fixup_apsclient_force_java_heif(ctx, file, file_path, *args, **kwargs):
    # OPlus supports two HEIF handoffs: optional native helpers when dlopen can
    # resolve them, otherwise its Java-reflection fallback. Stock keeps this APS
    # client in /product and the helpers in /system_ext, so product namespace
    # isolation selects reflection. Our system_ext remap co-located them and
    # unintentionally enabled the native route that stock CPH2747 does not use.
    patch_apsclient_heif_selector_file(file_path)


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
}

blob_fixups = {
    'system_ext/lib64/libAPSClient-cmd-jni.so': blob_fixup()
        .call(blob_fixup_apsclient_force_java_heif),
    'system_ext/framework/com.oplus.camera.unit.sdk.jar': blob_fixup()
        .apktool_unpack('patches-sdk')
        .patch_dir('patches-sdk')
        .call(blob_fixup_sdk_facebeauty)
        .apktool_pack()
        .stripzip(),
    # OplusCamera.apk crash-on-open fixes (re-authored to be
    # signature-anchored, verified against the apk bytecode): font-NPE neuter +
    # strip undefined OEM permission gates. apktool unpack -> edit smali/manifest -> repack.
    'system_ext/priv-app/OplusCamera/OplusCamera.apk': blob_fixup()
        .call(blob_fixup_opluscamera_unpack)
        .call(blob_fixup_opluscamera_component_safe_permission)
        .call(blob_fixup_opluscamera_font)
        .call(blob_fixup_opluscamera_strip_oem_perms)
        .call(blob_fixup_inject_compat_uses_library)
        .apktool_pack()
        .stripzip(),
    'system_ext/priv-app/OppoGallery2/OppoGallery2.apk': blob_fixup()
        .call(blob_fixup_apktool_unpack_full)
        .call(blob_fixup_oppogallery_wallpaper_attach_intent)
        .call(blob_fixup_oppogallery_strip_component_safe)
        .call(blob_fixup_oppogallery_strip_search_indexables)
        .call(blob_fixup_inject_compat_uses_library)
        .apktool_pack()
        .stripzip(),
    'system_ext/etc/permissions/vendor-oplus-hardware-cryptoeng.xml': blob_fixup()
        .call(blob_fixup_cryptoeng_permissions_xml),
    'odm/etc/permissions/vendor-oplus-hardware-cryptoeng.xml': blob_fixup()
        .call(blob_fixup_cryptoeng_permissions_xml),
    'odm/etc/vintf/manifest/manifest_oplus_cryptoeng.xml': blob_fixup()
        .call(blob_fixup_cryptoeng_manifest),
}  # fmt: skip

namespace_imports = [
    'vendor/oneplus/camera-sm8850-common/camera',
    'vendor/oneplus/infiniti',
    'vendor/oneplus/sm8850-common',
    'hardware/oplus',
]

module = ExtractUtilsModule(
    'camera',
    'oneplus/camera-sm8850-common',
    device_rel_path='vendor/oneplus/camera-sm8850-common',
    blob_fixups=blob_fixups,
    lib_fixups=lib_fixups,
    namespace_imports=namespace_imports,
)

def inject_optional_uses_lib_android_bp(bp_path, module_names, lib='com.oplus.compat'):
    # extract-utils has no uses_libs support, so post-process the generated
    # Android.bp: insert optional_uses_libs on the rebaked OEM android_app_import
    # blocks that now declare the com.oplus.compat <uses-library> (paired with
    # blob_fixup_inject_compat_uses_library, gated by soong's uses-library check).
    # Brace-aware + idempotent, so every regen re-applies it cleanly.
    text = bp_path.read_text(encoding='utf-8')
    insert = f'    optional_uses_libs: ["{lib}"],\n'
    changed = False
    for name in module_names:
        pos = 0
        while True:
            start = text.find('android_app_import {', pos)
            if start == -1:
                break
            depth = 0
            end = None
            idx = text.find('{', start)
            while idx < len(text):
                char = text[idx]
                if char == '{':
                    depth += 1
                elif char == '}':
                    depth -= 1
                    if depth == 0:
                        end = idx
                        break
                idx += 1
            if end is None:
                break
            block = text[start:end + 1]
            if re.search(r'\bname:\s*"' + re.escape(name) + r'"', block):
                if 'optional_uses_libs' not in block:
                    text = text[:end] + insert + text[end:]
                    changed = True
                break
            pos = end + 1
    if changed:
        bp_path.write_text(text, encoding='utf-8')
    return changed


if __name__ == '__main__':
    utils = ExtractUtils.device(module)
    utils.run()
    inject_optional_uses_lib_android_bp(
        Path(__file__).resolve().parent / 'camera' / 'Android.bp',
        ('OplusCamera', 'OppoGallery2'),
    )
