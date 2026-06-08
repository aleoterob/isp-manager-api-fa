from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.responses import EnvelopeRoute
from app.db.session import get_db

router = APIRouter(tags=["app"], route_class=EnvelopeRoute)


@router.get("/")
def root():
    return {"status": "ok"}


@router.get("/health/live")
def live():
    return {"status": "ok"}


@router.get("/health/ready")
def ready(db: Annotated[Session, Depends(get_db)]):
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": {"status": "up"}}
