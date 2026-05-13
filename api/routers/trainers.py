from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Trainer
from schemas import TrainerResponse

router = APIRouter(prefix="/trainers", tags=["trainers"])


@router.get("", response_model=list[TrainerResponse])
def list_trainers(db: Session = Depends(get_db)):
    return db.query(Trainer).all()
