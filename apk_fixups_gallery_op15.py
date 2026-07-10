from __future__ import annotations

from pathlib import Path
import re


def blob_fixup_oppogallery_wallpaper_attach_intent(ctx, file, file_path, *args, tmp_dir=None, **kwargs):
    if tmp_dir is None:
        return
    replacement = (
        '.method public final a(Landroid/app/Activity;Landroid/net/Uri;)V\n'
        '    .locals 3\n'
        '\n'
        '    const-string p0, "activity"\n'
        '\n'
        '    invoke-static {p1, p0}, Lkotlin/jvm/internal/Intrinsics;->checkNotNullParameter(Ljava/lang/Object;Ljava/lang/String;)V\n'
        '\n'
        '    const-string p0, "pickedItem"\n'
        '\n'
        '    invoke-static {p2, p0}, Lkotlin/jvm/internal/Intrinsics;->checkNotNullParameter(Ljava/lang/Object;Ljava/lang/String;)V\n'
        '\n'
        '    new-instance v0, Landroid/content/Intent;\n'
        '\n'
        '    const-string v1, "android.intent.action.ATTACH_DATA"\n'
        '\n'
        '    invoke-direct {v0, v1}, Landroid/content/Intent;-><init>(Ljava/lang/String;)V\n'
        '\n'
        '    const-string v1, "image/*"\n'
        '\n'
        '    invoke-virtual {v0, p2, v1}, Landroid/content/Intent;->setDataAndType(Landroid/net/Uri;Ljava/lang/String;)Landroid/content/Intent;\n'
        '\n'
        '    const/4 v2, 0x1\n'
        '\n'
        '    invoke-virtual {v0, v2}, Landroid/content/Intent;->setFlags(I)Landroid/content/Intent;\n'
        '\n'
        '    const-string v2, "mimeType"\n'
        '\n'
        '    invoke-virtual {v0, v2, v1}, Landroid/content/Intent;->putExtra(Ljava/lang/String;Ljava/lang/String;)Landroid/content/Intent;\n'
        '\n'
        '    invoke-virtual {p1, v0}, Landroid/app/Activity;->startActivity(Landroid/content/Intent;)V\n'
        '\n'
        '    return-void\n'
        '.end method\n'
    )
    signature = 'public final a(Landroid/app/Activity;Landroid/net/Uri;)V'
    patched = False
    for smali in Path(tmp_dir).glob('smali*/com/oplus/gallery/pictureeditorpage/PictureEditorDM.smali'):
        data = smali.read_text(encoding='utf-8')
        fixed, count = re.subn(
            rf'(?ms)^\.method {re.escape(signature)}\n.*?^\.end method',
            replacement,
            data,
            count=1,
        )
        if count != 1:
            continue
        smali.write_text(fixed, encoding='utf-8')
        patched = True
        break
    if not patched:
        raise ValueError('OppoGallery2 wallpaper attach intent patch point not found')


def _replace_smali_method(data: str, signature: str, body: str) -> str:
    # Replace a smali method body by its signature, independent of the (R8-obfuscated,
    # build-drifting) class path. The signature is the stable anchor.
    return re.sub(
        rf'(?ms)^\.method {re.escape(signature)}\n.*?^\.end method',
        f'.method {signature}\n{body}.end method',
        data,
    )


def blob_fixup_oppogallery_system_share_helper(ctx, file, file_path, *args, tmp_dir=None, **kwargs):
    # Use Gallery's existing system-share branch instead of the OnePlus custom
    # share page. This preserves Gallery's own media path -> content URI/MIME
    # conversion (via GalleryFileProvider) before Android's platform chooser is
    # opened. The share helper lives in the AIUnit-vision share class (x7m); the
    # obfuscated class/method names are the same generation as our extracted apk
    # (verified against OppoGallery2 dex: com/oplus/aiunit/vision/{x7m,ci8,rfg,ymd,ipd}).
    if tmp_dir is None:
        return

    smali_matches = list(Path(tmp_dir).glob('smali*/com/oplus/aiunit/vision/x7m.smali'))
    if not smali_matches:
        raise ValueError('OppoGallery2 ShareHelper smali not found')
    smali = smali_matches[0]

    data = smali.read_text(encoding='utf-8', errors='ignore')
    old = (
        '    sget-object v2, Lcom/oplus/aiunit/vision/ci8;->m0:Lkotlin/Lazy;\n'
        '\n'
        '    .line 40\n'
        '    .line 41\n'
        '    invoke-interface {v2}, Lkotlin/Lazy;->getValue()Ljava/lang/Object;\n'
        '\n'
        '    .line 42\n'
        '    .line 43\n'
        '    .line 44\n'
        '    move-result-object v2\n'
        '\n'
        '    .line 45\n'
        '    check-cast v2, Ljava/lang/Boolean;\n'
        '\n'
        '    .line 46\n'
        '    .line 47\n'
        '    invoke-virtual {v2}, Ljava/lang/Boolean;->booleanValue()Z\n'
        '\n'
        '    .line 48\n'
        '    .line 49\n'
        '    .line 50\n'
        '    move-result v2\n'
        '\n'
        '    .line 51\n'
        '    const/4 v3, 0x0\n'
        '\n'
        '    .line 52\n'
        '    if-nez v2, :cond_2\n'
    )
    new = (
        '    const/4 v3, 0x0\n'
        '\n'
        '    goto :cond_2\n'
    )
    fixed = data.replace(old, new, 1)
    if fixed == data:
        raise ValueError('OppoGallery2 ShareHelper system-share patch point not found')

    uri_body = (
        '    .locals 5\n'
        '\n'
        '    const-string v0, "<this>"\n'
        '\n'
        '    invoke-static {p0, v0}, Lkotlin/jvm/internal/Intrinsics;->checkNotNullParameter(Ljava/lang/Object;Ljava/lang/String;)V\n'
        '\n'
        '    invoke-virtual {p0}, Lcom/oplus/aiunit/vision/rfg;->f()Lcom/oplus/gallery/business_lib/model/data/base/MediaObject;\n'
        '\n'
        '    move-result-object v0\n'
        '\n'
        '    instance-of v1, v0, Lcom/oplus/aiunit/vision/ymd;\n'
        '\n'
        '    if-eqz v1, :cond_fallback\n'
        '\n'
        '    check-cast v0, Lcom/oplus/aiunit/vision/ymd;\n'
        '\n'
        '    invoke-virtual {v0}, Lcom/oplus/aiunit/vision/ymd;->x()Ljava/lang/String;\n'
        '\n'
        '    move-result-object v0\n'
        '\n'
        '    if-eqz v0, :cond_fallback\n'
        '\n'
        '    invoke-virtual {v0}, Ljava/lang/String;->length()I\n'
        '\n'
        '    move-result v1\n'
        '\n'
        '    if-lez v1, :cond_fallback\n'
        '\n'
        '    sget-object v1, Lcom/oplus/aiunit/vision/s55;->a:Landroid/content/Context;\n'
        '\n'
        '    if-eqz v1, :cond_fallback\n'
        '\n'
        '    new-instance v2, Lcom/oplus/aiunit/vision/mj8;\n'
        '\n'
        '    invoke-direct {v2, v0}, Lcom/oplus/aiunit/vision/mj8;-><init>(Ljava/lang/String;)V\n'
        '\n'
        '    const/4 v0, 0x0\n'
        '\n'
        '    new-array v0, v0, [Ljava/lang/String;\n'
        '\n'
        '    invoke-static {v1, v2, v0}, Lcom/oplus/gallery/foundation/fileaccess/GalleryFileProvider$a;->e(Landroid/content/Context;Lcom/oplus/aiunit/vision/mj8;[Ljava/lang/String;)Landroid/net/Uri;\n'
        '\n'
        '    move-result-object v0\n'
        '\n'
        '    return-object v0\n'
        '\n'
        '    :cond_fallback\n'
        '    invoke-static {p0}, Lcom/oplus/aiunit/vision/rkp;->i(Lcom/oplus/aiunit/vision/rfg;)Z\n'
        '\n'
        '    move-result v0\n'
        '\n'
        '    const-string v1, "external_primary"\n'
        '\n'
        '    if-eqz v0, :cond_0\n'
        '\n'
        '    iget-object p0, p0, Lcom/oplus/aiunit/vision/rfg;->b:Ljava/lang/String;\n'
        '\n'
        '    const/4 v0, 0x1\n'
        '\n'
        '    invoke-static {v0, p0, v1}, Lcom/oplus/aiunit/vision/ipd;->i(ILjava/lang/String;Ljava/lang/String;)Landroid/net/Uri;\n'
        '\n'
        '    move-result-object p0\n'
        '\n'
        '    goto :goto_0\n'
        '\n'
        '    :cond_0\n'
        '    invoke-static {p0}, Lcom/oplus/aiunit/vision/rkp;->j(Lcom/oplus/aiunit/vision/rfg;)Z\n'
        '\n'
        '    move-result v0\n'
        '\n'
        '    if-eqz v0, :cond_1\n'
        '\n'
        '    iget-object p0, p0, Lcom/oplus/aiunit/vision/rfg;->b:Ljava/lang/String;\n'
        '\n'
        '    const/4 v0, 0x3\n'
        '\n'
        '    invoke-static {v0, p0, v1}, Lcom/oplus/aiunit/vision/ipd;->i(ILjava/lang/String;Ljava/lang/String;)Landroid/net/Uri;\n'
        '\n'
        '    move-result-object p0\n'
        '\n'
        '    goto :goto_0\n'
        '\n'
        '    :cond_1\n'
        '    const/4 p0, 0x0\n'
        '\n'
        '    :goto_0\n'
        '    return-object p0\n'
    )
    before_uri = fixed
    fixed = _replace_smali_method(
        fixed,
        'public static b(Lcom/oplus/aiunit/vision/rfg;)Landroid/net/Uri;',
        uri_body,
    )
    if fixed == before_uri:
        raise ValueError('OppoGallery2 ShareHelper URI patch point not found')
    smali.write_text(fixed, encoding='utf-8')
