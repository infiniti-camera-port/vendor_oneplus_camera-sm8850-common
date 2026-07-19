# SPDX-FileCopyrightText: 2026 The LineageOS Project
# SPDX-License-Identifier: Apache-2.0

from hashlib import sha256

from aps_heif_fixup import ApsClientFixupError, patch_apsclient_heif_selector


ENCODER_OFFSET = 0x4C11B
WIN_BUFFER_OFFSET = 0x48551


def _synthetic_apsclient() -> bytes:
    image = bytearray(ENCODER_OFFSET + 0x100)
    image[ENCODER_OFFSET : ENCODER_OFFSET + len(b"libHeifEncoderWrapper.so")] = (
        b"libHeifEncoderWrapper.so"
    )
    image[WIN_BUFFER_OFFSET : WIN_BUFFER_OFFSET + len(b"libNativeWinBuffExchange.so")] = (
        b"libNativeWinBuffExchange.so"
    )
    return bytes(image)


def test_patch_changes_only_two_dlopen_targets() -> None:
    original = _synthetic_apsclient()

    patched = patch_apsclient_heif_selector(
        original,
        expected_sha256=sha256(original).hexdigest(),
    )

    changes = [
        (offset, before, after)
        for offset, (before, after) in enumerate(zip(original, patched, strict=True))
        if before != after
    ]
    assert changes == [
        (WIN_BUFFER_OFFSET, ord("l"), ord("x")),
        (ENCODER_OFFSET, ord("l"), ord("x")),
    ]
    assert patched[ENCODER_OFFSET:].startswith(b"xibHeifEncoderWrapper.so")
    assert patched[WIN_BUFFER_OFFSET:].startswith(b"xibNativeWinBuffExchange.so")


def test_patch_rejects_unrecognized_input_digest() -> None:
    original = _synthetic_apsclient()

    try:
        patch_apsclient_heif_selector(original, expected_sha256="0" * 64)
    except ApsClientFixupError as error:
        assert "SHA-256" in str(error)
    else:
        raise AssertionError("unrecognized input digest was accepted")


def test_patch_rejects_target_mismatch_even_with_matching_digest() -> None:
    original = bytearray(_synthetic_apsclient())
    original[ENCODER_OFFSET] = ord("z")
    corrupted = bytes(original)

    try:
        patch_apsclient_heif_selector(
            corrupted,
            expected_sha256=sha256(corrupted).hexdigest(),
        )
    except ApsClientFixupError as error:
        assert "target mismatch" in str(error)
    else:
        raise AssertionError("corrupted target was accepted")
