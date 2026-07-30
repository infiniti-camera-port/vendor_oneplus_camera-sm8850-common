# vendor_oneplus_camera-sm8850-common

SM8850 (canoe) SoC-common OnePlus camera vendor surface: glue/`.mk`/sepolicy/configs, the
apktool fixup pipeline (`apk_fixups_*.py`, `patches*`), the regen driver
(`extract-files.py`, `sort-blobs-list.py`), the common blob listing
(`proprietary-files-camera-common.txt`), the `CameraThemedIcon` RRO, and (later) the port
java source (`com.oplus.compat` / `oplus-fwk-cam`). The regenerated blob payload
materializes here under `camera/` (gitignored).

- Build path: `vendor/oneplus/camera-sm8850-common`
- Carved (history-preserving) from `infiniti-camera-port/vendor_oplus_camera` @ `3a76ca3` (`staging/16.0_crdroid`).
- Inherited via each device's camera makefile -> `camera-sm8850-common.mk`:
  `camera-infiniti.mk`, `camera-macan.mk`, `camera-macanc.mk`, `camera-fairlady.mk`.
