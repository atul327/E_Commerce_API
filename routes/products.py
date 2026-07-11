from fastapi import APIRouter, Depends, Header, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import AsyncSessionLocal
from typing import Optional

import schema
import models
import auth

product_route = APIRouter(
    prefix="/product"
)

async def get_db():
    async with AsyncSessionLocal() as db:
        yield db

# to decode and verify the token
def get_current_user(authorization: str = Header()):
    if not authorization:
        raise HTTPException(status_code=400, detail="Missing Token")
    
    token = authorization.split(" ")[1]
    payload = auth.verify_token(token)
    return payload

# to add new produt
@product_route.post("/products")
async def add_product(product: schema.AddProduct, current_user=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    user_email = current_user.get("sub")

    result = await db.execute(
        select(models.User).where(models.User.email == user_email)
    )
    db_user = result.scalar_one_or_none()

    if db_user.role != "admin":
        raise HTTPException(status_code=403, detail="User can't be add product")
    
    new_product = models.Product(
        name=product.name,
        stock=product.stock,
        price=product.price
    )

    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)

    return {
        "message": "New Product added successfully",
        "role": db_user.role,
        "email": user_email
    }

# for geting single product based on ID of product & add response model
@product_route.get("/get_product/{p_id}", response_model=schema.ProductResponse)
async def get_product(p_id: int = Path(..., example="1", description="Product ID"), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(models.Product).where(models.Product.id == p_id)
    )
    db_product = result.scalar_one_or_none()

    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")

    return {
        "message": "Product fetch Successfully",
        "product": {
            "p_id": db_product.id,
            "name": db_product.name,
            "price": db_product.price
        }
    }

# to get all products
@product_route.get("/get_all_product")
async def get_all_product(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(models.Product)
    )

    products = result.scalars().all()

    if not products:
        raise HTTPException(status_code=404, detail="No product found")

    return {
        "message": "Fetch all Product Sucessfully",
        "products": products
    }


# to update the exixting product details
@product_route.put("/update_product/{p_id}")
async def update_product_details(product: schema.UpdateProduct,
                                 p_id: int = Path(example="1", description="Product ID", gt=1),
                                 current_user=Depends(get_current_user),
                                 db: AsyncSession = Depends(get_db)):

    user_email = current_user.get("sub")

    result = await db.execute(
        select(models.User).where(
            models.User.email == user_email
        )
    )

    db_user = result.scalar_one_or_none()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if db_user.role != "admin":
        raise HTTPException(status_code=400, detail="User can't update the product details")
    
    result = await db.execute(
        select(models.Product).where(
            models.Product.id == p_id
        )
    )

    db_product = result.scalar_one_or_none()

    if not db_product:
        raise HTTPException(status_code=404, detail="Product not Found")

    db_product.name = product.name
    db_product.price = product.price
    db_product.stock = product.stock

    await db.commit()
    await db.refresh(db_product)

    return {
        "message": "Product Details update successfully",
        "p_id": db_product.id,
        "name": db_product.name,
        "price": db_product.price
    }


# to delete product based of product id
@product_route.delete("/delete_product/{p_id}")
async def delete_product(p_id: int = Path(example="1", description="Product ID"),
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
        raise HTTPException(status_code=403, detail="User can't delete Product")
    
    result = await db.execute(
        select(models.Product).where(
            models.Product.id == p_id
        )
    )

    db_id = result.scalar_one_or_none()

    if not db_id:
        raise HTTPException(status_code=404, detail="Product not found!")

    await db.delete(db_id)
    await db.commit()

    return {
        "message": "Product Deleted Successfully",
        "product": {
            "p_id": db_id.id,
            "name": db_id.name,
            "price": db_id.price
        }
    }
#Searching with Pagination and Sorting (Asc/Desc)
@product_route.get("/search")
async def search_product(name: str = Query(""),
                         #  For filtering the data
                         max_price: Optional[int] = Query(None, ge=0),
                         min_price: Optional[int] = Query(None, ge=0),
                         #  to sort the record
                         sort: str = Query("asc"),
                         #  For the Pagination
                         page: int = Query(1, ge=1),
                         limit: int = Query(10, ge=1, le=100),
                         db: AsyncSession = Depends(get_db)):

    # offset is for to skip the record which is in offset
    offset = (page - 1) * limit

    # Sorting logic
    if sort == "asc":
        sorting = models.Product.price.asc()
    elif sort == "desc":
        sorting = models.Product.price.desc()
    else:
        raise HTTPException(status_code=400, detail="Sorting Order must be asc or desc")

    # Base query create karo
    # SQL:
    # SELECT * FROM products;
    db_product = select(models.Product)

    # Product name ke basis par search karo
    db_product = db_product.where(
        models.Product.name.ilike(f"%{name}%")
    )

    # Agar user ne max_price diya hai
    # To usse kam ya equal price wale products fetch karo
    if max_price is not None:
        db_product = db_product.where(
            models.Product.price <= max_price
        )

    # Agar user ne min_price diya hai
    # To usse bade ya equal price wale products fetch karo
    if min_price is not None:
        db_product = db_product.where(
            models.Product.price >= min_price
        )
    
    # Products ko ascending ya descending order me sort karo
    db_product = db_product.order_by(sorting)

    # Pagination apply karo
    db_product = db_product.offset(offset).limit(limit)
    
    # Query execute karo aur database se actual records fetch karo
    result = await db.execute(db_product)

    products = result.scalars().all()

    if not products:
        raise HTTPException(status_code=404, detail="No Product found")

    return{
        "Products" : products
    }