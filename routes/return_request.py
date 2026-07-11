from fastapi import FastAPI, HTTPException, Path, Header, APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import AsyncSessionLocal

import models
import auth
import schema


admin_route = APIRouter(
    prefix="/admin"
)


# access the database to perform operations
async def get_db():
    async with AsyncSessionLocal() as db:
        yield db



# verify the token and get the user data
def get_current_user(authourization: str = Header()):

    if not authourization:
        raise HTTPException(
            status_code=400,
            detail="Missing Token"
        )
    
    token = authourization.split(" ")[1]

    payload = auth.verify_token(token)

    return payload



@admin_route.patch("/requests/{request_id}")
async def update_return_order_status(
        request_id: int = Path(),
        current_user = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):

    user_email = current_user.get("sub")


    db_user = await db.execute(
        select(models.User).filter(
            models.User.email == user_email
        )
    )

    db_user = db_user.scalar_one_or_none()


    if db_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="User can't perform update operation"
        )


    db_return = await db.execute(
        select(models.Returns).filter(
            models.Returns.id == request_id
        )
    )

    db_return = db_return.scalar_one_or_none()


    if not db_return:
        raise HTTPException(
            404,
            "No return order found"
        )


    if db_return.status == "Request":
        db_return.status = "Approve"

    elif db_return.status == "Approve":
        db_return.status = "Completed"

    elif db_return.status == "Completed":
        raise HTTPException(
            status_code=403,
            detail="Return process already completed for this product"
        )


    await db.commit()

    await db.refresh(db_return)


    return {
        "message": "The order status updated",
        "status": db_return.status
    }