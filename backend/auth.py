from jose import jwt
from jose import JWTError

from passlib.context import CryptContext

from datetime import datetime
from datetime import timedelta

from config import SECRET_KEY
from config import ALGORITHM

if SECRET_KEY is None:
    raise ValueError("SECRET_KEY environment variable must be set")

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


def hash_password(password):
    return pwd_context.hash(password)


def verify_password(
    plain_password,
    hashed_password
):
    return pwd_context.verify(
        plain_password,
        hashed_password
    )


def create_access_token(data):

    payload = data.copy()

    expire = datetime.utcnow() + timedelta(hours=1)

    payload.update({
        "exp": expire
    })

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


def verify_token(token):

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        return payload

    except JWTError:
        return None