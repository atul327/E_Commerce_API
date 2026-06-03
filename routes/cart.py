from fastapi import APIRouter, Depends, HTTPException, Header, Path
from database import SessionLocal
from sqlalchemy.orm import Session

import schema
import auth
import models


cart_route = APIRouter(
    prefix="/cart" 
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(authorization : str = Header()):
    if not authorization:
        raise HTTPException(status_code=403, detail="Missing Token")
    
    token = authorization.split(" ")[1]

    payload = auth.verify_token(token)

    return payload

@cart_route.post("/add")
def add_to_cart(cart : schema.AddToCart, current_user = Depends(get_current_user), db : Session = Depends(get_db)):
    user_email = current_user.get("sub")

    # to find out the user_id from User table
    db_user = db.query(models.User).filter(models.User.email == user_email).first()

    user_id = db_user.id

    if user_id != cart.user_id:
        raise HTTPException(status_code=404, detail="User not found")

    # to find out the product_id from the Products Table
    db_product = db.query(models.Product).filter(models.Product.id == cart.product_id).first()

    product_id = db_product.id

    if not product_id:
        raise HTTPException(status_code=404, detail="Product not found")
    
    new_cart = models.Cart(
        user_id = user_id,
        product_id = product_id,
        quantity = cart.quantity
    )

    db.add(new_cart)
    db.commit()
    db.refresh(new_cart)

    return {
        "message" : "Product is added to cart"
    }

@cart_route.put("/update")
def update_cart(cart : schema.UpdateCart, current_user = Depends(get_current_user), db : Session = Depends(get_db)):
    user_email = current_user.get("sub")

    db_user = db.query(models.User).filter(models.User.email == user_email).first()

    user_id = db_user.id 

    cart_id = db.query(models.Cart).filter(models.Cart.user_id == user_id).first()

    cart_id.quantity = cart.quantity

    db.commit()
    db.refresh(cart_id)

    return {
        "message" : "Cart Update sucessfully",
        "cart_product" : cart_id
    }
    

@cart_route.delete("/remove/{p_id}")
def remove_cart(p_id : int = Path(example="1"), current_user = Depends(get_current_user), db : Session = Depends(get_db)):
    user_email = current_user.get("sub")

    db_user = db.query(models.User).filter(models.User.email == user_email).first()

    user_id = db_user.id

    db_product = db.query(models.Cart).filter(models.Cart.user_id == user_id).first()

    pro_id = db_product.product_id

    if pro_id != p_id:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # user ki kitne product cart me available hai 
    cart_item = db.query(models.Cart).filter(models.Cart.user_id == user_id).filter()
    
    db_cart = db.query(models.Cart).filter(models.Cart.product_id == pro_id).first()

    cart_id = db_cart.product_id

    if  cart_id != p_id:
        raise HTTPException(status_code=404, detail="Cart Product not found")
    
    db.delete(db_cart)
    db.commit()

    return {
        "message" : "Product removed from Cart",
    }


@cart_route.get("/view")
def view_cart(current_user = Depends(get_current_user), db : Session = Depends(get_db)):
    user_email = current_user.get("sub")

    db_user = db.query(models.User).filter(models.User.email == user_email).first()

    user_id = db_user.id 

    cart_item = db.query(models.Cart).all()

    if not cart_item:
        raise HTTPException(403, "User Not found")

    return {
        "message" : "Cart Item fetched",
        "Cart Item" : cart_item
    }

