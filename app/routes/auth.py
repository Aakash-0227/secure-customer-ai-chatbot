
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from app.database import SessionLocal
from app.models import Customer
from app.services.otp_service import otp_service
from app.services.security import create_access_token, verify_access_token
from app.services.auth_dependency import get_current_customer_id


router = APIRouter(prefix="/auth", tags=["Authentication"])


class OTPRequest(BaseModel):
    phone: str = Field(pattern=r"^[0-9]{10}$")


class OTPVerify(BaseModel):
    phone: str = Field(pattern=r"^[0-9]{10}$")
    otp: str = Field(pattern=r"^[0-9]{6}$")


@router.post("/request-otp")
def request_otp(request: OTPRequest):
    db = SessionLocal()

    try:
        customer = (
            db.query(Customer)
            .filter(Customer.phone == request.phone)
            .first()
        )

        if customer is None:
            raise HTTPException(
                status_code=404,
                detail="Customer not found.",
            )

        try:
            otp_service.request_otp(request.phone)
        except ValueError as exc:
            raise HTTPException(
                status_code=429,
                detail=str(exc),
            ) from exc

        return {
            "message": "OTP requested. Check the development server terminal."
        }

    finally:
        db.close()


@router.post("/verify-otp")
def verify_otp(request: OTPVerify):
    db = SessionLocal()

    try:
        customer = (
            db.query(Customer)
            .filter(Customer.phone == request.phone)
            .first()
        )

        if customer is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid phone number or OTP.",
            )

        if not otp_service.verify_otp(request.phone, request.otp):
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired OTP.",
            )

        access_token = create_access_token(customer.id)

        return {
            "message": "OTP verified successfully.",
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 1800,
        }

    finally:
        db.close()


@router.get("/me")
def get_me(
    customer_id: int = Depends(get_current_customer_id),
):
    db = SessionLocal()

    try:
        customer = (
            db.query(Customer)
            .filter(Customer.id == customer_id)
            .first()
        )

        if customer is None:
            raise HTTPException(
                status_code=401,
                detail="Customer account not found.",
            )

        return {
            "id": customer.id,
            "name": customer.name,
            "email": customer.email,
            "phone": customer.phone,
        }

    finally:
        db.close()
