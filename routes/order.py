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

# To get and verify the user
def get_current_user(authorization : str = Header()):
    if not authorization:
        raise HTTPException(status_code=403, detail = "Missing token")

    token = authorization.split(" ")[1]
    
    payload = auth.verify_token(token)

    return payload

# 
@order_route.post("/place")
def place_order(order : schema.Order, current_user = Depends(get_current_user), db : Session = Depends(get_db)):

    user_email = current_user.get("sub")

    db_user = db.query(models.User).filter(models.User.email == user_email).first()

    user_id = db_user.id
    
    db_cart = db.query(models.Cart).filter(models.Cart.user_id == user_id).all()
    
    if not db_cart:
        raise HTTPException(
            status_code=404,
            detail="Cart is empty"
        )
    
    total_amount = 0

    for item in db_cart: 
        db_product = db.query(models.Product).filter(models.Product.id == item.product_id).first()

        total = item.quantity * db_product.price
        total_amount += total

    new_order = models.Order(
        user_id = user_id,
        total_amount = total_amount,
        status = "Pending",
        payment_method = order.payment_method,
        user_address = db_user.user_address
    )

    db.add(new_order)

    # order_by is used to find the the latest order_id from the order table
    db_order = db.query(models.Order)\
        .filter(models.Order.user_id == user_id)\
        .order_by(models.Order.id.desc())\
        .first()
    
    if not db_order:
        raise HTTPException(status_code=404, detail="User order not found")
    
    for item in db_cart:
        db_product = db.query(models.Product).filter(models.Product.id == item.product_id).first()

        if not db_product:
            raise HTTPException(
                404,
                "Product not found"
            )
        
        sub_total = item.quantity * db_product.price

        new_order_item = models.OrderItem(
            order_id = db_order.id,
            product_id = item.product_id,
            quantity = item.quantity,
            price = db_product.price,
            subtotal = sub_total
        )


        db.add(new_order_item)


    db.commit()
    db.refresh(new_order)

    # taki user duplicate cart use na krr ske
    for item in db_cart:
        db.delete(item)

    db.commit()
    db.refresh(new_order_item)

    return {
        "message" : "Order Placed",
        "Status" : db_order.status,
        "order_details" : new_order
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

@order_route.put("/cancel/{order_id}")
def cancel_order(order_id : int = Path(), current_user = Depends(get_current_user), db : Session = Depends(get_db)):
    user_email = current_user.get("sub")

    db_user = db.query(models.User).filter(models.User.email == user_email).first()

    db_order = db.query(models.Order).filter(
            models.Order.user_id == db_user.id,
            models.Order.id == order_id).first()
    
    if not db_order:
        raise HTTPException(status_code=403, detail="Order not found")
    
    existing_status = db.query(models.Order).filter(
        models.Order.id == order_id,
        models.Order.status == "Cancelled"
    ).first()

    if existing_status:
        raise HTTPException(status_code=403, detail = f"Order is already {db_order.status}")
    
    db_order.status = "Cancelled"

    db.commit()
    db.refresh(db_order)

    return {
        "message" : "Order cancelled",
        "order_id" : db_order.id,
        "Status" : db_order.status
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
            detail="Order is delevered and cannot be updated further"
        )
    
    db.commit()
    db.refresh(db_order)

    return {
        "message" : "Order status is updated",
        "order_id" : order_id,
        "order_status" : db_order.status
    }


@order_route.post("/returns")
def return_order(ret : schema.OrderReturn, current_user = Depends(get_current_user), db : Session = Depends(get_db)):
    user_email = current_user.get("sub")

    db_user = db.query(models.User).filter(models.User.email == user_email).first()

    db_order = db.query(models.Order).filter(
                            models.Order.id == ret.order_id,
                            models.Order.user_id == db_user.id
                        ).first()

    if not db_order:
        raise HTTPException(404, "Order not found")

    if db_order.status != "Delevered":
        raise HTTPException(403, "Order is not delevered yet")
    
    db_orderItem = db.query(models.OrderItem).filter(
        models.OrderItem.order_id == db_order.id,
        models.OrderItem.product_id == ret.product_id).first()    

    if not db_orderItem:
        raise HTTPException(
            status_code=404,
            detail="Order items not found"
        )
        
    existing_order = db.query(models.Returns).filter(
        models.Returns.order_id == ret.order_id,
        models.Returns.product_id == ret.product_id,
    ).first()

    if existing_order:
        raise HTTPException(status_code=400, detail=f"{existing_order.type} request already exist")
          
        
    return_order = models.Returns(
        user_id=db_order.user_id,
        order_id=db_order.id,
        product_id=db_orderItem.product_id,
        type="Return",
        reason=ret.reason.value
    )

    db.add(return_order)
    db.commit()
    
    db.refresh(return_order)
    
    return {
        "message" : "Order return Successfull",
        "data" : {
            "order_id" : db_orderItem.order_id,
            "product_id" : db_orderItem.product_id
        }
    }


@order_route.post("/replace")
def replace_order_item(ret : schema.OrderReplace, current_user = Depends(get_current_user), db : Session = Depends(get_db)):
    user_email = current_user.get("sub")

    db_user = db.query(models.User).filter(models.User.email == user_email).first()

    db_order = db.query(models.Order).filter(
            models.Order.user_id == db_user.id,
            models.Order.id == ret.order_id
            ).first()
    
    if not db_order:
        raise HTTPException(404, "Order not found")

    if db_order.status != "Delevered":
        raise HTTPException(403, "Order not delevered yet")
        
    db_orderItem = db.query(models.OrderItem).filter(
        models.OrderItem.order_id == db_order.id,
        models.OrderItem.product_id == ret.product_id).first()

    if not db_orderItem:
        raise HTTPException(
            status_code=404,
            detail="Order items not found"
        )
    existing_order = db.query(models.Returns).filter(
        models.Returns.order_id == ret.order_id,
        models.Returns.product_id == ret.product_id
    ).first()

    if existing_order:
        raise HTTPException(status_code=400, detail = "Replace request already exists")
        
    replace_order = models.Returns(
        user_id = db_user.id,
        order_id = ret.order_id,
        product_id =  db_orderItem.product_id,
        type = "Replace",
        reason = ret.reason.value
    )

    db.add(replace_order)
    
    db.commit()
    db.refresh(replace_order)

    return {
        "message" : "Order Replace success",
        "order_id" : db_orderItem.order_id
    }
