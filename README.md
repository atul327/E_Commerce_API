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
git clone <repository-url>

cd project

pip install -r requirements.txt

uvicorn main:app --reload
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
