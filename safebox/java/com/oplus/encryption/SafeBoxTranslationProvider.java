/*
 * Thin lifecycle provider for authority com.oplus.encyptionserver.
 * The OnePlus gallery invokes exactly one op on it: call("update_background_status","true"|"false")
 * when it goes to/from background (result ignored). Everything vault-related goes through the bound
 * EncyptionService instead. query() on /file and /file_exit returns an empty cursor (the gallery
 * does not read the provider; present only for fidelity/robustness).
 */
package com.oplus.encryption;

import android.content.ContentProvider;
import android.content.ContentValues;
import android.content.UriMatcher;
import android.database.Cursor;
import android.database.MatrixCursor;
import android.net.Uri;
import android.os.Bundle;
import android.util.Log;

public class SafeBoxTranslationProvider extends ContentProvider {
    private static final String AUTHORITY = "com.oplus.encyptionserver";
    private static final UriMatcher MATCHER = new UriMatcher(UriMatcher.NO_MATCH);
    static {
        MATCHER.addURI(AUTHORITY, "file", 1);
        MATCHER.addURI(AUTHORITY, "file_exit", 6);
    }

    @Override
    public boolean onCreate() {
        return true;
    }

    @Override
    public Bundle call(String method, String arg, Bundle extras) {
        if ("update_background_status".equals(method)) {
            // lifecycle hint only; nothing to do for the native-FBE translation.
            Log.d(SafeBoxNativeBackend.TAG, "update_background_status=" + arg);
            return null;
        }
        return super.call(method, arg, extras);
    }

    @Override
    public Cursor query(Uri uri, String[] projection, String selection, String[] selectionArgs,
            String sortOrder) {
        // Empty cursor; the gallery never reads vault contents from this provider.
        return new MatrixCursor(projection != null ? projection : new String[] {"_id"});
    }

    @Override
    public String getType(Uri uri) {
        return null;
    }

    @Override
    public Uri insert(Uri uri, ContentValues values) {
        return null;
    }

    @Override
    public int delete(Uri uri, String selection, String[] selectionArgs) {
        return 0;
    }

    @Override
    public int update(Uri uri, ContentValues values, String selection, String[] selectionArgs) {
        return 0;
    }
}
