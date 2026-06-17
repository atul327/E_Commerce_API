from fastapi import FastAPI, Depends, HTTPException
from database import SessionLocal, Base, engine


from routes.user import user_route
from routes.products import product_route
from routes.cart import cart_route
from routes.order import order_route
from routes.return_request import admin_route

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(user_route)
app.include_router(product_route)
app.include_router(cart_route)
app.include_router(order_route)
app.include_router(admin_route)


@app.get('/')
def home():
    return {"message" : "Hello User"}



