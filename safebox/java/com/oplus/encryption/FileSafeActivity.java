/*
 * Handles the gallery's "open Private Safe" delegation: the OnePlus gallery launches
 * Intent(action="com.oplus.filemanager.FILE_SAFE").setPackage("com.oplus.encryption") to browse
 * the vault. The OEM FileManager FILE_SAFE screen is dropped, so this translucent activity opens
 * the crDroid Axion Sandbox app directly on its Vault tab (tab index 2) — where move-to-safe
 * imported the media — gated by the Sandbox's own auth. Same user, no cross-profile.
 */
package com.oplus.encryption;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.util.Log;
import android.widget.Toast;

public class FileSafeActivity extends Activity {
    private static final String TAG = SafeBoxNativeBackend.TAG;

    // Axion Sandbox NavigationBar tab indices: 0=Apps, 1=Notifications, 2=Vault.
    private static final int SANDBOX_TAB_VAULT = 2;
    private static final String EXTRA_OPEN_TAB = "com.android.axion.sandbox.extra.OPEN_TAB";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        try {
            Intent i = new Intent(Intent.ACTION_MAIN)
                    .setClassName(SafeBoxNativeBackend.SANDBOX_PKG,
                            SafeBoxNativeBackend.SANDBOX_PKG + ".MainActivity")
                    .putExtra(EXTRA_OPEN_TAB, SANDBOX_TAB_VAULT)
                    .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
            startActivity(i);
        } catch (Throwable t) {
            Log.w(TAG, "FILE_SAFE -> Sandbox open failed", t);
            Toast.makeText(this, "Private Safe (Sandbox) unavailable", Toast.LENGTH_LONG).show();
        }
        finish();
    }
}
