from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db.session import get_db
from ..db.models import UserFeedback
# from ..core.security import get_current_user
from app.api.auth import get_current_user, oauth2_scheme

router = APIRouter()

@router.post("/feedback")
async def submit_feedback(
    product_id: int,
    rating: int,
    comment: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    feedback = UserFeedback(
        user_id=current_user.id,
        product_id=product_id,
        rating=rating,
        comment=comment
    )
    db.add(feedback)
    db.commit()
    return {"message": "Feedback submitted successfully"}