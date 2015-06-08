import hashlib


def username_hash(email, max_length=30):
    """Generates a Username hash from an email address."""
    m = hashlib.md5()
    m.update(email.encode("utf8"))
    return m.hexdigest()[:max_length]
