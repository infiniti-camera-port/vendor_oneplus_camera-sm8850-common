# SPDX-FileCopyrightText: 2026 The LineageOS Project
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
from typing import Final


# The APS client chooses its HEIF handoff at runtime: it dlopen()s these two
# optional native helpers and falls back to OPlus' Java reflection route when
# they cannot be resolved. Stock keeps this client in /product and the helpers
# in /system_ext, so product namespace isolation makes the dlopen fail and the
# reflection path is what actually runs. Our system_ext remap co-located them
# and unintentionally enabled the native route stock does not use.
#
# Neutralise both dlopen targets by rewriting the leading byte of their name.
# The replacement is the same length, so the ELF layout, section sizes and every
# other offset are untouched - the whole fixup is two bytes.
#
# Each name also occurs inside two log format strings:
#     "[ERROR][ %s ] %s: %d  %s()  libX.so dlopen failed!! dlerror:%s"
#     "[INFO][ %s ] %s: %d  %s()  libX.so dlopen success"
# Those are deliberately left alone so the logs stay readable. The dlopen
# argument is the only *standalone NUL-terminated* occurrence, and that is how
# it is located here.
#
# Deliberately no file digest and no absolute offsets: an OOS firmware bump
# reshuffles the binary and changes its hash without necessarily touching these
# strings, and pinning either would make the fixup fail closed on every update
# for no benefit. Matching on the string itself keeps working as long as the
# thing being patched still exists, and fails loudly when it genuinely does not.
_DLOPEN_TARGETS: Final = (
    b"libHeifEncoderWrapper.so",
    b"libNativeWinBuffExchange.so",
)
_NEUTRALISED_PREFIX: Final = b"x"


class ApsClientFixupError(RuntimeError):
    pass


def _neutralised(name: bytes) -> bytes:
    return _NEUTRALISED_PREFIX + name[len(_NEUTRALISED_PREFIX) :]


def _dlopen_arg_offsets(blob: bytes, name: bytes) -> list[int]:
    """Offsets of every standalone NUL-terminated occurrence of ``name``.

    Occurrences embedded in a longer string (the log format strings) are not
    NUL-terminated at the end of the name and are skipped.
    """
    offsets = []
    start = blob.find(name)
    while start != -1:
        end = start + len(name)
        if blob[end : end + 1] == b"\x00":
            offsets.append(start)
        start = blob.find(name, start + 1)
    return offsets


def patch_apsclient_heif_selector(blob: bytes) -> bytes:
    patched = bytearray(blob)

    for name in _DLOPEN_TARGETS:
        replacement = _neutralised(name)
        if len(replacement) != len(name):
            msg = f"replacement for {name!r} changes length"
            raise ApsClientFixupError(msg)

        offsets = _dlopen_arg_offsets(bytes(patched), name)
        if len(offsets) > 1:
            listed = ", ".join(hex(offset) for offset in offsets)
            msg = (
                f"ambiguous APS client dlopen target {name.decode()}: expected a "
                f"single NUL-terminated occurrence, found {len(offsets)} ({listed})"
            )
            raise ApsClientFixupError(msg)

        if not offsets:
            # Already neutralised (re-running against a patched blob) is a no-op.
            if _dlopen_arg_offsets(bytes(patched), replacement):
                continue
            msg = (
                f"APS client dlopen target not found: neither {name.decode()} nor "
                f"{replacement.decode()} occurs as a NUL-terminated string. The "
                "blob no longer selects its HEIF handoff this way; re-check the "
                "fixup against the current firmware before shipping it."
            )
            raise ApsClientFixupError(msg)

        offset = offsets[0]
        patched[offset : offset + len(name)] = replacement

    return bytes(patched)


def patch_apsclient_heif_selector_file(file_path: str) -> None:
    path = Path(file_path)
    path.write_bytes(patch_apsclient_heif_selector(path.read_bytes()))
