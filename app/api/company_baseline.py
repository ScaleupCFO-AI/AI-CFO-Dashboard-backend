from fastapi import APIRouter
from app.presentation.baseline_presentation import get_company_baseline


router = APIRouter()

@router.get("/company/{company_id}/baseline")
@router.get("/company/{company_id}/baseline")
def company_baseline(company_id: str):
    presentation = get_company_baseline(company_id)
    return {
        "presentation": presentation
    }
