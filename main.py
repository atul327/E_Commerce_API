from fastapi import FastAPI, Depends, HTTPException
from database import SessionLocal, Base, engine


from routes.user import user_route
from routes.products import product_route

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(user_route)
app.include_router(product_route)


@app.get('/')
def home():
    return {"message" : "Hello User"}



