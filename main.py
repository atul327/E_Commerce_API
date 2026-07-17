from contextlib import asynccontextmanager
from fastapi import FastAPI

from database import Base, engine

# IMPORTANT: models load karo
import models.user
import models.products
import models.cart
import models.order
import models.payment


from routes.user import user_route
from routes.products import product_route
from routes.cart import cart_route
from routes.order import order_route
from routes.return_request import admin_route
from routes.payment import payment_router


@asynccontextmanager
async def lifespan(app: FastAPI):

    print("REGISTERED TABLES:", Base.metadata.tables.keys())

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    await engine.dispose()


app = FastAPI(lifespan=lifespan)


app.include_router(user_route)
app.include_router(product_route)
app.include_router(cart_route)
app.include_router(order_route)
app.include_router(admin_route)
app.include_router(payment_router)


@app.get("/")
def home():
    return {"message": "Hello User"}