import logging
import os
from http import HTTPStatus
from typing import Any

import jwt
from fastapi import HTTPException
from fastapi.security import HTTPBearer
from jwt.exceptions import DecodeError


def get_token_payload(token: str) -> dict[str, Any]:
    try:
        unverified_headers = jwt.get_unverified_header(token)
        return jwt.decode(
            token,
            key=os.getenv("JWT_SECRET"),
            algorithms=unverified_headers["alg"],
        )

    except DecodeError as exc:
        logging.error(f"Error JWT decode: {exc}")
        return {}


def check_authorization(token):
    token_payload = get_token_payload(token.credentials)
    user_id = token_payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED)
    return user_id


security = HTTPBearer()
