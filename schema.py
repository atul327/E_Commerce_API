from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from enum import Enum

class Registration(BaseModel):
    username : str 
    email : EmailStr
    mob_num : str = Field(min_length=10, max_length=10)
    password : str = Field(min_length=8, max_length=12)
    date_of_birth :  str = Field(description="12-10-2006")
    role : Optional[str]
    user_address : str

class Login(BaseModel):
    email : EmailStr
    password : str 

class UpdateProfile(BaseModel):
    username : Optional[str]
    mob_num : Optional[str] = Field(min_length=10, max_length=10)
    user_address : Optional[str]

class ChangePass(BaseModel):
    old_password : str
    new_password : str 

class AddProduct(BaseModel):
    name : str
    stock : int
    price : float
    
class UpdateProduct(BaseModel):
    name : str
    price : float

class AddToCart(BaseModel):
    user_id : int
    product_id : int 
    quantity : int 

class UpdateCart(BaseModel):
    quantity : int

class Order(BaseModel):
    user_id : int
    payment_method : str


# Only alow fixed value from this gien below
class OrderStatus(str, Enum):
    Pending = "Pending"
    Processing = "Processing"
    Shipped = "Shipped"
    Delevered = "Delevered"
    Cancelled = "Cancelled"

class UpdateStatus(BaseModel):
    status : OrderStatus

class OrderReturnReason(str, Enum):
    Damaged = "Damaged product"
    Wrong = "Wrong product"
    NotSatisfied = "Not satisfied"
    Defective = "Defective"

class OrderReturn(BaseModel):
    order_id : int 
    product_id : int 
    reason : OrderReturnReason

class OrderReplaceReason(str, Enum):
    Wrong = "Wrong product"
    Defective = "Defective"

class OrderReplace(BaseModel):
    order_id : int
    product_id : int
    reason : OrderReplaceReason

class Reviews(BaseModel):
    order_id : int 
    product_id : int
    rating : int = Field(ge = 1, le = 5)
    comment : str


# Add response model for the security and validation
class GetProductResponseModel(BaseModel):
    id : int
    name : str
    price : float

class ProductResponse(BaseModel):
    message : str
    product : GetProductResponseModel