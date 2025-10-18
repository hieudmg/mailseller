import hashlib
import random
import time
from app.core.config import settings


def generate_user_token(email: str) -> str:
    """Generate a new API token for a user based on their email, timestamp, and salted with SECRET_KEY."""
    random_number = random.randint(100000, 999999999)
    timestamp = str(time.time())
    token_string = f"{email}~{random_number}~{timestamp}~{settings.SECRET_KEY}"

    token_hash = hashlib.blake2b(token_string.encode(), digest_size=20).hexdigest()

    return f"{token_hash[0:10]}-{token_hash[10:20]}-{token_hash[20:]}"
