/*
 * SafeBox / Private-Safe translation service.
 *
 * Reimplements the dropped OEM com.oplus.encryption EncyptionService so the OnePlus gallery's
 * "Move to Private Safe" works, proxying the vault onto the crDroid Axion Sandbox's encrypted
 * file vault (com.android.axion.sandbox). Behavior faithful to the OEM service RE (return
 * conventions + IEncryptProgressListener onStarted/onProgress/onFinished sequence + result
 * codes 0/1/2/3).
 *
 * Move-in is the load-bearing path; getSafeFile/edit are secondary (v1 reports "not in vault"
 * so the gallery treats items as movable; browsing vaulted media happens in the Sandbox app's
 * Vault tab).
 */
package com.oplus.encryption;

import android.app.Service;
import android.content.Intent;
import android.os.IBinder;
import android.os.RemoteException;
import android.util.Log;

import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class EncyptionService extends Service {
    private static final String TAG = SafeBoxNativeBackend.TAG;

    // onFinished(result, count) codes — match the OEM service contract.
    private static final int RESULT_SUCCESS = 0;
    private static final int RESULT_PERMISSION = 1;   // storage permission required
    private static final int RESULT_FAILURE = 2;      // generic failure
    private static final int RESULT_NOT_CONFIGURED = 3; // vault not set up

    // saveEdit*/restoreEditPhoto convention.
    private static final int EDIT_OK = 0;
    private static final int EDIT_ERR = 2;

    private SafeBoxNativeBackend mBackend;
    private final ExecutorService mExecutor = Executors.newSingleThreadExecutor();
    private volatile boolean mStop = false;

    @Override
    public void onCreate() {
        super.onCreate();
        mBackend = new SafeBoxNativeBackend(this);
    }

    @Override
    public IBinder onBind(Intent intent) {
        return mBinder;
    }

    @Override
    public void onDestroy() {
        mExecutor.shutdownNow();
        super.onDestroy();
    }

    private final EncyptionInterface.Stub mBinder = new EncyptionInterface.Stub() {

        // ---- move-in (photos) : returns 0 = dispatched; outcome via listener ----
        @Override
        public int encryptionTasks(List<String> sources, int[] imageTypes,
                boolean keepOriginal, IEncryptProgressListener listener) {
            mStop = false;
            if (sources == null || sources.isEmpty()) {
                fireFinished(listener, RESULT_SUCCESS, 0);
                return 0;
            }
            mExecutor.execute(() -> runMove(sources, listener));
            return 0;
        }

        // ---- move-in (albums) : flatten each folder's image list ----
        @Override
        public int encryptionFoldersTasks(List<EncryptionFolderInfo> folders,
                boolean keepOriginal, IEncryptProgressListener listener) {
            mStop = false;
            if (folders == null || folders.isEmpty()) {
                fireFinished(listener, RESULT_SUCCESS, 0);
                return 0;
            }
            final java.util.ArrayList<String> flat = new java.util.ArrayList<>();
            for (EncryptionFolderInfo f : folders) {
                if (f != null && f.imageList != null) flat.addAll(f.imageList);
            }
            if (flat.isEmpty()) {
                fireFinished(listener, RESULT_SUCCESS, 0);
                return 0;
            }
            mExecutor.execute(() -> runMove(flat, listener));
            return 0;
        }

        @Override
        public void setStopEncryption(boolean stop) {
            if (stop) mStop = true;
        }

        // ---- vault availability ----
        @Override
        public boolean isConfigurationComplete() {
            boolean ok = mBackend.isVaultAvailable();
            if (!ok) Log.i(TAG, "isConfigurationComplete=false (Axion Sandbox vault unreachable)");
            return ok;
        }

        // ---- vault record lookup : never null; matched=0 == not in vault ----
        @Override
        public ImageInfo getSafeFile(String path, long a, long b, String c, String d) {
            // v1: we do not maintain an original->vault mapping table, so report "not found".
            // (Move-in still works; browsing vaulted media is done in the Sandbox Vault tab.)
            ImageInfo info = new ImageInfo();
            info.matched = 0;
            info.deleted = 0;
            info.path = path;
            return info;
        }

        // ---- edit round-trip of an already-vaulted item : unsupported in v1 ----
        @Override
        public int saveEditVideo(String src, String editPath) { return EDIT_ERR; }

        @Override
        public int saveEditPhoto(String src, String editPath, int mode) { return EDIT_ERR; }

        @Override
        public int restoreEditPhoto(String src) { return EDIT_ERR; }

        // ---- deprecated / never-called by the gallery : OEM-faithful safe stubs ----
        @Override
        public void registerCallback(CallbackInterface callback) { /* deprecated no-op */ }

        @Override
        public int encryptionTask(String path, int imageType, boolean keepOriginal) {
            return 2; // OEM: deprecated, returns 2
        }

        @Override
        public int dencryptionTask(String a, String b, String c, String d, String e,
                int f, String g, boolean h) {
            return RESULT_FAILURE;
        }

        @Override
        public void deleteTask(String path) { /* not used by gallery */ }

        @Override
        public String viewTask(String path) { return null; }

        @Override
        public android.graphics.Bitmap getBitmap(String a, String b) { return null; }

        @Override
        public void savePasswordAndMode(int mode, String password) { /* deprecated no-op */ }

        @Override
        public boolean mergeBackupRestoreData() { return false; }

        @Override
        public boolean deleteBackupRestoreData() { return false; }

        @Override
        public android.graphics.Bitmap getBitmapForExternal(String path, int a, int b, int c) {
            return null;
        }
    };

    /** Runs on the executor thread: import all sources into the Axion Sandbox vault. */
    private void runMove(List<String> sources, IEncryptProgressListener listener) {
        if (!mBackend.isVaultAvailable()) {
            Log.w(TAG, "runMove: Axion Sandbox vault unavailable");
            fireFinished(listener, RESULT_NOT_CONFIGURED, sources.size());
            return;
        }
        fireStarted(listener);
        int total = sources.size();
        int failed = 0;
        for (int i = 0; i < total; i++) {
            if (mStop) { Log.i(TAG, "runMove: stopped by request"); break; }
            boolean ok = mBackend.importOne(sources.get(i));
            if (!ok) failed++;
            fireProgress(listener, (int) (((i + 1) * 100L) / total));
        }
        fireFinished(listener, failed == 0 ? RESULT_SUCCESS : RESULT_FAILURE, failed);
    }

    private static void fireStarted(IEncryptProgressListener l) {
        if (l == null) return;
        try { l.onStarted(); } catch (RemoteException e) { Log.w(TAG, "onStarted", e); }
    }

    private static void fireProgress(IEncryptProgressListener l, int p) {
        if (l == null) return;
        try { l.onProgress(p); } catch (RemoteException e) { Log.w(TAG, "onProgress", e); }
    }

    private static void fireFinished(IEncryptProgressListener l, int result, int count) {
        if (l == null) return;
        try { l.onFinished(result, count); } catch (RemoteException e) { Log.w(TAG, "onFinished", e); }
    }
}
