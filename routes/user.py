from fastapi import APIRouter, Depends, HTTPException, Header 
from database import SessionLocal, Base
from sqlalchemy.orm import Session

import schema
import models
import auth

user_route = APIRouter(
    prefix="/user"
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@user_route.post('/register')
def register(user : schema.Registration, db : Session = Depends(get_db)):
    exixting_user = db.query(models.User).filter(models.User.email == user.email).first()

    if exixting_user:
        raise HTTPException(status_code=400, detail="User already exist")
    
    new_user = models.User(
        username = user.username,
        email = user.email,
        mob_num = user.mob_num,
        password = auth.hashed_pass(user.password),
        date_of_birth = user.date_of_birth,
        role = "user",
        user_address = user.user_address
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message" : "Registration Successfull"}

@user_route.post("/login")
def login(user : schema.Login, db : Session = Depends(get_db)):
    user_email = db.query(models.User).filter(models.User.email == user.email).first()

    if not user_email:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_pass = auth.verify_pass(user.password, user_email.password)

    if not user_pass:
        raise HTTPException(status_code=400, detail="Invalid Password")
    
    access_token = auth.create_access_token(data = {
        "sub" : user_email.email,
        "role" : user_email.role
    })

    return {
        "message" : "Login Successfull",
        "access_token" : access_token,
        "token_type" : "bearer"
    }

def get_current_user(authorization: str = Header()):
    if not authorization:
        raise HTTPException(401, "Missing token")

    token = authorization.split(" ")[1]

    payload = auth.verify_token(token)

    return payload

@user_route.get('/profile')
def profile(current_user = Depends(get_current_user), db : Session = Depends(get_db)):
    if not current_user:
        raise HTTPException(status_code=400, detail="Missing token")
    
    # taking the email from payload
    email = current_user.get("sub")

    # fetch the user data based on email
    user = db.query(models.User).filter(models.User.email == email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User Not Found")

    return {
        "message" : "User fetch successfully",
        "current_user" : {
                "id" : user.id,
                "username" : user.username,
                "email" : user.email,
                "user_address" : user.user_address
            }
        }
   
@user_route.put("/update_profile")
def update_profile( user : schema.UpdateProfile ,current_user = Depends(get_current_user),db : Session = Depends(get_db)):
    
    email = current_user.get("sub")

    db_user = db.query(models.User).filter(models.User.email == email).first()

    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
    )

    db_user.username = user.username
    db_user.mob_num = user.mob_num 
    db_user.user_address = user.user_address

    db.commit()
    db.refresh(db_user)

    return{
        "message" : "User Update successfully",
        "user" : {
            "username" : db_user.username,
            "email" : db_user.email,
            "mob_num" : db_user.mob_num
        }
    }

@user_route.put("/change_password")
def change_password(user : schema.ChangePass, current_user = Depends(get_current_user), db : Session = Depends(get_db)):
    
    email = current_user.get("sub")

    db_user = db.query(models.User).filter(models.User.email == email).first()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not auth.verify_pass(user.old_password, db_user.password):
        raise HTTPException(
            status_code=400,
            detail="Current password is incorrect"
    )
    
    if auth.verify_pass(user.new_password, db_user.password):
        raise HTTPException(status_code=400, detail="New password must be different")

    db_user.password = auth.hashed_pass(user.new_password)

    db.commit()
    db.refresh(db_user)

    return {
        "message" : "Password Changed Successfully",
    }


