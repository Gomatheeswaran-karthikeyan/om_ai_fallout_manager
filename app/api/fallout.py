from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.request_model import CloseCaseRequest, FalloutRequest
from app.models.response_model import CloseCaseResponse, FalloutAnalysisResponse, FalloutMeta
from app.service.closed_cases_service import record_closed_case
from app.service.fallout_service import analyze_fallout
from app.service.metadata_service import list_all_meta

router = APIRouter(prefix="/fallout", tags=["Fallout"])


@router.post(
    "/analyze",
    response_model=FalloutAnalysisResponse,
    summary="Analyze a fallout — returns meta resolution directly if confident, else LLM suggestion",
)
async def analyze_fallout_endpoint(
    payload: FalloutRequest,
    session: AsyncSession = Depends(get_db),
) -> FalloutAnalysisResponse:
    try:
        return await analyze_fallout(session, payload)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Fallout analysis failed: {exc}")


@router.post(
    "/close",
    response_model=CloseCaseResponse,
    summary="Record a resolved fallout case into the closed cases history",
)
async def close_case_endpoint(
    payload: CloseCaseRequest,
    session: AsyncSession = Depends(get_db),
) -> CloseCaseResponse:
    try:
        return await record_closed_case(session, payload)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Failed to record closed case: {exc}")


@router.get(
    "/meta",
    response_model=list[FalloutMeta],
    summary="List all fallout metadata knowledge base entries",
)
async def list_meta_endpoint(
    session: AsyncSession = Depends(get_db),
) -> list[FalloutMeta]:
    try:
        return await list_all_meta(session)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Failed to fetch metadata: {exc}")
