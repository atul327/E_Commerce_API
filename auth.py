from passlib.context import CryptContext
from jose import jwt 
from datetime import datetime, timedelta

pwd_context = CryptContext(schemes=['bcrypt'])

def hashed_pass(password : str):
    hashed_password = pwd_context.hash(password)

    return hashed_password

def verify_pass(plain_pass : str, password : str):
    return  pwd_context.verify(plain_pass, password)



# Token generating
SECRET_KEY ="mysecretkey"
ALGORITH = "HS256"
ACCESS_TIME_MINUTE = 30

def create_access_token(data : dict):
    to_encode = data.copy()

    expire = datetime.utcnow()+timedelta(minutes=ACCESS_TIME_MINUTE)

    to_encode.update({
        "exp" : expire,
    })

    encode_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITH
    )

    return encode_jwt


def verify_token(token : str):
    payload = jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITH]
    )

    return payload



