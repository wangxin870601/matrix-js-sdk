#!/bin/env python
#
# Copyright 2023 The Matrix.org Foundation C.I.C.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
This file is a Python script to generate test data for crypto tests.

To run it:

python -m venv env
./env/bin/pip install cryptography canonicaljson
./env/bin/python generate-test-data.py > index.ts
"""

import base64
import json

from canonicaljson import encode_canonical_json
from cryptography.hazmat.primitives.asymmetric import ed25519, x25519
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from random import randbytes, seed

ALICE_DATA = {
    "TEST_USER_ID": "@alice:localhost",
    "TEST_DEVICE_ID": "test_device",
    "TEST_ROOM_ID": "!room:id",
    # any 32-byte string can be an ed25519 private key.
    "TEST_DEVICE_PRIVATE_KEY_BYTES": b"deadbeefdeadbeefdeadbeefdeadbeef",

    "MASTER_CROSS_SIGNING_PRIVATE_KEY_BYTES": b"doyouspeakwhaaaaaaaaaaaaaaaaaale",
    "USER_CROSS_SIGNING_PRIVATE_KEY_BYTES": b"useruseruseruseruseruseruseruser",
    "SELF_CROSS_SIGNING_PRIVATE_KEY_BYTES": b"selfselfselfselfselfselfselfself",

    # Private key for secure key backup. There are some sessions encrypted with this key in megolm-backup.spec.ts
    "B64_BACKUP_DECRYPTION_KEY": "dwdtCnMYpX08FsFyUbJmRd9ML4frwJkqsXf7pR25LCo=",

    "OTK": "j3fR3HemM16M7CWhoI4Sk5ZsdmdfQHsKL1xuSft6MSw"
}

BOB_DATA = {
    "TEST_USER_ID": "@bob:xyz",
    "TEST_DEVICE_ID": "bob_device",
    "TEST_ROOM_ID": "!room:id",
    # any 32-byte string can be an ed25519 private key.
    "TEST_DEVICE_PRIVATE_KEY_BYTES": b"Deadbeefdeadbeefdeadbeefdeadbeef",

    "MASTER_CROSS_SIGNING_PRIVATE_KEY_BYTES": b"Doyouspeakwhaaaaaaaaaaaaaaaaaale",
    "USER_CROSS_SIGNING_PRIVATE_KEY_BYTES": b"Useruseruseruseruseruseruseruser",
    "SELF_CROSS_SIGNING_PRIVATE_KEY_BYTES": b"Selfselfselfselfselfselfselfself",

    # Private key for secure key backup. There are some sessions encrypted with this key in megolm-backup.spec.ts
    "B64_BACKUP_DECRYPTION_KEY": "DwdtCnMYpX08FsFyUbJmRd9ML4frwJkqsXf7pR25LCo=",

    "OTK": "j3fR3HemM16M7CWhoI4Sk5ZsdmdfQHsKL1xuSft6MSw"
}

def main() -> None:
    print(
        f"""\
/* Test data for cryptography tests
 *
 * Do not edit by hand! This file is generated by `./generate-test-data.py`
 */

import {{ IDeviceKeys, IMegolmSessionData }} from "../../../src/@types/crypto";
import {{ IDownloadKeyResult }} from "../../../src";
import {{ KeyBackupInfo }} from "../../../src/crypto-api";

/* eslint-disable comma-dangle */

// Alice data

{build_test_data(ALICE_DATA)}
// Bob data

{build_test_data(BOB_DATA, "BOB_")}
""",
        end="",
    )

# Use static seed to have stable random test data upon new generation
seed(10)

def build_test_data(user_data, prefix = "") -> str:
    private_key = ed25519.Ed25519PrivateKey.from_private_bytes(
             user_data["TEST_DEVICE_PRIVATE_KEY_BYTES"]
        )
    b64_public_key = encode_base64(
        private_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    )

    device_data = {
        "algorithms": ["m.olm.v1.curve25519-aes-sha2", "m.megolm.v1.aes-sha2"],
        "device_id":  user_data["TEST_DEVICE_ID"],
        "keys": {
            f"curve25519:{user_data['TEST_DEVICE_ID']}": "F4uCNNlcbRvc7CfBz95ZGWBvY1ALniG1J8+6rhVoKS0",
            f"ed25519:{user_data['TEST_DEVICE_ID']}": b64_public_key,
        },
        "signatures": {user_data['TEST_USER_ID']: {}},
        "user_id": user_data["TEST_USER_ID"],
    }

    device_data["signatures"][user_data["TEST_USER_ID"]][f"ed25519:{user_data['TEST_DEVICE_ID']}"] = sign_json(
        device_data, private_key
    )

    master_private_key = ed25519.Ed25519PrivateKey.from_private_bytes(
        user_data["MASTER_CROSS_SIGNING_PRIVATE_KEY_BYTES"]
    )
    b64_master_public_key = encode_base64(
        master_private_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    )
    b64_master_private_key = encode_base64(user_data["MASTER_CROSS_SIGNING_PRIVATE_KEY_BYTES"])

    self_signing_private_key = ed25519.Ed25519PrivateKey.from_private_bytes(
        user_data["SELF_CROSS_SIGNING_PRIVATE_KEY_BYTES"]
    )
    b64_self_signing_public_key = encode_base64(
        self_signing_private_key.public_key().public_bytes(
            Encoding.Raw, PublicFormat.Raw
        )
    )
    b64_self_signing_private_key = encode_base64( user_data["SELF_CROSS_SIGNING_PRIVATE_KEY_BYTES"])

    user_signing_private_key = ed25519.Ed25519PrivateKey.from_private_bytes(
         user_data["USER_CROSS_SIGNING_PRIVATE_KEY_BYTES"]
    )
    b64_user_signing_public_key = encode_base64(
        user_signing_private_key.public_key().public_bytes(
            Encoding.Raw, PublicFormat.Raw
        )
    )
    b64_user_signing_private_key = encode_base64(user_data["USER_CROSS_SIGNING_PRIVATE_KEY_BYTES"])

    backup_decryption_key = x25519.X25519PrivateKey.from_private_bytes(
        base64.b64decode(user_data["B64_BACKUP_DECRYPTION_KEY"])
    )
    b64_backup_public_key = encode_base64(
        backup_decryption_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    )

    backup_data = {
        "algorithm": "m.megolm_backup.v1.curve25519-aes-sha2",
        "version": "1",
        "auth_data": {
            "public_key": b64_backup_public_key,
        },
    }
    # sign with our device key
    sig = sign_json(backup_data["auth_data"], private_key)
    backup_data["auth_data"]["signatures"] = {
        user_data["TEST_USER_ID"]: {f"ed25519:{user_data['TEST_DEVICE_ID']}": sig}
    }

    set_of_exported_room_keys = [build_exported_megolm_key(), build_exported_megolm_key()]

    additional_exported_room_key = build_exported_megolm_key()

    otk_to_sign = {
        "key": user_data['OTK']
    }
    # sign our public otk key with our device key
    otk = sign_json(otk_to_sign, private_key)
    otks = {
        user_data["TEST_USER_ID"]: {
            user_data['TEST_DEVICE_ID']: {
                 "signed_curve25519:AAAAHQ": {
                    "key": user_data["OTK"],
                    "signatures": {
                        user_data["TEST_USER_ID"]: {f"ed25519:{user_data['TEST_DEVICE_ID']}": otk}
                    }
                 }
            }
        }
    }

    return f"""\
export const {prefix}TEST_USER_ID = "{user_data['TEST_USER_ID']}";
export const {prefix}TEST_DEVICE_ID = "{user_data['TEST_DEVICE_ID']}";
export const {prefix}TEST_ROOM_ID = "{user_data['TEST_ROOM_ID']}";

/** The base64-encoded public ed25519 key for this device */
export const {prefix}TEST_DEVICE_PUBLIC_ED25519_KEY_BASE64 = "{b64_public_key}";

/** Signed device data, suitable for returning from a `/keys/query` call */
export const {prefix}SIGNED_TEST_DEVICE_DATA: IDeviceKeys = {json.dumps(device_data, indent=4)};

/** base64-encoded public master cross-signing key */
export const {prefix}MASTER_CROSS_SIGNING_PUBLIC_KEY_BASE64 = "{b64_master_public_key}";

/** base64-encoded private master cross-signing key */
export const {prefix}MASTER_CROSS_SIGNING_PRIVATE_KEY_BASE64 = "{b64_master_private_key}";

/** base64-encoded public self cross-signing key */
export const {prefix}SELF_CROSS_SIGNING_PUBLIC_KEY_BASE64 = "{b64_self_signing_public_key}";

/** base64-encoded private self signing cross-signing key */
export const {prefix}SELF_CROSS_SIGNING_PRIVATE_KEY_BASE64 = "{b64_self_signing_private_key}";

/** base64-encoded public user cross-signing key */
export const {prefix}USER_CROSS_SIGNING_PUBLIC_KEY_BASE64 = "{b64_user_signing_public_key}";

/** base64-encoded private user signing cross-signing key */
export const {prefix}USER_CROSS_SIGNING_PRIVATE_KEY_BASE64 = "{b64_user_signing_private_key}";

/** Signed cross-signing keys data, also suitable for returning from a `/keys/query` call */
export const {prefix}SIGNED_CROSS_SIGNING_KEYS_DATA: Partial<IDownloadKeyResult> = {
        json.dumps(build_cross_signing_keys_data(user_data), indent=4)
};

/** base64-encoded backup decryption (private) key */
export const {prefix}BACKUP_DECRYPTION_KEY_BASE64 = "{ user_data['B64_BACKUP_DECRYPTION_KEY'] }";

/** Signed backup data, suitable for return from `GET /_matrix/client/v3/room_keys/keys/{{roomId}}/{{sessionId}}` */
export const {prefix}SIGNED_BACKUP_DATA: KeyBackupInfo = { json.dumps(backup_data, indent=4) };

/** A set of megolm keys that can be imported via CryptoAPI#importRoomKeys */
export const {prefix}MEGOLM_SESSION_DATA_ARRAY: IMegolmSessionData[] = {
    json.dumps(set_of_exported_room_keys, indent=4)
};

/** An exported megolm session */
export const {prefix}MEGOLM_SESSION_DATA: IMegolmSessionData = {
        json.dumps(additional_exported_room_key, indent=4)
};

/** Signed OTKs, returned by `POST /keys/claim` */
export const {prefix}ONE_TIME_KEYS = { json.dumps(otks, indent=4) };
"""


def build_cross_signing_keys_data(user_data) -> dict:
    """Build the signed cross-signing-keys data for return from /keys/query"""
    master_private_key = ed25519.Ed25519PrivateKey.from_private_bytes(
        user_data["MASTER_CROSS_SIGNING_PRIVATE_KEY_BYTES"]
    )
    b64_master_public_key = encode_base64(
        master_private_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    )
    self_signing_private_key = ed25519.Ed25519PrivateKey.from_private_bytes(
         user_data["SELF_CROSS_SIGNING_PRIVATE_KEY_BYTES"]
    )
    b64_self_signing_public_key = encode_base64(
        self_signing_private_key.public_key().public_bytes(
            Encoding.Raw, PublicFormat.Raw
        )
    )
    user_signing_private_key = ed25519.Ed25519PrivateKey.from_private_bytes(
         user_data["USER_CROSS_SIGNING_PRIVATE_KEY_BYTES"]
    )
    b64_user_signing_public_key = encode_base64(
        user_signing_private_key.public_key().public_bytes(
            Encoding.Raw, PublicFormat.Raw
        )
    )
    # create without signatures initially
    cross_signing_keys_data = {
        "master_keys": {
             user_data["TEST_USER_ID"]: {
                "keys": {
                    f"ed25519:{b64_master_public_key}": b64_master_public_key,
                },
                "user_id": user_data["TEST_USER_ID"],
                "usage": ["master"],
            }
        },
        "self_signing_keys": {
            user_data["TEST_USER_ID"]: {
                "keys": {
                    f"ed25519:{b64_self_signing_public_key}": b64_self_signing_public_key,
                },
                "user_id": user_data["TEST_USER_ID"],
                "usage": ["self_signing"],
            },
        },
        "user_signing_keys": {
            user_data["TEST_USER_ID"]: {
                "keys": {
                    f"ed25519:{b64_user_signing_public_key}": b64_user_signing_public_key,
                },
                "user_id": user_data["TEST_USER_ID"],
                "usage": ["user_signing"],
            },
        },
    }
    # sign the sub-keys with the master
    for k in ["self_signing_keys", "user_signing_keys"]:
        to_sign = cross_signing_keys_data[k][user_data["TEST_USER_ID"]]
        sig = sign_json(to_sign, master_private_key)
        to_sign["signatures"] = {
            user_data["TEST_USER_ID"]: {f"ed25519:{b64_master_public_key}": sig}
        }

    return cross_signing_keys_data


def encode_base64(input_bytes: bytes) -> str:
    """Encode with unpadded base64"""
    output_bytes = base64.b64encode(input_bytes)
    output_string = output_bytes.decode("ascii")
    return output_string.rstrip("=")


def sign_json(json_object: dict, private_key: ed25519.Ed25519PrivateKey) -> str:
    """
    Sign the given json object

    Returns the base64-encoded signature of signing `input` following the Matrix
    JSON signature algorithm [1]

    [1]: https://spec.matrix.org/v1.7/appendices/#signing-details
    """
    signatures = json_object.pop("signatures", {})
    unsigned = json_object.pop("unsigned", None)

    signature = private_key.sign(encode_canonical_json(json_object))
    signature_base64 = encode_base64(signature)

    json_object["signatures"] = signatures
    if unsigned is not None:
        json_object["unsigned"] = unsigned

    return signature_base64

def build_exported_megolm_key() -> dict:
    """
    Creates an exported megolm room key, as per https://gitlab.matrix.org/matrix-org/olm/blob/master/docs/megolm.md#session-export-format
    that can be imported via importRoomKeys API.
    """
    index = 0
    private_key = ed25519.Ed25519PrivateKey.from_private_bytes(randbytes(32))
    # Just use radom bytes for the ratchet parts
    ratchet = randbytes(32 * 4)
    # exported key, start with version byte
    exported_key = bytearray(b'\x01')
    exported_key += index.to_bytes(4, 'big')
    exported_key += ratchet
    # KPub
    exported_key += private_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)


    megolm_export = {
        "algorithm": "m.megolm.v1.aes-sha2",
        "room_id": "!roomA:example.org",
        "sender_key": "/Bu9e34hUClhddpf4E5gu5qEAdMY31+1A9HbiAeeQgo",
        "session_id": encode_base64(
            private_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
        ),
        "session_key": encode_base64(exported_key),
        "sender_claimed_keys": {
            "ed25519": encode_base64(ed25519.Ed25519PrivateKey.from_private_bytes(randbytes(32)).public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)),
        },
        "forwarding_curve25519_key_chain": [],
    }

    return megolm_export


if __name__ == "__main__":
    main()
