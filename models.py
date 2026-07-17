from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean, Numeric
from datetime import datetime
from database import Base
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    username = Column(String(50))
    email = Column(String(50))
    mob_num = Column(String(15))
    password = Column(String(255))
    date_of_birth = Column(String(255))
    role = Column(String(20), default="user")
    user_address = Column(String(255))
    is_active = Column(Boolean, default=True)

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100))
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
    total_amount = Column(Float)
    status = Column(String(50))
    payment_method = Column(String(50))
    user_address = Column(String(255))
    created_at = Column(DateTime, default=datetime.now)

    payment = relationship(
        "Payment",
        back_populates="order"
    )
    
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

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey(Order.id))
    gateway = Column(String(50))
    gateway_order_id = Column(String(100),unique=True)
    gateway_payment_id = Column(String(100), unique=True, nullable=True)
    amount = Column(Numeric(10,2))
    status = Column(String(20), default="Pending")
    created_at = Column(DateTime, default=datetime.utcnow)

    order = relationship(
        "Order",
        back_populates="payment"
    )