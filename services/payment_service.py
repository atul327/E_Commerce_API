from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from utils.razorpay_client import client
from config import settings
from models import Payment, Order

async def create_payment(db: AsyncSession, order_id:int):

    # Find order
    existing_order = await db.get(Order, order_id)

    if not existing_order:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    # Create Razorpay order
    razorpay_order = client.order.create(
        {
            "amount":int(existing_order.total_amount * 100),
            "currency":"INR",
            "receipt":f"order_{existing_order.id}"
        }
    )

    # Save payment record
    new_payment = Payment(
        order_id=existing_order.id,
        gateway="Razorpay",
        gateway_order_id=razorpay_order["id"],
        amount=existing_order.total_amount,
        status="Pending"
    )

    db.add(new_payment)

    await db.commit()

    await db.refresh(new_payment)

    return {
        "razorpay_order_id": razorpay_order["id"],
        "amount":razorpay_order["amount"],
        "currency": "INR",
        "key": settings.RAZORPAY_KEY_ID

    }