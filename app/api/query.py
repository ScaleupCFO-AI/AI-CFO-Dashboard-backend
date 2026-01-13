from fastapi import APIRouter
from pydantic import BaseModel

from app.qa.answer_financial_question import answer_question

router = APIRouter()


class QueryRequest(BaseModel):
    question: str
    company_id: str


@router.post("/query")
def query_financials(request: QueryRequest):
    """
    Executes a data-grounded financial query.

    - Uses SQL-derived summaries
    - Evidence-first
    - No business logic in API layer
    """
    return answer_question(
        question=request.question,
        company_id=request.company_id
    )
