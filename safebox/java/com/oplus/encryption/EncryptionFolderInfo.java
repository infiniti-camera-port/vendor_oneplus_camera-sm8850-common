/*
 * SafeBox translation shim - album descriptor passed INTO
 * EncyptionInterface.encryptionFoldersTasks() by the OnePlus gallery.
 *
 * WIRE-CRITICAL: the gallery WRITES this (it is an 'in' param) in EXACTLY this order
 * (verified by smali RE of OppoGallery2); createFromParcel() below MUST read the same order:
 *     String folderName, List<String> imageList, String path, String createFrom
 */
package com.oplus.encryption;

import android.os.Parcel;
import android.os.Parcelable;

import java.util.ArrayList;
import java.util.List;

public class EncryptionFolderInfo implements Parcelable {
    public String folderName;
    public List<String> imageList;
    public String path;
    public String createFrom;

    public EncryptionFolderInfo() {}

    protected EncryptionFolderInfo(Parcel in) {
        folderName = in.readString();
        imageList = in.createStringArrayList();
        path = in.readString();
        createFrom = in.readString();
    }

    @Override
    public void writeToParcel(Parcel dest, int flags) {
        dest.writeString(folderName);
        dest.writeStringList(imageList);
        dest.writeString(path);
        dest.writeString(createFrom);
    }

    @Override
    public int describeContents() {
        return 0;
    }

    public static final Parcelable.Creator<EncryptionFolderInfo> CREATOR =
            new Parcelable.Creator<EncryptionFolderInfo>() {
        @Override
        public EncryptionFolderInfo createFromParcel(Parcel in) {
            return new EncryptionFolderInfo(in);
        }

        @Override
        public EncryptionFolderInfo[] newArray(int size) {
            return new EncryptionFolderInfo[size];
        }
    };
}
