import random
from sympy import isprime, mod_inverse, gcd, randprime

def generate_rsa_keys(bits):
    """Генерация RSA-ключей с корректными e и d"""
    
    def generate_prime(bits):
        """Генерирует случайное простое число нужной длины"""
        while True:
            num = random.getrandbits(bits) | 1  # Делаем число нечетным
            if isprime(num):
                return num
    
    # Генерация p и q
    p = generate_prime(bits // 2)
    q = generate_prime(bits // 2)

    # Вычисление N = p * q
    N = p * q
    
    # Вычисление функции Эйлера φ(N)
    phi_n = (p - 1) * (q - 1)
    
    # Выбор e
    e = 65537  # Часто используемое значение
    if gcd(e, phi_n) != 1:
        e = randprime(3, phi_n)  # Если e не подходит, выбираем другое

    # Вычисление d - обратного по модулю φ(N)
    d = mod_inverse(e, phi_n)
    
    # Возвращаем открытый ключ (e, N) и закрытый ключ (d, N)
    return (e, N), (d, N)

# Пример использования
bits = 512  # Минимум для безопасности
public_key, private_key = generate_rsa_keys(bits)

print("Public Key (e, N):", public_key)
print("Private Key (d, N):", private_key)
