// SafeBox / Private-Safe translation shim for crDroid.
// Reimplements the OEM com.oplus.encryption.EncyptionInterface so the OnePlus gallery
// (com.oneplus.gallery) binds this service instead of the dropped OEM FileEncryption app.
//
// CRITICAL: method declaration order == binder transaction codes. The OnePlus gallery's
// compiled Proxy uses fixed txn codes 0x1..0x12; AIDL assigns TRANSACTION_<first>=1 in
// declaration order, so this order MUST match the OEM interface exactly (verified by
// smali RE of OppoGallery2 $Stub):
//   0x1 registerCallback        0x2 encryptionTask          0x3 encryptionTasks
//   0x4 setStopEncryption       0x5 dencryptionTask         0x6 deleteTask
//   0x7 viewTask                0x8 getBitmap               0x9 savePasswordAndMode
//   0xa getSafeFile             0xb mergeBackupRestoreData  0xc deleteBackupRestoreData
//   0xd getBitmapForExternal    0xe isConfigurationComplete 0xf encryptionFoldersTasks
//   0x10 saveEditVideo          0x11 saveEditPhoto          0x12 restoreEditPhoto
package com.oplus.encryption;

import com.oplus.encryption.CallbackInterface;
import com.oplus.encryption.IEncryptProgressListener;
import com.oplus.encryption.ImageInfo;
import com.oplus.encryption.EncryptionFolderInfo;
import android.graphics.Bitmap;

interface EncyptionInterface {
    // 0x1 - never called by the gallery (safe stub)
    void registerCallback(CallbackInterface callback);

    // 0x2 - never called by the gallery (single-item variant; safe stub)
    int encryptionTask(String path, int imageType, boolean keepOriginal);

    // 0x3 - MOVE PHOTOS/VIDEOS INTO the vault. sources = content/file paths,
    // imageTypes[] = per-source media-type codes, keepOriginal=false for a move.
    // Progress reported via the listener; returns a status/task int (see impl).
    int encryptionTasks(in List<String> sources, in int[] imageTypes,
            boolean keepOriginal, IEncryptProgressListener listener);

    // 0x4 - cancel the in-flight encryption job.
    void setStopEncryption(boolean stop);

    // 0x5 - never called by the gallery (safe stub)
    int dencryptionTask(String a, String b, String c, String d, String e,
            int f, String g, boolean h);

    // 0x6 - never called by the gallery (safe stub)
    void deleteTask(String path);

    // 0x7 - never called by the gallery (safe stub)
    String viewTask(String path);

    // 0x8 - never called by the gallery (safe stub)
    @nullable Bitmap getBitmap(String a, String b);

    // 0x9 - never called by the gallery (safe stub)
    void savePasswordAndMode(int mode, String password);

    // 0xa - look up a vault record for an item. Returns null when not in the vault.
    @nullable ImageInfo getSafeFile(String path, long a, long b, String c, String d);

    // 0xb - never called by the gallery (safe stub)
    boolean mergeBackupRestoreData();

    // 0xc - never called by the gallery (safe stub)
    boolean deleteBackupRestoreData();

    // 0xd - never called by the gallery (safe stub)
    @nullable Bitmap getBitmapForExternal(String path, int a, int b, int c);

    // 0xe - is the vault set up / usable. True when a native Private Space exists.
    boolean isConfigurationComplete();

    // 0xf - MOVE WHOLE ALBUM(S) INTO the vault.
    int encryptionFoldersTasks(in List<EncryptionFolderInfo> folders,
            boolean keepOriginal, IEncryptProgressListener listener);

    // 0x10 - save an edited video back over its encrypted original. 0 == success.
    int saveEditVideo(String src, String editPath);

    // 0x11 - save an edited photo back over its encrypted original. 0 == success.
    int saveEditPhoto(String src, String editPath, int mode);

    // 0x12 - restore an edited photo. 0 == success.
    int restoreEditPhoto(String src);
}
