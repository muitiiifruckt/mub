import hashlib
import random
import string
import logging
from sympy import randprime, primitive_root
def md5(text):
    hashed = hashlib.md5(text.encode('utf-8')).hexdigest()
    logging.info(f"MD5('{text}') = {hashed}")
    return hashed

def gen_str(length=32):
    random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    logging.info(f"Generated nonce: {random_str}")
    return random_str
def generate_prime(bits):
        lower_bound = 2**(bits - 1)
        upper_bound = 2**bits - 1
        return randprime(lower_bound, upper_bound)
def gen_a_g_p(bits = 128):
    p = generate_prime(bits)
    g = primitive_root(p)
    a = random.randint(1, p-1)
    return a,g,p
def sha256(data: bytes) -> int:
    """Возвращает SHA-256 хэш в виде числа"""
    return int(hashlib.sha256(data).hexdigest(), 16)