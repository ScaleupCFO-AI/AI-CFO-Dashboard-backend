from fastapi import APIRouter
from pydantic import BaseModel
import asyncio

from app.qa.answer_financial_question import answer_question

router = APIRouter()


class QueryRequest(BaseModel):
    question: str
    company_id: str


@router.post("/query")
async def query_financials(request: QueryRequest):
    """
    Executes a data-grounded financial query.

    Guarantees:
    - SQL-backed summaries only
    - Evidence-first
    - No business logic in API layer
    - Deterministic charts
    """
    # print(await answer_question)
    return await answer_question(
        question=request.question,
        company_id=request.company_id
    )
