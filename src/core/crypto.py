import base64
import hashlib
import hmac

from cryptography.fernet import Fernet

KDF_ITERATIONS = 480_000
_VERIFIER_LABEL = b"password-manager-verifier"


def derive_key(master_password: str, salt: bytes) -> bytes:
    raw = hashlib.pbkdf2_hmac("sha256", master_password.encode("utf-8"), salt, KDF_ITERATIONS, dklen=32)
    return base64.urlsafe_b64encode(raw)


def make_verifier(key: bytes) -> bytes:
    return hmac.new(key, _VERIFIER_LABEL, hashlib.sha256).digest()


def verify_master(master_password: str, salt: bytes, verifier: bytes) -> bool:
    candidate = make_verifier(derive_key(master_password, salt))
    return hmac.compare_digest(candidate, verifier)


def encrypt_password(plain: str, key: bytes) -> str:
    return Fernet(key).encrypt(plain.encode("utf-8")).decode("ascii")


def decrypt_password(token: str, key: bytes) -> str:
    return Fernet(key).decrypt(token.encode("ascii")).decode("utf-8")
