from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

import models


async def checkout(db : AsyncSession, user_details : models.User):

    try:

        # get cart
        result = await db.execute(
            select(models.Cart)
            .options(joinedload(models.Cart.product))
            .where(models.Cart.user_id == user_details.id)
        )

        db_cart = result.scalars().all()

        if not db_cart:
            raise HTTPException(
                status_code=404,
                detail="Cart is empty"
            )


        total_amount = 0
        
        # Check stock and calculate total amount
        for item in db_cart:

            if item.product.stock < item.quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"{item.product.name} has only {item.product.stock} item(s) in stock."
                )

            total_amount += item.quantity * item.product.price

        # create Order
        order = models.Order(
            user_id = user_details.id,
            total_amount = total_amount,
            status = "Pending",
            payment_method = "COD",  # Later replace with user-selected payment method
            user_address = user_details.user_address
        )

        db.add(order)

        await db.flush()

        # Create Order Items & Reduce Stock
        for item in db_cart:

            sub_total = item.quantity * item.product.price


            new_order_item = models.OrderItem(
                order_id=order.id,
                product_id=item.product.id,
                quantity=item.quantity,
                price=item.product.price,
                subtotal=sub_total
            )

            db.add(new_order_item)

            # Reduce stock
            item.product.stock -= item.quantity

        # Clear Cart
        for item in db_cart:
            await db.delete(item)

        await db.commit()

        return {
        "message": "Checkout Successful",
        "order_id": order.id,
        "total_amount": total_amount,
        "status": order.status
        }

    except HTTPException:
        await db.rollback()
        raise

    except Exception:
        await db.rollback()
        raise


# Buy Now
async def buy_now(db: AsyncSession, data, p_id, user):
    try:
        result = await db.execute(
            select(models.Product).where(
                models.Product.id == p_id
            )
        )

        db_product = result.scalar_one_or_none()

        if not db_product:
            raise HTTPException(404, "No product available")
        
        if db_product.stock < data.quantity:
            raise HTTPException(
                400,
                "Insufficient stock"
            )
        
        total_amount = db_product.price * data.quantity

        new_order = models.Order(
            user_id = user.id,
            total_amount = total_amount,
            status = "Pending",
            payment_method = data.payment_method,
            user_address = user.user_address
        )

        db.add(new_order)

        await db.flush()

        new_order_item = models.OrderItem(
            order_id = new_order.id,
            product_id = db_product.id,
            quantity = data.quantity,
            price = db_product.price,
            subtotal = total_amount
        )

        db.add(new_order_item)

        db_product.stock -= data.quantity

        await db.commit()


        return {
            "message":"Order placed successfully",
            "order_id":new_order.id,
            "total_amount":total_amount
        }

    except HTTPException:
        await db.rollback()
        raise

    except Exception:
        await db.rollback()
        raise