from pydantic import BaseModel, EmailStr, Field
from typing import Optional

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
