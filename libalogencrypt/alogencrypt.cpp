/*
 * Copyright (C) 2026 The LineageOS Project
 *
 * SPDX-License-Identifier: Apache-2.0
 *
 * Plaintext pass-through shim for libalogencrypt.so (log-hygiene + debuggability).
 *
 * The arcsoft APS logging library (/odm/lib64/libalog.so) lazily dlopen()s
 * /odm/lib64/libalogencrypt.so and dlsym()s alog_encrypt() to obfuscate its log
 * buffers before flushing them to disk. That proprietary OEM blob is not shipped
 * on this build (it survives only as a stale file_contexts label), so at runtime
 * libalog logs "libalogencrypt.so dlopen failed!!", its flush thread stalls with
 * an ever-growing pending queue (APS_ALOG flushRoutine g_pendingCount backlog),
 * and the APS/arcsoft log path is left obfuscated and noisy.
 *
 * Reverse-engineered contract of the OEM export (odm/lib64/libalogencrypt.so):
 *   void alog_encrypt(unsigned char* buf, int len);   // mangled _Z12alog_encryptPhi
 * The OEM implementation performs an IN-PLACE, SAME-LENGTH XOR transform over
 * buf[0..len] (16-byte SIMD chunks + byte tail, key gated by sEncryptEnable) and
 * returns void. libalogs call sites (libalog.so 0xb554 / 0xb690) load the
 * dlsymd pointer, call alog_encrypt(buf, len), then IGNORE the return value and
 * write the same buf[0..len] to the log regardless.
 *
 * The minimal safe shim is therefore a no-op pass-through: leave buf unchanged
 * (logs stay plaintext / de-obfuscated / readable) and return void. This makes
 * libalogs dlopen+dlsym succeed so its flush thread drains normally and the
 * "dlopen failed" backlog clears, with no proprietary dependency. (It is a
 * logging-hygiene / debuggability module; it is not itself a fix for any camera
 * capture-path race.)
 *
 * Compiled as C++ (no extern "C") so the symbol is emitted with the exact Itanium
 * mangling libalog dlsym()s: _Z12alog_encryptPhi.
 */

// alog_encrypt(unsigned char*, int) -> _Z12alog_encryptPhi
__attribute__((visibility("default")))
void alog_encrypt(unsigned char* /*buf*/, int /*len*/) {
    // Pass-through: do not transform the buffer. Logs remain plaintext and the
    // libalog flush thread proceeds, matching the OEM void return contract.
}
