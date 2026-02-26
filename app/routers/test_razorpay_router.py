from fastapi import APIRouter
from app.core.razorpay_client import client

router = APIRouter(
    prefix="/test",
    tags=["Razorpay Test"]
)

@router.get("/contact")
def test_contact():
    return client.contact.create({
        "name": "Test User",
        "type": "customer",
        "reference_id": "test_1"
    })