from __future__ import annotations

from pathlib import Path


class CameraFixupError(RuntimeError):
    pass


def _manifest(tmp_dir: str) -> Path:
    return Path(tmp_dir) / 'AndroidManifest.xml'


def _add_permissions(tmp_dir: str, permissions: tuple[str, ...]) -> None:
    manifest = _manifest(tmp_dir)
    data = manifest.read_text(encoding='utf-8') if manifest.exists() else ''
    entries = ''.join(
        f'    <uses-permission android:name="{permission}"/>\n'
        for permission in permissions
        if permission not in data
    )
    if entries:
        manifest.write_text(data.replace('<application ', entries + '    <application ', 1), encoding='utf-8')


def blob_fixup_opluscamera_component_safe_permission(ctx, file, file_path, *args, tmp_dir=None, **kwargs):
    if tmp_dir is not None:
        _add_permissions(tmp_dir, ('oppo.permission.OPPO_COMPONENT_SAFE',))


def blob_fixup_opluscamera_heic_quick_flag(ctx, file, file_path, *args, tmp_dir=None, **kwargs):
    if tmp_dir is None:
        return

    matches = list(Path(tmp_dir).glob('smali*/xj/k.smali'))
    if len(matches) != 1:
        raise CameraFixupError('OplusCamera HEIC quick-flag class not found exactly once')

    smali = matches[0]
    data = smali.read_text(encoding='utf-8')
    signature = '.method public static d(Lnc/h1;Ljava/util/Map;Ljava/lang/String;Ljava/io/File;)V'
    start = data.find(signature)
    end = data.find('.end method', start)
    if start < 0 or end < 0:
        raise CameraFixupError('OplusCamera HEIC quick-flag method not found')

    method = data[start:end]
    replacements = (
        (
            'invoke-static {v5}, Ljava/lang/Integer;->parseInt(Ljava/lang/String;)I',
            'invoke-static {v5}, Ljava/lang/Long;->parseLong(Ljava/lang/String;)J',
        ),
        ('move-result v5\n    :try_end_', 'move-result-wide v5\n    :try_end_'),
        ('const v7, -0x10000001', 'const-wide/32 v7, -0x10000001'),
        ('and-int/2addr v5, v7', 'and-long/2addr v5, v7'),
        (
            'invoke-virtual {v7, v5}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;',
            'invoke-virtual {v7, v5, v6}, Ljava/lang/StringBuilder;->append(J)Ljava/lang/StringBuilder;',
        ),
    )
    for old, new in replacements:
        if method.count(old) != 1:
            raise CameraFixupError(f'OplusCamera HEIC quick-flag patch point mismatch: {old}')
        method = method.replace(old, new, 1)

    smali.write_text(data[:start] + method + data[end:], encoding='utf-8')


# AOSP Settings category that lands a MANUFACTURER tile under
# Security & privacy > More security and privacy (SafetyCenter merges the
# advanced-security category into it; without SafetyCenter it shows under
# "More security settings"). Used to re-home the two OEM tiles that ship with a
# missing/misspelled category and otherwise leak onto every Settings subpage.
_SETTINGS_CATEGORY_META = (
    '<meta-data android:name="com.android.settings.category" '
    'android:value="com.android.settings.category.ia.advanced_security"/>'
)


def blob_fixup_aonservice_settings_category(ctx, file, file_path, *args, tmp_dir=None, **kwargs):
    # AONService's "EZ Pay" tile (IntelligentPerceptionActivity) declares a
    # MANUFACTURER_APPLICATION_SETTING tile but NO com.android.settings.category,
    # so AOSP TileUtils files it under a null category that renders on every
    # unregistered Settings subpage (Reset options, etc.). Inject the AOSP
    # advanced-security category next to its (unique) title meta-data.
    if tmp_dir is None:
        return
    manifest = _manifest(tmp_dir)
    if not manifest.exists():
        return
    data = manifest.read_text(encoding='utf-8')
    if _SETTINGS_CATEGORY_META in data:
        return
    anchor = (
        '<meta-data android:name="com.android.settings.title" '
        'android:resource="@string/intelligent_perception_title_new"/>'
    )
    if anchor not in data:
        raise ValueError('AONService settings-tile title anchor not found')
    manifest.write_text(
        data.replace(anchor, anchor + '\n            ' + _SETTINGS_CATEGORY_META, 1),
        encoding='utf-8',
    )


def blob_fixup_aiunit_settings_category(ctx, file, file_path, *args, tmp_dir=None, **kwargs):
    # AIUnit's "AI Service Engine" tile (ExpAIStrengthenActivity) uses the
    # misspelled key com.android.settings.category.export with an Oplus-only
    # value, which AOSP never reads, so the tile leaks onto every unregistered
    # Settings subpage. Rewrite it to the proper com.android.settings.category
    # key with the AOSP advanced-security value.
    if tmp_dir is None:
        return
    manifest = _manifest(tmp_dir)
    if not manifest.exists():
        return
    data = manifest.read_text(encoding='utf-8')
    if _SETTINGS_CATEGORY_META in data:
        return
    old = (
        '<meta-data android:name="com.android.settings.category.export" '
        'android:value="com.oplus.settings.category.ia.strengthen_service"/>'
    )
    if old not in data:
        raise ValueError('AIUnit settings-tile category.export anchor not found')
    manifest.write_text(data.replace(old, _SETTINGS_CATEGORY_META, 1), encoding='utf-8')
