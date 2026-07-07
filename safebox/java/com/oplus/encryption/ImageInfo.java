/*
 * SafeBox translation shim - vault record returned by EncyptionInterface.getSafeFile().
 *
 * WIRE-CRITICAL: the OnePlus gallery reads this back via its own
 * com.oplus.encryption.ImageInfo(Parcel) / SafeBoxImageInfo(Parcel), which reads fields in
 * EXACTLY this order (verified by smali RE of OppoGallery2):
 *     int matched, int deleted, String path, String md5, String gid, long fileLength, String source
 * writeToParcel() below MUST match that order byte-for-byte.
 */
package com.oplus.encryption;

import android.os.Parcel;
import android.os.Parcelable;

public class ImageInfo implements Parcelable {
    /** 1 == a vault record exists for the queried item, 0 == not found. */
    public int matched;
    /** 1 == the record is tombstoned/deleted. */
    public int deleted;
    /** Path of the item as the vault knows it. */
    public String path;
    public String md5;
    /** Vault record id. */
    public String gid;
    public long fileLength;
    /** Original (pre-vault) source path. */
    public String source;

    public ImageInfo() {}

    protected ImageInfo(Parcel in) {
        matched = in.readInt();
        deleted = in.readInt();
        path = in.readString();
        md5 = in.readString();
        gid = in.readString();
        fileLength = in.readLong();
        source = in.readString();
    }

    @Override
    public void writeToParcel(Parcel dest, int flags) {
        dest.writeInt(matched);
        dest.writeInt(deleted);
        dest.writeString(path);
        dest.writeString(md5);
        dest.writeString(gid);
        dest.writeLong(fileLength);
        dest.writeString(source);
    }

    @Override
    public int describeContents() {
        return 0;
    }

    public static final Parcelable.Creator<ImageInfo> CREATOR = new Parcelable.Creator<ImageInfo>() {
        @Override
        public ImageInfo createFromParcel(Parcel in) {
            return new ImageInfo(in);
        }

        @Override
        public ImageInfo[] newArray(int size) {
            return new ImageInfo[size];
        }
    };
}
