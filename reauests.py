import math
import random
import time

def quadratic_sieve(n):
    start_time = time.time()
    
    B = int(math.exp(math.sqrt(math.log(n) * math.log(math.log(n)))))
    primes = sieve_of_eratosthenes(B)
    factors = []
    
    x = int(math.sqrt(n))
    y = x
    smooth_count = 0
    while smooth_count < len(primes):
        x += 1
        smooth = list(find_smooth(x, y, primes))
        if smooth:
            smooth_count += 1
            M = math.prod(smooth)
            t = tonelli_shanks(M, n)
            if t is not None:
                g = math.gcd(x - t, n)
                if 1 < g < n:
                    factors.append(g)
                    n //= g
                    if n > 1:
                        factors.append(n)
                    end_time = time.time()
                    print(f"Время выполнения: {end_time - start_time:.6f} секунд")
                    return factors
    end_time = time.time()
    print(f"Время выполнения: {end_time - start_time:.6f} секунд")
    return [n]

def sieve_of_eratosthenes(limit):
    sieve = [True] * (limit + 1)
    sieve[0] = sieve[1] = False
    for i in range(2, int(math.sqrt(limit)) + 1):
        if sieve[i]:
            for j in range(i * i, limit + 1, i):
                sieve[j] = False
    return [p for p in range(2, limit + 1) if sieve[p]]

def tonelli_shanks(n, p):
    if p == 2:
        return n % 2
    if pow(n, (p - 1) // 2, p) == p - 1:
        return None
    q = p - 1
    s = 0
    while q % 2 == 0:
        q //= 2
        s += 1
    if s == 1:
        return pow(n, (p + 1) // 4, p)
    z = 2
    while pow(z, (p - 1) // 2, p) != p - 1:
        z += 1
    c = pow(z, q, p)
    r = pow(n, (q + 1) // 2, p)
    t = pow(n, q, p)
    m = s
    while t != 1:
        for i in range(1, m):
            if pow(t, 2**i, p) == 1:
                b = pow(c, 2**(m - i - 1), p)
                r = (r * b) % p
                t = (t * b * b) % p
                c = (b * b) % p
                m = i
                break
    return r

def find_smooth(x, y, primes):
    v = (x * x - n) % n
    for p in primes:
        while v % p == 0:
            v //= p
            yield p
    if v == 1:
        return True
    return False

# Пример использования:
n = random.getrandbits(30)  # 100-битное число
result = quadratic_sieve(n)
print(f"Факторы: {result}")
