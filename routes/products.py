from fastapi import APIRouter, Depends, Header, HTTPException, Path
from sqlalchemy.orm import Session
from database import SessionLocal

import schema
import models
import auth

product_route = APIRouter(
    prefix="/product"
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# to decode and verify the token
def get_current_user(authorization : str = Header()):
    if not authorization:
        raise HTTPException(status_code=400, detail="Missing Token")
    
    token = authorization.split(" ")[1]

    payload = auth.verify_token(token)

    return payload

# to add new produt
@product_route.post("/products")
def add_product(product : schema.AddProduct, current_user = Depends(get_current_user), db : Session = Depends(get_db)):
    user_email = current_user.get("sub")

    db_user = db.query(models.User).filter(models.User.email == user_email).first()

    if db_user.role != "admin":
        raise HTTPException(status_code=403, detail="User can't be add product")
    
    new_product = models.Product(
        name = product.name,
        stock = product.stock,
        price = product.price
    )

    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return{
        "message" : "New Product added successfully",
        "role" : db_user.role,
        "email" : user_email
    }

# for geting single product based on ID of product
@product_route.get("/get_product/{p_id}")
def get_product(p_id : int = Path(..., example="1", description="Product ID"), db : Session = Depends(get_db)):

    db_product = db.query(models.Product).filter(models.Product.id == p_id).first()

    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")

    return {
        "message" : "Product fetch Successfully",
        "product" : {
            "p_id" : db_product.id,
            "name" : db_product.name,
            "price" : db_product.price
        }
    }

# to get all products
@product_route.get("/get_all_product")
def get_all_product(db : Session = Depends(get_db)):
    products = db.query(models.Product).all()

    if not products:
        raise HTTPException(status_code=404, detail="No product found")

    return {
        "message" : "Fetch all Product Sucessfully",
        "products" : products
    }

# to update the exixting product details
@product_route.put("/update_product/{p_id}")
def update_product_details(product : schema.UpdateProduct , p_id : int = Path(example="1", description="Product ID", gt=1), current_user = Depends(get_current_user), db : Session = Depends(get_db)):
    user_email = current_user.get("sub")

    db_user = db.query(models.User).filter(models.User.email == user_email).first()

    if db_user.role != "admin":
        raise HTTPException(status_code=400, detail="User can't update the product details")
    
    db_product = db.query(models.Product).filter(models.Product.id == p_id).first()

    if not db_product:
        raise HTTPException(status_code=404, detail="Product not Found")

    db_product.name = product.name
    db_product.price = product.price

    db.commit()
    db.refresh(db_product)

    return {
        "message" : "Product Details update successfully",
        "p_id" : db_product.id,
        "name" : db_product.name,
        "price" : db_product.price
    }


# to delete product based of product id
@product_route.delete("/delete_product/{p_id}")
def delete_product(p_id : int = Path(example="1", description="Product ID"), current_user = Depends(get_current_user), db : Session = Depends(get_db)):
    user_email = current_user.get("sub")
    
    db_user = db.query(models.User).filter(models.User.email == user_email).first()

    if db_user.role != "admin":
        raise HTTPException(status_code=403, detail="User can't delete Product")
    
    db_id = db.query(models.Product).filter(models.Product.id == p_id).first()

    if not db_id:
        raise HTTPException(status_code=404, detail="Product not found!")

    db.delete(db_id)
    db.commit()

    return {
        "message" : "Product Deleted Successfully",
        "product" : {
            "p_id" : db_id.id,
            "name" : db_id.name,
            "price" : db_id.price
        }
    }