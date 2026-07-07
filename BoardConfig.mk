# Camera (Oplus camera port): OEM camera sets vendor props outside the standard namespace.
BUILD_BROKEN_VENDOR_PROPERTY_NAMESPACE := true

# AI Unit: the stock app-dir JNI payloads (product/{priv-app,app}/*/lib/arm64)
# ship via PRODUCT_COPY_FILES. The apks embed no native libs and PM derives the
# app ABI from the bundled lib dir (the OOS-stock layout); no Soong prebuilt
# module type can install into an app dir. Only disables the ELF-in-copy-files
# lint.
BUILD_BROKEN_ELF_PREBUILT_PRODUCT_COPY_FILES := true
