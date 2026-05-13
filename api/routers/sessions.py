from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import Member, PTSession, Trainer
from schemas import SessionCreate, SessionResponse

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(body: SessionCreate, db: Session = Depends(get_db)):
    if not db.get(Member, body.member_id):
        raise HTTPException(status_code=404, detail="Member not found")
    if not db.get(Trainer, body.trainer_id):
        raise HTTPException(status_code=404, detail="Trainer not found")

    session = PTSession(**body.model_dump(), created_at=date.today())
    db.add(session)
    db.commit()
    db.refresh(session)
    return session
