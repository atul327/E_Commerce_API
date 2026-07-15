from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from services.payment_service import create_payment
from database import AsyncSessionLocal

payment_router = APIRouter(
    prefix="/payment",
    tags=["Payment"]
)

async def get_db():
    async with AsyncSessionLocal() as db:
        yield db

@payment_router.post("/create/{order_id}")
async def create_payment_api(order_id:int, db:AsyncSession = Depends(get_db)):

    return await create_payment(db, order_id)