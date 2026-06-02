from sqlalchemy import Column, Integer, String, Float, ForeignKey
from database import Base

class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    username = Column(String(50))
    email = Column(String(50))
    mob_num = Column(String(15))
    password = Column(String(20))
    date_of_birth = Column(String(255))
    role = Column(String(20), default="user")

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    price = Column(Float)

class Cart(Base):
    __tablename__  = "cart"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey(User.id))
    product_id = Column(Integer, ForeignKey(Product.id))
    quantity = Column(Integer)
