import logging
import os
from typing import Any

import jwt
from fastapi.security import HTTPBearer


def get_token_payload(token: str) -> dict[str, Any]:
    try:
        unverified_headers = jwt.get_unverified_header(token)
        return jwt.decode(
            token,
            key=os.getenv('JWT_SECRET'),
            algorithms=unverified_headers['alg'],
        )

    except Exception as exc:
        logging.error(f'Error JWT decode: {exc}')
        return {}


security = HTTPBearer()
