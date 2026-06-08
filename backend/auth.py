from jose import jwt
from jose import JWTError

import bcrypt
import hashlib

from datetime import datetime
from datetime import timedelta

from backend.config import SECRET_KEY
from backend.config import ALGORITHM

if SECRET_KEY is None:
    raise ValueError("SECRET_KEY environment variable must be set")


def hash_password(password):
    # Hash with SHA256 first, then bcrypt
    sha256_hash = hashlib.sha256(password.encode()).hexdigest()
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(sha256_hash.encode(), salt)
    return hashed.decode()


def verify_password(
    plain_password,
    hashed_password
):
    # Hash plain password same way
    sha256_hash = hashlib.sha256(plain_password.encode()).hexdigest()
    return bcrypt.checkpw(sha256_hash.encode(), hashed_password.encode())


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