import time
import secrets

def generate_timestamp():
    return str(int(time.time() * 1000))

def generate_token(length=16):
    return secrets.token_hex(length // 2)
