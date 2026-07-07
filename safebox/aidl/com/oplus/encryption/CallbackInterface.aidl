// Registered via EncyptionInterface.registerCallback() - which the gallery never calls.
// Present only for AIDL completeness / interface fidelity.
package com.oplus.encryption;

interface CallbackInterface {
    void invokCallback(int value);
}
