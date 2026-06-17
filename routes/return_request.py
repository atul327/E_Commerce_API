from fastapi import FastAPI, HTTPException, Path, Header, APIRouter, Depends
from sqlalchemy.orm import Session
from database import SessionLocal

import models
import auth
import schema

admin_route = APIRouter(
    prefix="/admin"
)

# access the database to perform operations
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# verify the token and get the user data
def get_current_user(authourization : str = Header()):
    if not authourization:
        raise HTTPException(status_code=400, detail="Missing Token")
    
    token = authourization.split(" ")[1]

    payload = auth.verify_pass(token) 

    return payload

@admin_route.patch("/requests/{request_id}")
def update_return_order_status(request_id : int = Path(), current_user = Depends(get_current_user), db : Session = Depends(get_db)):
    user_email = current_user.get("sub")

    db_user = db.query(models.User).filter(models.User.email == user_email).first()

    if db_user.role != "admin":
        raise HTTPException(status_code=403, detail="User can't perform update operation")
    
    db_return = db.query(models.Returns).filter(models.Returns.id == request_id).first()

    if not db_return:
        raise HTTPException(404, "No return order found")

    if db_return.status == "Request":
        db_return.status = "Approve"
    elif db_return.status == "Approve":
        db_return.status = "Completed"
    elif db_return.status == "Completed":
        raise HTTPException(status_code = 403, detail = "Return process already completed for this product")
            
    db.commit()
    db.refresh(db_return)

    return {
        "message" : "The order status updated",
        "status" : db_return.status
    }
