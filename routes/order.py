from fastapi import APIRouter, Header, Depends, HTTPException, Path
from database import AsyncSessionLocal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from sqlalchemy.orm import joinedload, selectinload

from services.order_service import checkout

import models
import schema
import auth
import routes.user

import services.order_service

order_route = APIRouter(
    prefix="/order"
)

async def get_db():
    async with AsyncSessionLocal() as db:
        yield db

# To get and verify the user
def get_current_user(authorization: str = Header()):
    if not authorization:
        raise HTTPException(status_code=403, detail="Missing token")

    token = authorization.split(" ")[1]
    
    payload = auth.verify_token(token)

    return payload


@order_route.post("/place")
async def place_order(order: schema.Order, current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):

    user_email = current_user.get("sub")

    result = await db.execute(
        select(models.User).where(
            models.User.email == user_email
        )
    )

    db_user = result.scalar_one_or_none()

    # user_id = db_user.id

    try:

        # use joinload for improving the efficiency and response
        # joinload first take the all data from database then perform operation on it

        result = await db.execute(
            select(models.Cart)
            .options(joinedload(models.Cart.product))
            .where(models.Cart.user_id == db_user.id)
        )

        db_cart = result.scalars().all()

        if not db_cart:
            raise HTTPException(
                status_code=404,
                detail="Cart is empty"
            )

        total_amount = 0

        for item in db_cart:

            total = item.quantity * item.product.price
            total_amount += total


        new_order = models.Order(
            user_id=db_user.id,
            total_amount=total_amount,
            status="Pending",
            payment_method=order.payment_method,
            user_address=db_user.user_address
        )

        db.add(new_order)

        await db.flush()

        await db.refresh(new_order)


        for item in db_cart:

            result = await db.execute(
                select(models.Product).where(
                    models.Product.id == item.product_id
                )
            )

            db_product = result.scalar_one_or_none()

            if not db_product:
                raise HTTPException(
                    404,
                    "Product not found"
                )

            sub_total = item.quantity * db_product.price

            # Update Stock
            db_product.stock -= item.quantity

            if db_product.stock < item.quantity:
                raise HTTPException(
                    status_code=400,
                    detail="Insufficient stock"
                )

            new_order_item = models.OrderItem(
                order_id=new_order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                price=db_product.price,
                subtotal=sub_total
            )

            db.add(new_order_item)


        for item in db_cart:
            await db.delete(item)


        await db.commit()

        return {
            "message": "Order Placed",
            "Status": new_order.status,
            "order_details": new_order
        }

    except HTTPException:
        await db.rollback()
        raise 

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error"
        )


# route for the showing User order details
@order_route.get("/myorder")
async def my_order(current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):

    # for getting the current login use email
    user_email = current_user.get("sub")

    # getting the current login User Data using email

    result = await db.execute(
        select(models.User).where(
            models.User.email == user_email
        )
    )

    db_user = result.scalar_one_or_none()


    result = await db.execute(
        select(
            models.Order.id,
            models.Order.user_id,
            models.Product.name,
            models.OrderItem.quantity,
            models.OrderItem.price
        )
        .join(
            models.OrderItem,
            models.Order.id == models.OrderItem.order_id
        )
        .join(
            models.Product,
            models.OrderItem.product_id == models.Product.id
        )
        .where(
            models.Order.user_id == db_user.id
        )
    )

    result = result.all()

    my_order = []

    for item in result:
        my_order.append({
            "order_id": item.id,
            "user_id": item.user_id,
            "product_name": item.name,
            "Quantity": item.quantity,
            "price": item.price
        })

    if len(my_order) == 0:
        raise HTTPException(404, "No order details found")

    return {
        "message": "Oredr Details",
        "myorder": my_order
    }
@order_route.get("/order_details")
async def order_details(current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):

    user_email = current_user.get("sub")

    result = await db.execute(
        select(models.User).where(
            models.User.email == user_email
        )
    )

    db_user = result.scalar_one_or_none()


    result = await db.execute(
        select(
            models.Order.id,
            models.Product.name,
            models.OrderItem.quantity,
            models.OrderItem.price,
            models.Order.payment_method,
            models.OrderItem.subtotal,
            models.Order.created_at,
            models.Order.status
        )
        .join(
            models.OrderItem,
            models.Order.id == models.OrderItem.order_id
        )
        .join(
            models.Product,
            models.OrderItem.product_id == models.Product.id
        )
        .where(
            models.Order.user_id == db_user.id
        )
    )

    result = result.all()

    order_details_list = []

    for item in result:
        order_details_list.append({
            "Order_id": item.id,
            "Product_name": item.name,
            "Quantity": item.quantity,
            "Price": item.price,
            "Payment_Method": item.payment_method,
            "Total price": item.subtotal,
            "Cteated time": item.created_at,
            "Status": item.status
        })

    return {
        "message": "Order Details",
        "Order Details": order_details_list
    }


@order_route.put("/cancel/{order_id}")
async def cancel_order(order_id: int = Path(), current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):

    user_email = current_user.get("sub")

    result = await db.execute(
        select(models.User).where(
            models.User.email == user_email
        )
    )

    db_user = result.scalar_one_or_none()

    try:
        result = await db.execute(
            select(models.Order).where(
                models.Order.user_id == db_user.id,
                models.Order.id == order_id
            )
        )

        db_order = result.scalar_one_or_none()

        if not db_order:
            raise HTTPException(status_code=403, detail="Order not found")

        result = await db.execute(
            select(models.Order).where(
                models.Order.id == order_id,
                models.Order.status == "Cancelled"
            )
        )

        existing_status = result.scalar_one_or_none()

        if existing_status:
            raise HTTPException(
                status_code=403,
                detail=f"Order is already {db_order.status}"
            )

        db_order.status = "Cancelled"

        result = await db.execute(
            select(models.OrderItem).where(
                models.OrderItem.order_id == db_order.id
            )
        )

        db_order_item = result.scalars().all()

        for item in db_order_item:

            result = await db.execute(
                select(models.Product).where(
                    models.Product.id == item.product_id
                )
            )

            db_product = result.scalar_one_or_none()

            db_product.stock += item.quantity

        await db.commit()

        await db.refresh(db_order)


        return {
            "message": "Order cancelled",
            "order_id": db_order.id,
            "Status": db_order.status
        }

    except HTTPException:
        await db.rollback()
        raise 

    except Exception as e:
        await db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Internal Server Error"
        )

@order_route.get("/all")
async def fetch_all_order(current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):

    user_email = current_user.get("sub")

    result = await db.execute(
        select(models.User).where(
            models.User.email == user_email
        )
    )

    db_user = result.scalar_one_or_none()

    if db_user.role != "admin":
        raise HTTPException(status_code=403, detail="User cant see all order")    

    result = await db.execute(
        select(models.OrderItem)
    )

    db_orderItem = result.scalars().all()

    return {
        "message": "All order details",
        "orders": db_orderItem
    }


@order_route.put("/update_status/{order_id}")
async def update_order_status(order_status: schema.UpdateStatus,
                              order_id: int,
                              current_user=Depends(get_current_user),
                              db: AsyncSession = Depends(get_db)):

    user_email = current_user.get("sub")

    result = await db.execute(
        select(models.User).where(
            models.User.email == user_email
        )
    )

    db_user = result.scalar_one_or_none()

    if db_user.role != "admin":
        raise HTTPException(status_code=403, detail="User can't update the status")

    try: 
        result = await db.execute(
            select(models.Order).where(
                models.Order.id == order_id
            )
        )

        db_order = result.scalar_one_or_none()

        if not db_order:
            raise HTTPException(status_code=404, detail="Order not found")

        result = await db.execute(
            select(models.OrderItem).where(
                models.OrderItem.order_id == db_order.id
            )
        )

        db_orderitems = result.scalars().all()

        if db_order.status == "Pending":
            for item in db_orderitems:
                result = await db.execute(
                    select(models.Product).where(
                        models.Product.id == item.product_id
                    )
                )

                db_product = result.scalar_one_or_none()

                # if db_product.stock < item.quantity:
                #     raise HTTPException(400, "Insufficient stock")

                # db_product.stock -= item.quantity

            db_order.status = "Processing"

        elif db_order.status == "Processing":
            db_order.status = "Shipped"

        elif db_order.status == "Shipped":
            db_order.status = "Delevered"

        else:
            raise HTTPException(
                status_code=400,
                detail="Order is delevered and cannot be updated further"
            )

        await db.commit()
        await db.refresh(db_order)

        return {
            "message": "Order status is updated",
            "order_id": order_id,
            "order_status": db_order.status
        }

    except HTTPException:
        await db.rollback()
        raise 

    except Exception as e:
        await db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Internal Server Error"
        )
    

@order_route.post("/returns")
async def return_order(ret: schema.OrderReturn, current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):

    user_email = current_user.get("sub")

    result = await db.execute(
        select(models.User).where(
            models.User.email == user_email
        )
    )

    db_user = result.scalar_one_or_none()

    try:

        result = await db.execute(
            select(models.Order).where(
                models.Order.id == ret.order_id,
                models.Order.user_id == db_user.id
            )
        )

        db_order = result.scalar_one_or_none()

        if not db_order:
            raise HTTPException(404, "Order not found")

        if db_order.status != "Delevered":
            raise HTTPException(403, "Order is not delevered yet")

        result = await db.execute(
            select(models.OrderItem).where(
                models.OrderItem.order_id == db_order.id,
                models.OrderItem.product_id == ret.product_id
            )
        )

        db_orderItem = result.scalar_one_or_none()

        if not db_orderItem:
            raise HTTPException(
                status_code=404,
                detail="Order items not found"
            )


        result = await db.execute(
            select(models.Returns).where(
                models.Returns.order_id == ret.order_id,
                models.Returns.product_id == ret.product_id
            )
        )

        existing_order = result.scalar_one_or_none()


        if existing_order:
            raise HTTPException(
                status_code=400,
                detail=f"{existing_order.type} request already exist"
            )


        return_order = models.Returns(
            user_id=db_order.user_id,
            order_id=db_order.id,
            product_id=db_orderItem.product_id,
            type="Return",
            reason=ret.reason.value
        )


        result = await db.execute(
            select(models.Product).where(
                models.Product.id == db_orderItem.product_id
            )
        )

        db_product = result.scalar_one_or_none()


        reason_list = ["Damaged product", "Defective"]


        if ret.reason.value not in reason_list:
            db_product.stock += db_orderItem.quantity


        db.add(return_order)

        await db.commit()

        await db.refresh(return_order)


        return {
            "message": "Order return Successfull",
            "data": {
                "order_id": db_orderItem.order_id,
                "product_id": db_orderItem.product_id
            }
        }


    except HTTPException:
        await db.rollback()
        raise 


    except Exception as e:
        await db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Internal Server Error"
        )


@order_route.post("/replace")
async def replace_order_item(ret: schema.OrderReplace, current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):

    user_email = current_user.get("sub")


    result = await db.execute(
        select(models.User).where(
            models.User.email == user_email
        )
    )

    db_user = result.scalar_one_or_none()


    result = await db.execute(
        select(models.Order).where(
            models.Order.user_id == db_user.id,
            models.Order.id == ret.order_id
        )
    )

    db_order = result.scalar_one_or_none()


    if not db_order:
        raise HTTPException(404, "Order not found")


    if db_order.status != "Delevered":
        raise HTTPException(403, "Order not delevered yet")


    result = await db.execute(
        select(models.OrderItem).where(
            models.OrderItem.order_id == db_order.id,
            models.OrderItem.product_id == ret.product_id
        )
    )

    db_orderItem = result.scalar_one_or_none()


    if not db_orderItem:
        raise HTTPException(
            status_code=404,
            detail="Order items not found"
        )


    result = await db.execute(
        select(models.Returns).where(
            models.Returns.order_id == ret.order_id,
            models.Returns.product_id == ret.product_id
        )
    )

    existing_order = result.scalar_one_or_none()


    if existing_order:
        raise HTTPException(
            status_code=400,
            detail="Replace request already exists"
        )


    replace_order = models.Returns(
        user_id=db_user.id,
        order_id=ret.order_id,
        product_id=db_orderItem.product_id,
        type="Replace",
        reason=ret.reason.value
    )


    db.add(replace_order)

    await db.commit()

    await db.refresh(replace_order)


    return {
        "message": "Order Replace success",
        "order_id": db_orderItem.order_id
    }

# this checkout endpoint is use for place_order with proper validation
@order_route.post("/checkout")
async def checkout_api(current_user = Depends(get_current_user), db : AsyncSession = Depends(get_db)):
    user_email = current_user.get("sub")

    result = await db.execute(
        select(models.User).where(
            models.User.email == user_email
        )
    )

    db_user = result.scalar_one_or_none()

    return await checkout(db, db_user)


# Buy now for the user can directly buy product without fetching the cart
@order_route.post('/buy_now/{p_id}')
async def buy_now_api(data : schema.BuyNow, p_id : int = Path(), current_user = Depends(get_current_user) ,db : AsyncSession = Depends(get_db)):
    user_email = current_user.get("sub")

    result = await db.execute(
        select(models.User).where(
            models.User.email == user_email
        )
    )

    db_user = result.scalar_one()

    return await services.order_service.buy_now(db, data, p_id, db_user)
