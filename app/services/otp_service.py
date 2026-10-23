
import hashlib
import secrets
import time
from dataclasses import dataclass


OTP_EXPIRY_SECONDS = 300
RESEND_COOLDOWN_SECONDS = 60
MAX_VERIFICATION_ATTEMPTS = 5


@dataclass
class OTPRecord:
    otp_hash: str
    expires_at: float
    next_resend_at: float
    attempts: int = 0
    used: bool = False


class OTPService:
    def __init__(self):
        self._records: dict[str, OTPRecord] = {}

    @staticmethod
    def _hash_otp(phone: str, otp: str) -> str:
        value = f"{phone}:{otp}".encode("utf-8")
        return hashlib.sha256(value).hexdigest()

    def request_otp(self, phone: str) -> None:
        now = time.time()
        existing = self._records.get(phone)

        if existing and now < existing.next_resend_at:
            remaining = int(existing.next_resend_at - now) + 1
            raise ValueError(
                f"Please wait {remaining} seconds before requesting another OTP."
            )

        otp = f"{secrets.randbelow(1_000_000):06d}"

        self._records[phone] = OTPRecord(
            otp_hash=self._hash_otp(phone, otp),
            expires_at=now + OTP_EXPIRY_SECONDS,
            next_resend_at=now + RESEND_COOLDOWN_SECONDS,
        )

        # Development-only output.
        # Never return the OTP in a normal API response.
        print(f"[DEV ONLY] OTP for {phone}: {otp}")

    def verify_otp(self, phone: str, otp: str) -> bool:
        record = self._records.get(phone)
        now = time.time()

        if record is None or record.used:
            return False

        if now >= record.expires_at:
            self._records.pop(phone, None)
            return False

        if record.attempts >= MAX_VERIFICATION_ATTEMPTS:
            self._records.pop(phone, None)
            return False

        record.attempts += 1

        if secrets.compare_digest(
            record.otp_hash,
            self._hash_otp(phone, otp),
        ):
            record.used = True
            self._records.pop(phone, None)
            return True

        return False


otp_service = OTPService()
