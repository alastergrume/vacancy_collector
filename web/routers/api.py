from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_session
from schemas.app import StatsOut
from services.stats import collect_stats
from web.security import require_user

router = APIRouter(prefix="/api", dependencies=[Depends(require_user)])


@router.get("/stats", response_model=StatsOut)
def stats(session: Session = Depends(get_session)) -> StatsOut:
    return collect_stats(session)
