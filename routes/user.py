from fastapi import APIRouter, Depends, HTTPException, Header 
from database import SessionLocal, Base
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

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

    if user_email.is_active:
        raise HTTPException(status_code=403, detail="Account has been deleted")

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


@user_route.delete("/delete_account")
def detele_user_account(current_user = Depends(get_current_user), db : Session = Depends(get_db)):
    user_email =current_user.get("sub")
    
    db_user = db.query(models.User).filter(models.User.email == user_email).first()

    db_user.is_active = False

    db.commit()
    db.refresh(db_user)

    return {
        "message" : "User Deleted Sucessfully"
    }


@user_route.get("/requests")
def get_all_return_replace_order(current_user = Depends(get_current_user), db : Session = Depends(get_db)):
    user_email = current_user.get("sub")

    db_user = db.query(models.User).filter(models.User.email == user_email).first()

    result = (
        db.query(
            models.Returns.id.label("return_id"),
            models.User.id.label("user_id"),
            models.Returns.order_id,
            models.Returns.type,
            models.Returns.reason,
            models.Returns.status          
        ).join(
            models.User,
            models.Returns.user_id == models.User.id
        ).filter(
            models.Returns.user_id == db_user.id
            ).all()
    ) 

    order_details_list = []
    for item in result:
        order_details_list.append({
            "return ID" : item.return_id,
            "User_id" : item.user_id,
            "Order_ID" : item.order_id,
            "Type" : item.type,
            "Reason" : item.reason,
            "Status" : item.status
        })

    return {
        "message" : "Order Details",
        "Order Details" : order_details_list
    }


@user_route.post("/reviews")
def user_reviews(review : schema.Reviews, current_user = Depends(get_current_user), db : Session = Depends(get_db)):
    user_email = current_user.get("sub")

    db_user = db.query(models.User).filter(models.User.email == user_email).first()

    db_order = db.query(models.Order)\
        .filter(
            and_(models.Order.user_id == db_user.id,
                models.Order.id == review.order_id
                )).first()

    if not db_order:
        raise HTTPException(status_code=404, detail="No Order found")

    if db_order.status != "Delevered":
        raise HTTPException(status_code=400, detail="Product is not delevered You can,t review it")
        
    db_orderItem = db.query(models.OrderItem)\
        .filter(
            and_(models.OrderItem.order_id == db_order.id,
                models.OrderItem.product_id == review.product_id
            )).first()
        
    if not db_orderItem:
        raise HTTPException(status_code=404, detail="No Order product found")

    new_review = models.Reviews(
        user_id = db_user.id,
        product_id = review.product_id,
        rating = review.rating,
        comment = review.comment
    )

    db_review = db.query(models.Reviews).filter(
        and_(models.Reviews.product_id == review.product_id,
        models.Reviews.user_id == db_user.id
        )).first()

    if db_review:
        raise HTTPException(status_code=400, detail="The Product already rated by this User")
    
    db.add(new_review)
    db.commit()
    db.refresh(new_review)

    return{
        "messsage" : "Rewiew added sucessfully"
    }
