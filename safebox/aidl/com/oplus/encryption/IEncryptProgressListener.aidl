// Service -> gallery progress callback for encryptionTasks / encryptionFoldersTasks.
// The gallery subclasses this Stub; our service holds the Proxy and invokes it.
// NOTE(oneway): declared non-oneway here; the gallery's compiled Stub oneway-ness must be
// confirmed against OppoGallery2 smali before the first bind test (mismatch breaks callbacks).
package com.oplus.encryption;

interface IEncryptProgressListener {
    void onStarted();
    void onProgress(int progress);
    void onFinished(int result, int failedCount);
}
