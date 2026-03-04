from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


# Send OTP request
class ReferenceOTPSendRequest(BaseModel):
    reference_id: int

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "reference_id": ""
            }
        }
    )
    
# Verify OTP request
class ReferenceOTPVerifyRequest(BaseModel):
    reference_id: int
    otp_code: str = Field(min_length=4, max_length=6)
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "reference_id": "",
                "otp_code": ""
            }
        }
    )

# Verify OTP response
class ReferenceOTPVerifyResponse(BaseModel):
    reference_id: int
    verified: bool
    verified_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


# OTP table response
class ReferenceOTPResponse(BaseModel):
    id: int
    reference_id: int
    is_used: bool
    attempts: int
    expires_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Internal create 
class ReferenceOTPInternalCreate(BaseModel):
    reference_id: int
    otp_code: str
    expires_at: datetime
