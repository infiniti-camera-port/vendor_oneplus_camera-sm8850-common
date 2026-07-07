# AI Unit: the stock app-dir JNI payloads (product/{priv-app,app}/*/lib/arm64)
# ship via PRODUCT_COPY_FILES. The apks embed no native libs and PM derives the
# app ABI from the bundled lib dir (the OOS-stock layout); no Soong prebuilt
# module type can install into an app dir. Only disables the ELF-in-copy-files
# lint.
BUILD_BROKEN_ELF_PREBUILT_PRODUCT_COPY_FILES := true
