/*
 * SafeBox translation backend — proxies the OEM "Private Safe" vault onto the crDroid Axion
 * Sandbox's encrypted file vault (com.android.axion.sandbox).
 *
 * Move-in resolves the gallery's source (raw path or content:// uri) to a MediaStore content Uri
 * and hands it to the Sandbox VaultFileProvider's importFile() call. The Sandbox (which holds
 * MANAGE_EXTERNAL_STORAGE) reads it, AES-GCM-encrypts it into its vault dir, records it in the
 * vault DB, and deletes the original. The vault key auto-creates (not auth-bound), so import
 * works even while the Sandbox UI is locked. Browsing the vaulted media happens in the Sandbox
 * app's Vault tab, gated by the Sandbox's own auth.
 *
 * Runs in userId 0 (the vault service's own process); same-user, no cross-profile.
 */
package com.oplus.encryption;

import android.content.ContentResolver;
import android.content.ContentUris;
import android.content.Context;
import android.database.Cursor;
import android.net.Uri;
import android.os.Bundle;
import android.provider.MediaStore;
import android.text.TextUtils;
import android.util.Log;

import java.io.File;

class SafeBoxNativeBackend {
    static final String TAG = "SafeBoxShim";

    /** The Axion Sandbox app + its exported vault provider + import contract. */
    static final String SANDBOX_PKG = "com.android.axion.sandbox";
    private static final Uri VAULT_AUTHORITY =
            Uri.parse("content://com.android.axion.sandbox.vault");
    private static final String METHOD_IMPORT_FILE = "importFile";
    private static final String METHOD_IS_CONFIGURED = "isConfigured";
    private static final String KEY_RESULT = "result";

    private final Context mContext;

    SafeBoxNativeBackend(Context context) {
        mContext = context;
    }

    /** Vault is usable iff the Axion Sandbox provider answers (isConfigurationComplete). */
    boolean isVaultAvailable() {
        try {
            Bundle res = mContext.getContentResolver()
                    .call(VAULT_AUTHORITY, METHOD_IS_CONFIGURED, null, null);
            return res != null && res.getBoolean(KEY_RESULT, false);
        } catch (Throwable t) {
            Log.w(TAG, "isVaultAvailable: Sandbox provider unreachable", t);
            return false;
        }
    }

    /**
     * Move one item into the Sandbox vault. Returns true on success.
     * @param source a raw filesystem path or a content:// uri in userId 0.
     */
    boolean importOne(String source) {
        Uri uri = resolveToUri(source);
        if (uri == null) {
            Log.w(TAG, "importOne: could not resolve source " + source);
            return false;
        }
        try {
            Bundle res = mContext.getContentResolver()
                    .call(VAULT_AUTHORITY, METHOD_IMPORT_FILE, uri.toString(), null);
            boolean ok = res != null && res.getBoolean(KEY_RESULT, false);
            if (!ok) Log.w(TAG, "importOne: Sandbox import returned false for " + uri);
            return ok;
        } catch (Throwable t) {
            Log.w(TAG, "importOne: Sandbox import failed for " + uri, t);
            return false;
        }
    }

    /**
     * Resolve the gallery's source to a content Uri the Sandbox can read via
     * ContentResolver.openInputStream + delete via its _data path. Prefer MediaStore (gives the
     * Sandbox a correct display name / size / _data path); fall back to file:// for un-indexed
     * paths.
     */
    private Uri resolveToUri(String source) {
        if (TextUtils.isEmpty(source)) return null;
        if (source.startsWith("content://")) return Uri.parse(source);
        String path = source.startsWith("file://") ? Uri.parse(source).getPath() : source;
        if (TextUtils.isEmpty(path)) return null;
        Uri media = mediaUriForPath(mContext.getContentResolver(), path);
        if (media != null) return media;
        return Uri.fromFile(new File(path));
    }

    /** Resolve a raw filesystem path to its MediaStore content Uri (null if not indexed). */
    private static Uri mediaUriForPath(ContentResolver res, String path) {
        Uri files = MediaStore.Files.getContentUri(MediaStore.VOLUME_EXTERNAL);
        String[] proj = { MediaStore.MediaColumns._ID };
        try (Cursor c = res.query(files, proj, MediaStore.MediaColumns.DATA + "=?",
                new String[] { path }, null)) {
            if (c != null && c.moveToFirst()) {
                return ContentUris.withAppendedId(files, c.getLong(0));
            }
        } catch (Throwable t) {
            Log.w(TAG, "mediaUriForPath failed for " + path, t);
        }
        return null;
    }
}
