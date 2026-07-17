from fastapi import APIRouter, Depends, HTTPException, Header, Path
from database import AsyncSessionLocal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

import schema
import auth
import models


cart_route = APIRouter(
    prefix="/cart" 
)

async def get_db():
    async with AsyncSessionLocal() as db:
        yield db
        
# request the token from header and verify it
def get_current_user(authorization : str = Header()):
    if not authorization:
        raise HTTPException(status_code=403, detail="Missing Token")
    
    token = authorization.split(" ")[1]

    payload = auth.verify_token(token)

    return payload


@cart_route.post("/add")
async def add_to_cart(cart : schema.AddToCart, current_user = Depends(get_current_user), db : AsyncSession = Depends(get_db)):

    user_email = current_user.get("sub")

    # to find out the user_id from User table
    result = await db.execute(
        select(models.User).where(
            models.User.email == user_email
        )
    )

    db_user = result.scalar_one_or_none()

    # user_id = db_user.id

    if  not db_user:
        raise HTTPException(status_code=404, detail="User not found")


    # to find out the product_id from the Products Table
    result = await db.execute(
        select(models.Product).where(
            models.Product.id == cart.product_id
        )
    )

    db_product = result.scalar_one_or_none()

    product_id = db_product.id

    if not product_id:
        raise HTTPException(status_code=404, detail="Product not found")
    

    new_cart = models.Cart(
        user_id = db_user.id,
        product_id = product_id,
        quantity = cart.quantity
    )


    db.add(new_cart)

    await db.commit()

    await db.refresh(new_cart)


    return {
        "message" : "Product is added to cart"
    }

# have to work on this
@cart_route.put("/update")
async def update_cart(cart : schema.UpdateCart, current_user = Depends(get_current_user), db : AsyncSession = Depends(get_db)):

    user_email = current_user.get("sub")

    result = await db.execute(
        select(models.User).where(
            models.User.email == user_email
        )
    )

    db_user = result.scalar_one_or_none()

    user_id = db_user.id 


    result = await db.execute(
        select(models.Cart).where(
            models.Cart.user_id == user_id,
            models.Cart.product_id == cart.product_id
        )
    )

    cart_id = result.scalar_one_or_none()


    if not cart_id:
        raise HTTPException(
            status_code=404,
            detail="Cart item not found"
        )
    

    cart_id.quantity = cart.quantity

    await db.commit()

    await db.refresh(cart_id)


    return {
        "message" : "Cart Update sucessfully",
        "cart_product" : {
            "Product name" : cart_id.product.name
        }
    }
    

@cart_route.delete("/remove/{p_id}")
async def remove_cart(p_id : int = Path(example="1"), current_user = Depends(get_current_user), db : AsyncSession = Depends(get_db)):

    user_email = current_user.get("sub")


    result = await db.execute(
        select(models.User).where(
            models.User.email == user_email
        )
    )

    db_user = result.scalar_one_or_none()

    user_id = db_user.id


    result = await db.execute(
        select(models.Cart).where(
            models.Cart.user_id == user_id,
            models.Cart.product_id == p_id
        )
    )

    db_cart = result.scalar_one_or_none()


    if not db_cart:
        raise HTTPException(404, "Product not found in cart")


    await db.delete(db_cart)

    await db.commit()


    return {
        "message" : "Product removed from Cart",
    }
@cart_route.get("/view")
async def view_cart(current_user = Depends(get_current_user), db : AsyncSession = Depends(get_db)):

    user_email = current_user.get("sub")


    result = await db.execute(
        select(models.User).where(
            models.User.email == user_email
        )
    )

    db_user = result.scalar_one_or_none()


    user_id = db_user.id 


    result = await db.execute(
        select(models.Cart)
        .options(selectinload(models.Cart.product))
        .where(
            models.Cart.user_id == user_id
        )
    )

    db_cart = result.scalars().all()


    if len(db_cart) == 0:
        return {
            "message": "Cart is empty",
            "cart_items": []
        }


    cart_items = []


    for item in db_cart:

        cart_items.append({
            "product_id": item.product_id,
            "product_name": item.product.name if item.product else None,
            "price": item.product.price if item.product else None,
            "quantity": item.quantity,
            "total": (item.product.price * item.quantity) if item.product else 0
        })


    return {
        "message" : "Cart Item fetched",
        "Cart Item" : cart_items
    }