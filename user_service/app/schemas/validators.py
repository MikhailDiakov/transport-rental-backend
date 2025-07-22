import re


def validate_password_complexity(password: str) -> str:
    if len(password) < 6:
        raise ValueError("Password must be at least 6 characters long")
    if not re.search(r"\d", password):
        raise ValueError("Password must contain at least one digit")
    if not re.search(r"[A-Za-zА-Яа-я]", password):
        raise ValueError("Password must contain at least one letter")
    if not re.search(r"[\W_]", password):
        raise ValueError("Password must contain at least one special character")
    return password


def validate_username_length(username: str) -> str:
    if not (3 <= len(username) <= 50):
        raise ValueError("Username must be between 3 and 50 characters")
    return username
