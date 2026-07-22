"""async non-blocking"""
from fastapi import APIRouter, Depends, HTTPException, Header, Path 
from database import AsyncSessionLocal, Base
from sqlalchemy import or_, and_, func, select

from sqlalchemy.ext.asyncio import AsyncSession

import schema
import models
import auth

user_route = APIRouter(
    prefix="/user"
)

async def get_db():
    async with AsyncSessionLocal() as db:
        yield db

@user_route.post('/register')
async def register(user : schema.Registration, db : AsyncSession = Depends(get_db)):
    # exixting_user = db.query(models.User).filter(models.User.email == user.email).first()

    # async non-blocking 
    result = await db.execute(
        select(models.User).where(
            models.User.email == user.email
        )
    )

    existing_user = result.scalar_one_or_none()

    if existing_user:
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
    await db.commit()
    await db.refresh(new_user)

    return {"message" : "Registration Successfull"}

@user_route.post("/login")
async def login(user : schema.Login, db : AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(models.User).where(
        models.User.email == user.email
        )
    )

    # user_email = db.query(models.User).filter(models.User.email == user.email).first()

    user_email = result.scalar_one_or_none()

    if not user_email:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if not user_email.is_active:
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
async def profile(current_user = Depends(get_current_user), db : AsyncSession = Depends(get_db)):
    if not current_user:
        raise HTTPException(status_code=400, detail="Missing token")
    
    # taking the email from payload
    email = current_user.get("sub")

    # fetch the user data based on email
    result = await db.execute(
        select(models.User).where(
            models.User.email == email
        )
    )
    # user = db.query(models.User).filter(models.User.email == email).first()

    user = result.scalar_one_or_none()

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
async def update_profile( user : schema.UpdateProfile ,current_user = Depends(get_current_user),db : AsyncSession = Depends(get_db)):
    
    email = current_user.get("sub")

    # db_user = db.query(models.User).filter(models.User.email == email).first()

    result = await db.execute(
        select(models.User).where(
            models.User.email == email
        )
    )

    db_user = result.scalar_one_or_none()

    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
    )

    db_user.username = user.username
    db_user.mob_num = user.mob_num 
    db_user.user_address = user.user_address

    await db.commit()
    await db.refresh(db_user)

    return{
        "message" : "User Update successfully",
        "user" : {
            "username" : db_user.username,
            "email" : db_user.email,
            "mob_num" : db_user.mob_num
        }
    }

@user_route.put("/change_password")
async def change_password(user : schema.ChangePass, current_user = Depends(get_current_user), db : AsyncSession = Depends(get_db)):
    
    email = current_user.get("sub")

    # db_user = db.query(models.User).filter(models.User.email == email).first()

    result = await db.execute(
        select(models.User).where(
            models.User.email == email
        )
    )

    db_user = result.scalar_one_or_none()

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

    await db.commit()
    await db.refresh(db_user)

    return {
        "message" : "Password Changed Successfully",
    }


@user_route.delete("/delete_account")
async def detele_user_account(current_user = Depends(get_current_user), db : AsyncSession = Depends(get_db)):
    user_email =current_user.get("sub")
    
    # db_user = db.query(models.User).filter(models.User.email == user_email).first()

    result = await db.execute(
        select(models.User).where(
            models.User.email == user_email
        )
    )

    db_user = result.scalar_one_or_none()

    db_user.is_active = False

    await db.commit()
    await db.refresh(db_user)

    return {
        "message" : "User Deleted Sucessfully"
    }


@user_route.get("/requests")
async def get_all_return_replace_order(current_user = Depends(get_current_user), db : AsyncSession = Depends(get_db)):
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
async def user_reviews(
    review: schema.Reviews,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user_email = current_user.get("sub")

    # Fetch User
    result = await db.execute(
        select(models.User).where(
            models.User.email == user_email
        )
    )

    db_user = result.scalar_one_or_none()

    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # Fetch Order
    result = await db.execute(
        select(models.Order).where(
            and_(
                models.Order.user_id == db_user.id,
                models.Order.id == review.order_id
            )
        )
    )

    db_order = result.scalar_one_or_none()

    if not db_order:
        raise HTTPException(
            status_code=404,
            detail="No Order found"
        )

    if db_order.status != "Delivered":
        raise HTTPException(
            status_code=400,
            detail="Product is not delivered. You can't review it."
        )

    # Fetch Order Item
    result = await db.execute(
        select(models.OrderItem).where(
            and_(
                models.OrderItem.order_id == db_order.id,
                models.OrderItem.product_id == review.product_id
            )
        )
    )

    db_order_item = result.scalar_one_or_none()

    if not db_order_item:
        raise HTTPException(
            status_code=404,
            detail="No Order Product found"
        )

    # Check existing review
    result = await db.execute(
        select(models.Reviews).where(
            and_(
                models.Reviews.product_id == review.product_id,
                models.Reviews.user_id == db_user.id
            )
        )
    )

    db_review = result.scalar_one_or_none()

    if db_review:
        raise HTTPException(
            status_code=400,
            detail="The Product already rated by this User"
        )

    # Create Review
    new_review = models.Reviews(
        user_id=db_user.id,
        product_id=review.product_id,
        rating=review.rating,
        comment=review.comment
    )

    db.add(new_review)

    await db.commit()
    await db.refresh(new_review)

    return {
        "message": "Review added successfully"
    }


@user_route.get("/reviews/{product_id}")
async def get_reviews(
    product_id: int = Path(),
    db: AsyncSession = Depends(get_db)
):

    # Fetch all reviews
    result = await db.execute(
        select(models.Reviews).where(
            models.Reviews.product_id == product_id
        )
    )

    db_review = result.scalars().all()

    if not db_review:
        raise HTTPException(
            status_code=404,
            detail="No Product Review Found"
        )

    # Calculate average rating
    result = await db.execute(
        select(func.avg(models.Reviews.rating)).where(
            models.Reviews.product_id == product_id
        )
    )

    avg_rating = result.scalar()

    return {
        "message": "Fetch Success",
        "Review": db_review,
        "Rating average": avg_rating
    }

