from fastapi import APIRouter, Header, Depends, HTTPException, Path
from database import SessionLocal
from sqlalchemy.orm import Session 
from sqlalchemy import or_, and_

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
        status = "Pending",
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

    # use join to fetch 3 table data 
    result = (
        db.query(
            models.Order.id,
            models.Order.user_id,
            models.Product.name,
            models.OrderItem.quantity,
            models.OrderItem.price
        )
        # Join OrderItem Table to Order Table
        .join(
            models.OrderItem,  #isme orderItem table ko order table se join krr rhe
            models.Order.id == models.OrderItem.order_id
        )
        # join the product table to OrderItem table 
        .join(
            models.Product,
            models.OrderItem.product_id == models.Product.id
        )
        # Get only current user data
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

@order_route.get("/order_details")
def order_details(current_user = Depends(get_current_user), db : Session = Depends(get_db)):
    user_email = current_user.get("sub")

    db_user = db.query(models.User).filter(models.User.email == user_email).first()

    result = (
        db.query(
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
        .filter(models.Order.user_id == db_user.id).all() 
    )

    order_details_list = []
    for item in result:
        order_details_list.append({
            "Order_id" : item.id,
            "Product_name" : item.name,
            "Quantity" : item.quantity,
            "Price" : item.price,
            "Payment_Method" : item.payment_method,
            "Total price" : item.subtotal,
            "Cteated time": item.created_at,
            "Status" : item.status
        }) 

    return {
        "message" : "Order Details",
        "Order Details" : order_details_list
    }


@order_route.put("/cancel/{p_id}")
def order_cancel(p_id : int = Path(), current_user = Depends(get_current_user), db : Session = Depends(get_db)):
    user_email = current_user.get("sub")

    db_user = db.query(models.User).filter(models.User.email == user_email).first()

    db_product = db.query(models.Product).filter(models.Product.id == p_id).first()

    if not db_product:
        raise HTTPException(status_code=403, detail="Product not found")
    
    db_orderItem = db.query(models.OrderItem).filter(models.OrderItem.product_id == db_product.id).first()

    if not db_orderItem:
        raise HTTPException(status_code=403, detail="Order not found")

    db_order = db.query(models.Order).filter(
        and_(
            models.Order.id == db_orderItem.order_id,
            models.Order.user_id == db_user.id
        )).first()

    if db_orderItem.product_id == p_id and db_order.status in ["Pending", "Shipped", "Processing", "Confirm"]:
        db_order.status = "Cancelled"

    db.commit()
    db.refresh(db_order)

    return{
        "message" : "Order is cancelled",
        "cancelled Order" : db_product.name
    }

@order_route.get("/all")
def fetch_all_order(current_user = Depends(get_current_user), db : Session = Depends(get_db)):
    user_email = current_user.get("sub")

    db_user = db.query(models.User).filter(models.User.email == user_email).first()

    if db_user.role != "admin":
        raise HTTPException(status_code=403, detail="User cant see all order")    

    db_orderItem = db.query(models.OrderItem).all()

    return {
        "message" : "All order details",
        "orders" : db_orderItem
    }

@order_route.put("/update_status/{order_id}")
def update_order_status(order_status : schema.UpdateStatus, order_id : int, current_user = Depends(get_current_user), db : Session = Depends(get_db)):
    user_email = current_user.get("sub")

    db_user = db.query(models.User).filter(models.User.email == user_email).first()

    if db_user.role != "admin":
        raise HTTPException(status_code=403, detail="User can't update the status")
    
    db_order = db.query(models.Order).filter(models.Order.id == order_id).first()

    if not db_order:
        raise HTTPException(status_code=403, detail="Order not found")

    if db_order.status == "Pending":
        db_order.status = "Processing"

    elif db_order.status == "Processing":
        db_order.status = "Shipped"

    elif db_order.status == "Shipped":
        db_order.status = "Delevered"

    else:
        raise HTTPException(
            status_code=400,
            detail="Order cannot be updated further"
        )
    
    db.commit()
    db.refresh(db_order)

    return {
        "message" : "Order status is updated",
        "order_id" : order_id,
        "order_status" : db_order.status
    }


            
