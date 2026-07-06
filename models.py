from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from datetime import datetime
from database import Base
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    username = Column(String(50))
    email = Column(String(50))
    mob_num = Column(String(15))
    password = Column(String(20))
    date_of_birth = Column(String(255))
    role = Column(String(20), default="user")
    user_address = Column(String)
    is_active = Column(String, default=True)

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    stock = Column(Integer)
    price = Column(Float)

    cart = relationship("Cart", back_populates="product")
    orderitem = relationship("OrderItem", back_populates="product")

class Cart(Base):
    __tablename__  = "cart"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey(User.id))
    product_id = Column(Integer, ForeignKey(Product.id))
    quantity = Column(Integer)

    product = relationship("Product", back_populates="cart")

class Order(Base):
    __tablename__ = "order_place"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey(User.id))
    total_amount = Column(Float) #internally pure product ka total
    status = Column(String)
    payment_method = Column(String)
    user_address = Column(String) # profile se aayenga
    created_at = Column(DateTime, default=datetime.now)
    
class OrderItem(Base):
    __tablename__ = "order_item"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey(Order.id))
    product_id = Column(Integer, ForeignKey(Product.id))
    quantity = Column(Integer)
    price = Column(Float)
    subtotal = Column(Float)

    product = relationship("Product", back_populates="orderitem")

class Returns(Base):
    __tablename__ = "returns"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey(User.id))
    order_id = Column(Integer, ForeignKey(Order.id))
    product_id = Column(Integer, ForeignKey(Product.id))
    type = Column(String(50))
    reason = Column(String(50))
    status = Column(String(50), default="Request")
    created_at = Column(DateTime, default=datetime.now)

class Reviews(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey(User.id))
    product_id = Column(Integer, ForeignKey(Product.id))
    rating = Column(Integer)
    comment = Column(String(100))
    created_at = Column(DateTime, default=datetime.now)
