# E-Commerce API (FastAPI)

A RESTful E-Commerce Backend API built using FastAPI, SQLAlchemy, JWT Authentication, and MySQL.

## Features

### Authentication & User Management

* User Registration
* User Login
* JWT Authentication
* Get User Profile
* Update User Profile
* Change Password

### Product Management

* Add Product
* Get All Products
* Get Product By ID
* Update Product
* Delete Product

## Tech Stack

* Python
* FastAPI
* SQLAlchemy
* MySQL
* JWT Authentication
* Pydantic
* Uvicorn

## API Endpoints

### User Routes

| Method | Endpoint         | Description                |
| ------ | ---------------- | -------------------------- |
| POST   | /register        | Register new user          |
| POST   | /login           | User login                 |
| GET    | /profile         | Get logged-in user profile |
| PUT    | /profile         | Update profile             |
| PUT    | /change-password | Change password            |

### Product Routes

| Method | Endpoint       | Description       |
| ------ | -------------- | ----------------- |
| POST   | /products      | Add product       |
| GET    | /products      | Get all products  |
| GET    | /products/{id} | Get product by ID |
| PUT    | /products/{id} | Update product    |
| DELETE | /products/{id} | Delete product    |

## Project Structure

```
E_comm/
│
├── main.py
├── database.py
├── models/
├── routes/
├── schemas/
├── requirements.txt
└── README.md
```

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/atul327/E_Commerce_API.git

# 2. Go to the project folder
cd E_Commerce_API

# 3. Install all dependencies
pip install -r requirements.txt

# 4. Run the FastAPI application
python -m uvicorn main:app --reload
```

## Authentication

This project uses JWT (JSON Web Token) Authentication.

After login, include the token in the Authorization header:

```
Authorization: Bearer <your_token>
```

## Upcoming Features

* Order Management
* Cart Management
* Payment Integration

## Author

Atul Patle
AI & Machine Learning Engineering Student

```
```
