# Часть 1: Класс итераторов Fibo
class Fibo:
    def __init__(self):
        # Начальные значения последовательности Фибоначчи
        self.a, self.b = 0, 1
    
    def __iter__(self):
        return self
    
    def __next__(self):
        result = self.a
        # Следующие два числа вычисляются по рекурсивному соотношению
        self.a, self.b = self.b, self.a + self.b
        return result


# Часть 2: Функция integers(), возвращающая список целых чисел
def integers(count):
    return list(range(count))


# Часть 3: Функция primes(), возвращающая список простых чисел
def is_prime(n):
    """ Проверяет, является ли число n простым """
    if n <= 1:
        return False
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return False
    return True

def primes(count):
    found_primes = []
    num = 2
    while len(found_primes) < count:
        if is_prime(num):
            found_primes.append(num)
        num += 1
    return found_primes


# Основная часть программы
if __name__ == "__main__":
    # Пример использования итераторов и функций
    fibo_iter = Fibo()  # Создаем итератор для чисел Фибоначчи
    print("Первые 10 чисел Фибоначчи:")
    for _ in range(10):
        print(next(fibo_iter))

    # Генерируем целые числа
    print("\nПервые 10 целых чисел:")
    integer_list = integers(10)
    for number in integer_list:
        print(number)

    # Генерируем простые числа
    print("\nПервые 10 простых чисел:")
    prime_list = primes(10)
    for prime in prime_list:
        print(prime)