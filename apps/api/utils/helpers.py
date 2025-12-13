"""Helper functions."""
import re
from typing import Optional
import bcrypt


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def normalize_brand(brand: str) -> str:
    """Normalize brand name."""
    brand_map = {
        "nike": "Nike",
        "adidas": "Adidas",
        "new balance": "New Balance",
        "puma": "Puma",
        "reebok": "Reebok",
        "asics": "Asics",
        "converse": "Converse",
        "vans": "Vans",
        "jordan": "Jordan",
        "ralph lauren": "Ralph Lauren",
        "polo ralph lauren": "Ralph Lauren",
        "lacoste": "Lacoste",
        "tommy hilfiger": "Tommy Hilfiger",
    }
    return brand_map.get(brand.lower().strip(), brand.title())


def parse_price(price_str: str) -> Optional[float]:
    """Parse price string to float."""
    if not price_str:
        return None
    try:
        cleaned = price_str.replace("€", "").replace(",", ".").replace(" ", "").strip()
        return float(cleaned)
    except ValueError:
        return None


def slugify(text: str) -> str:
    """Convert text to URL-safe slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text
