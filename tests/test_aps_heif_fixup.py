# SPDX-FileCopyrightText: 2026 The LineageOS Project
# SPDX-License-Identifier: Apache-2.0

from aps_heif_fixup import ApsClientFixupError, patch_apsclient_heif_selector


ENCODER = b"libHeifEncoderWrapper.so"
WIN_BUFFER = b"libNativeWinBuffExchange.so"
ENCODER_OFFSET = 0x4C11B
WIN_BUFFER_OFFSET = 0x48551

# The real blob carries each name three times: once standalone as the dlopen
# argument, and twice embedded in a log format string.
ENCODER_LOG_OFFSET = 0x49B0E
WIN_BUFFER_LOG_OFFSET = 0x48738
ENCODER_LOG = b"[ERROR][ %s ] %s: %d  %s()  libHeifEncoderWrapper.so dlopen failed!!"
WIN_BUFFER_LOG = b"[INFO][ %s ] %s: %d  %s()  libNativeWinBuffExchange.so dlopen success"


def _place(image: bytearray, offset: int, payload: bytes) -> None:
    image[offset : offset + len(payload)] = payload


def _synthetic_apsclient() -> bytes:
    image = bytearray(ENCODER_OFFSET + 0x100)
    _place(image, ENCODER_OFFSET, ENCODER)
    _place(image, WIN_BUFFER_OFFSET, WIN_BUFFER)
    _place(image, ENCODER_LOG_OFFSET, ENCODER_LOG)
    _place(image, WIN_BUFFER_LOG_OFFSET, WIN_BUFFER_LOG)
    return bytes(image)


def _changed_offsets(original: bytes, patched: bytes) -> list[int]:
    return [
        offset
        for offset, (before, after) in enumerate(zip(original, patched, strict=True))
        if before != after
    ]


def test_patch_changes_only_the_two_dlopen_arguments() -> None:
    original = _synthetic_apsclient()

    patched = patch_apsclient_heif_selector(original)

    assert _changed_offsets(original, patched) == [
        WIN_BUFFER_OFFSET,
        ENCODER_OFFSET,
    ]
    assert patched[ENCODER_OFFSET:].startswith(b"xibHeifEncoderWrapper.so")
    assert patched[WIN_BUFFER_OFFSET:].startswith(b"xibNativeWinBuffExchange.so")


def test_patch_leaves_log_format_strings_intact() -> None:
    patched = patch_apsclient_heif_selector(_synthetic_apsclient())

    assert patched[ENCODER_LOG_OFFSET:].startswith(ENCODER_LOG)
    assert patched[WIN_BUFFER_LOG_OFFSET:].startswith(WIN_BUFFER_LOG)


def test_patch_survives_a_firmware_bump_that_moves_everything() -> None:
    """An OOS update changes the hash and the layout but keeps the strings.

    The previous implementation pinned the input SHA-256 and absolute offsets,
    so any firmware bump failed closed. Matching on the string keeps working.
    """
    image = bytearray(0x2000)
    _place(image, 0x40, b"unrelated payload that did not exist before\x00")
    _place(image, 0x400, ENCODER)
    _place(image, 0x900, WIN_BUFFER)
    _place(image, 0x1000, ENCODER_LOG)
    bumped = bytes(image)

    patched = patch_apsclient_heif_selector(bumped)

    assert _changed_offsets(bumped, patched) == [0x400, 0x900]
    assert patched[0x400:].startswith(b"xibHeifEncoderWrapper.so")
    assert patched[0x900:].startswith(b"xibNativeWinBuffExchange.so")


def test_patch_is_idempotent() -> None:
    once = patch_apsclient_heif_selector(_synthetic_apsclient())

    twice = patch_apsclient_heif_selector(once)

    assert twice == once


def test_patch_rejects_a_blob_without_the_dlopen_targets() -> None:
    image = bytearray(0x1000)
    _place(image, 0x100, ENCODER)

    try:
        patch_apsclient_heif_selector(bytes(image))
    except ApsClientFixupError as error:
        assert "libNativeWinBuffExchange.so" in str(error)
        assert "not found" in str(error)
    else:
        raise AssertionError("blob missing a dlopen target was accepted")


def test_patch_rejects_an_ambiguous_dlopen_target() -> None:
    image = bytearray(0x1000)
    _place(image, 0x100, ENCODER)
    _place(image, 0x300, ENCODER)
    _place(image, 0x500, WIN_BUFFER)

    try:
        patch_apsclient_heif_selector(bytes(image))
    except ApsClientFixupError as error:
        assert "ambiguous" in str(error)
        assert "found 2" in str(error)
    else:
        raise AssertionError("ambiguous dlopen target was accepted")


def test_embedded_occurrence_alone_is_not_treated_as_the_argument() -> None:
    """A name that only appears inside a log string is not a dlopen argument."""
    image = bytearray(0x1000)
    _place(image, 0x100, ENCODER_LOG)
    _place(image, 0x400, WIN_BUFFER)

    try:
        patch_apsclient_heif_selector(bytes(image))
    except ApsClientFixupError as error:
        assert "libHeifEncoderWrapper.so" in str(error)
        assert "not found" in str(error)
    else:
        raise AssertionError("embedded-only occurrence was treated as the argument")
