from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import Member
from schemas import MemberCreate, MemberResponse

router = APIRouter(prefix="/members", tags=["members"])


@router.get("", response_model=list[MemberResponse])
def list_members(db: Session = Depends(get_db)):
    return db.query(Member).all()


@router.post("", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
def create_member(body: MemberCreate, db: Session = Depends(get_db)):
    member = Member(**body.model_dump(), created_at=date.today())
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


@router.get("/{member_id}", response_model=MemberResponse)
def get_member(member_id: int, db: Session = Depends(get_db)):
    member = db.get(Member, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return member
