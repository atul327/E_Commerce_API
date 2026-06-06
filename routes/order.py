from fastapi import APIRouter, Header, Depends, HTTPException
from database import SessionLocal
from sqlalchemy.orm import Session 

import models
import schema
import auth
import routes.user

order_route = APIRouter(
    prefix= "/order"
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(authorization : str = Header()):
    if not authorization:
        raise HTTPException(status_code=403, detail = "Missing token")

    token = authorization.split(" ")[1]
    
    payload = auth.verify_token(token)

    return payload

@order_route.post("/place")
def place_order(order : schema.Order, current_user = Depends(get_current_user), db : Session = Depends(get_db)):

    user_email = current_user.get("sub")

    db_user = db.query(models.User).filter(models.User.email == user_email).first()

    user_id = db_user.id

    if user_id != order.user_id:
        raise HTTPException(status_code=404, detail = "User Not Found")
    

    cart_item = db.query(models.Cart).filter(models.Cart.user_id == user_id).first()
    
    if not cart_item:
        raise HTTPException(
            status_code=404,
            detail="Cart is empty"
        )
    
    db_product = db.query(models.Product).filter(models.Product.id == cart_item.product_id).first()

    total_amount = cart_item.quantity * db_product.price

    new_order = models.Order(
        user_id = user_id,
        total_amount = total_amount,
        status = "Processing",
        payment_method = order.payment_method,
        user_address = db_user.user_address
    )

    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    return {
        "message" : "Order Placed",
        "order_details" : new_order
    }


@order_route.post("/orderitem")
def order_item(current_user = Depends(get_current_user), db : Session = Depends(get_db)):
    user_email = current_user.get("sub")

    db_user = db.query(models.User).filter(models.User.email == user_email).first()
    user_id = db_user.id  

    if not user_id:
        raise HTTPException(status_code=404, detail="User not found")

    db_cart = db.query(models.Cart).filter(models.Cart.user_id == user_id).first()

    if not db_cart:
        raise HTTPException(status_code=403, detail="Cart Product not found")

    db_product = db.query(models.Product).filter(models.Product.id == db_cart.product_id).first()

    db_order = db.query(models.Order).filter(models.Order.user_id == user_id).first()

    if not db_order:
        raise HTTPException(status_code=403, detail="User order not found")

    sub_total = db_cart.quantity * db_product.price

    new_order_item = models.OrderItem(
        order_id = db_order.id,
        product_id = db_cart.product_id,
        quantity = db_cart.quantity,
        price = db_product.price,
        subtotal = sub_total
    )

    db.add(new_order_item)
    db.commit()
    db.refresh(new_order_item)

    return {
        "message" : "Order Item added successfully",
        "order_item" : new_order_item
    }

# route for the showing User order details
@order_route.get("/myorder")
def my_order(current_user = Depends(get_current_user), db : Session = Depends(get_db)):

    # for getting the current login use email
    user_email = current_user.get("sub")

    # getting the current login User Data using email
    db_user = db.query(models.User).filter(models.User.email == user_email).first()

    # fetching the login user order using user_id
    result = (
        db.query(
            models.Order.id,
            models.Order.user_id,
            models.Product.name,
            models.OrderItem.quantity,
            models.OrderItem.price
        )
        .join(
            models.OrderItem,  #isme orderItem table ko order table se join krr rhe
            models.Order.id == models.OrderItem.order_id
        )
        .join(
            models.Product,
            models.OrderItem.product_id == models.Product.id
        )
        .filter(models.Order.user_id == db_user.id).all()
    )

    my_order = []
    # .all() return the list so to return the data need for loop
    for item in result:
        my_order.append({
            "order_id" : item.id,
            "user_id" : item.user_id,
            "product_name" : item.name,
            "Quantity" : item.quantity,
            "price" : item.price
            })
        
    if len(my_order) == 0:
        raise HTTPException(404, "No order details found")

    return {
        "message" : "Oredr Details",
        "myorder" : my_order
    }



