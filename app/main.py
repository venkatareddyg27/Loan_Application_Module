from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from app.core.session import engine,Base
from app.db_models import *
from app.routers.loan_application_router import router as loan_application_router
from app.routers.loan_application_purpose_router import router as loan_application_purpose_router
from app.routers.loan_application_reference_router import router as loan_application_reference_router
from app.routers.reference_otp_router import router as reference_otp_router
from app.routers.loan_application_summary_router import router as loan_application_summary_router
from app.routers.loan_application_declaration_router import router as loan_application_declaration_router
from app.routers.lender_router import router as lender_router
from app.routers.loan_disbursement_router import router as loan_disbursement_router

app = FastAPI(debug=True, title="LOAN APPLICATION API")

Base.metadata.create_all(bind=engine)


app.include_router(loan_application_router)
app.include_router(loan_application_purpose_router)
app.include_router(loan_application_reference_router)   
app.include_router(reference_otp_router)
app.include_router(loan_application_declaration_router)
app.include_router(loan_application_summary_router)
app.include_router(lender_router)
app.include_router(loan_disbursement_router)




app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # for testing only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)






