from typing import List, Optional
import math


# Класс для работы с рациональными числами
class RatNum:
    def __init__(self, numerator: int = 0, denominator: int = 1):
        '''Initializes a rational number instance.
        @requires: numerator ϵ integer, denominator ϵ integer ≠ 0
        @modifies: _numerator, _denominator
        @effects: Reduces the fraction by finding the greatest common divisor (GCD).
        @raises: ValueError if denominator equals zero.
        @returns: None'''
        if denominator == 0:
            raise ValueError("Знаменатель не может быть равен нулю!")
        
        # Сокращение дроби
        gcd_val = math.gcd(numerator, denominator)
        self._numerator = numerator // gcd_val
        self._denominator = denominator // gcd_val
    
    # Является ли число NaN?
    def is_nan(self) -> bool:
        '''Checks if the rational number is undefined (NaN).
        @requires: None
        @modifies: None
        @effects: Returns True if denominator is zero.
        @raises: None
        @returns: bool'''
        return self._denominator == 0
    
    # Положительное число?
    def is_positive(self) -> bool:
        '''Determines if the number is positive.
        @requires: None
        @modifies: None
        @effects: Returns True if numerator is greater than zero.
        @raises: None
        @returns: bool'''
        return self._numerator > 0
    
    # Отрицательное число?
    def is_negative(self) -> bool:
        '''Determines if the number is negative.
        @requires: None
        @modifies: None
        @effects: Returns True if numerator is less than zero.
        @raises: None
        @returns: bool'''
        return self._numerator < 0
    
    # Преобразовать в вещественное число
    def float_value(self) -> float:
        '''Converts the rational number to a floating-point representation.
        @requires: Fraction must be valid (not NaN).
        @modifies: None
        @effects: Divides numerator by denominator.
        @raises: ValueError if the fraction is NaN.
        @returns: float'''
        if self.is_nan():
            raise ValueError("Преобразование NaN в float невозможно.")
        return self._numerator / self._denominator
    
    # Преобразовать в целое число
    def int_value(self) -> int:
        '''Truncates the rational number to an integer.
        @requires: Fraction must be valid (not NaN).
        @modifies: None
        @effects: Integer divides numerator by denominator.
        @raises: ValueError if the fraction is NaN.
        @returns: int'''
        if self.is_nan():
            raise ValueError("Преобразование NaN в int невозможно.")
        return self._numerator // self._denominator
    
    # Получить наибольший общий делитель
    def gcd(self, other: 'RatNum') -> int:
        '''Returns the greatest common divisor of two rational numbers' numerators.
        @requires: other ϵ RatNum
        @modifies: None
        @effects: Calculates GCD of both numerators.
        @raises: None
        @returns: int'''
        return math.gcd(self._numerator, other._numerator)
    
    # Строковое представление
    def __str__(self) -> str:
        '''Provides a human-readable string representation of the rational number.
        @requires: None
        @modifies: None
        @effects: Formats the number properly.
        @raises: None
        @returns: str'''
        if self.is_nan():
            return "NaN"
        return f"{self._numerator}/{self._denominator}" if self._denominator != 1 else f"{self._numerator}"
    
    # Хэширование
    def __hash__(self) -> int:
        '''Generates a unique hashcode for the rational number.
        @requires: None
        @modifies: None
        @effects: Uses the built-in hash function on the pair (_numerator, _denominator).
        @raises: None
        @returns: int'''
        return hash((self._numerator, self._denominator))
    
    # Проверка равенства
    def __eq__(self, other: object) -> bool:
        '''Tests equality against another object.
        @requires: other should be an instance of type RatNum.
        @modifies: None
        @effects: Compares both numerator and denominator.
        @raises: None
        @returns: bool'''
        if not isinstance(other, RatNum):
            return False
        return self._numerator == other._numerator and self._denominator == other._denominator
    
    # Арифметические операторы
    def __neg__(self) -> 'RatNum':
        '''Negates the rational number.
        @requires: None
        @modifies: None
        @effects: Returns a new rational number with the opposite sign.
        @raises: None
        @returns: RatNum'''
        return RatNum(-self._numerator, self._denominator)
    
    def __add__(self, other: 'RatNum') -> 'RatNum':
        '''Adds two rational numbers.
        @requires: other ϵ RatNum
        @modifies: None
        @effects: Performs addition of rational numbers.
        @raises: None
        @returns: RatNum'''
        common_denom = self._denominator * other._denominator
        numer_sum = self._numerator * other._denominator + other._numerator * self._denominator
        return RatNum(numer_sum, common_denom)
    
    def __sub__(self, other: 'RatNum') -> 'RatNum':
        '''Subtracts one rational number from another.
        @requires: other ϵ RatNum
        @modifies: None
        @effects: Performs subtraction via addition with negation.
        @raises: None
        @returns: RatNum'''
        return self + (-other)
    
    def __mul__(self, other: 'RatNum') -> 'RatNum':
        '''Multiplies two rational numbers.
        @requires: other ϵ RatNum
        @modifies: None
        @effects: Multiplies the numerators and denominators separately.
        @raises: None
        @returns: RatNum'''
        return RatNum(self._numerator * other._numerator, self._denominator * other._denominator)
    
    def __truediv__(self, other: 'RatNum') -> 'RatNum':
        '''Divides one rational number by another.
        @requires: other ϵ RatNum, numerator of other != 0
        @modifies: None
        @effects: Inverts the second argument and multiplies.
        @raises: ZeroDivisionError if attempting to divide by zero.
        @returns: RatNum'''
        if other.is_nan() or other._numerator == 0:
            raise ZeroDivisionError("Делить на ноль нельзя!")
        return self * RatNum(other._denominator, other._numerator)


# Класс для работы с полиномами с рациональными коэффициентами
class RatPoly:
    def __init__(self, coeffs: Optional[List[RatNum]] = None):
        '''Creates a polynomial with rational coefficients.
        @requires: coeffs ϵ Optional[list of RatNum]
        @modifies: coeffs
        @effects: Initializes the coefficients array.
        @raises: None
        @returns: None'''
        if coeffs is None:
            coeffs = []
        self.coeffs = list(coeffs)
    
    # Возвращает степень полинома
    def degree(self) -> int:
        '''Returns the degree of the polynomial.
        @requires: None
        @modifies: None
        @effects: Returns the size of the coefficients array minus one.
        @raises: None
        @returns: int'''
        return len(self.coeffs) - 1
    
    # Возвращает коэффициент при соответствующей степени
    def get_coeff(self, index: int) -> RatNum:
        '''Gets the coefficient at a given index.
        @requires: index ≥ 0
        @modifies: None
        @effects: Returns the corresponding coefficient or 0 if out of bounds.
        @raises: None
        @returns: RatNum'''
        try:
            return self.coeffs[index]
        except IndexError:
            return RatNum(0)
    
    # Проверка на NaN
    def is_nan(self) -> bool:
        '''Verifies if any coefficient is NaN.
        @requires: None
        @modifies: None
        @effects: Iterates through coefficients to check for NaN values.
        @raises: None
        @returns: bool'''
        return any(coeff.is_nan() for coeff in self.coeffs)
    
    # Масштабирование коэффициентов
    def scale_coeff(self, factor: RatNum) -> 'RatPoly':
        '''Scales the polynomial's coefficients by a given factor.
        @requires: factor ϵ RatNum
        @modifies: None
        @effects: Returns a new polynomial with scaled coefficients.
        @raises: None
        @returns: RatPoly'''
        scaled_coeffs = [coeff * factor for coeff in self.coeffs]
        return RatPoly(scaled_coeffs)
    
    # Перегрузка оператора унарного минуса
    def __neg__(self) -> 'RatPoly':
        '''Negates the polynomial.
        @requires: None
        @modifies: None
        @effects: Returns a new polynomial with flipped signs.
        @raises: None
        @returns: RatPoly'''
        negated_coeffs = [-coeff for coeff in self.coeffs]
        return RatPoly(negated_coeffs)
    
    # Перегрузка оператора сложения
    def __add__(self, other: 'RatPoly') -> 'RatPoly':
        '''Adds two polynomials.
        @requires: other ϵ RatPoly
        @modifies: None
        @effects: Merges coefficients according to addition rules.
        @raises: None
        @returns: RatPoly'''
        max_degree = max(self.degree(), other.degree())
        new_coeffs = [
            self.get_coeff(i) + other.get_coeff(i) for i in range(max_degree + 1)
        ]
        return RatPoly(new_coeffs)
    
    # Перегрузка оператора вычитания
    def __sub__(self, other: 'RatPoly') -> 'RatPoly':
        '''Subtracts one polynomial from another.
        @requires: other ϵ RatPoly
        @modifies: None
        @effects: Subtracts by adding the negation of the second polynomial.
        @raises: None
        @returns: RatPoly'''
        return self + (-other)
    
    # Перегрузка оператора умножения
    def __mul__(self, other: 'RatPoly') -> 'RatPoly':
        '''Multiplies two polynomials.
        @requires: other ϵ RatPoly
        @modifies: None
        @effects: Multiplies polynomials by distributing coefficients.
        @raises: None
        @returns: RatPoly'''
        new_coeffs = [RatNum(0)] * (len(self.coeffs) + len(other.coeffs) - 1)
        for i in range(len(self.coeffs)):
            for j in range(len(other.coeffs)):
                new_coeffs[i + j] += self.coeffs[i] * other.coeffs[j]
        return RatPoly(new_coeffs)
    
    # Перегрузка оператора деления
    def __truediv__(self, other: 'RatPoly') -> 'RatPoly':
        '''Divides one polynomial by another.
        @requires: other ϵ RatPoly, the degree of other must be zero.
        @modifies: None
        @effects: Supports only division by a constant.
        @raises: NotImplementedError if trying to divide by a non-constant polynomial.
        @returns: RatPoly'''
        if other.degree() == 0:
            divisor = other.get_coeff(0)
            divided_coeffs = [coeff / divisor for coeff in self.coeffs]
            return RatPoly(divided_coeffs)
        else:
            raise NotImplementedError("Комплексное деление полиномов не реализовано.")
    
    # Вычислить значение полинома в точке
    def eval(self, x: RatNum) -> RatNum:
        '''Evaluates the polynomial at a given point.
        @requires: x ϵ RatNum
        @modifies: None
        @effects: Evaluates the polynomial at the given point.
        @raises: None
        @returns: RatNum'''
        result = RatNum(0)
        for i, coeff in enumerate(reversed(self.coeffs)):
            result *= x
            result += coeff
        return result
    
    # Найти производную полинома
    def differentiate(self) -> 'RatPoly':
        '''Differentiates the polynomial.
        @requires: None
        @modifies: None
        @effects: Computes the derivative of the polynomial.
        @raises: None
        @returns: RatPoly'''
        derived_coeffs = [RatNum(i) * coeff for i, coeff in enumerate(self.coeffs) if i > 0]
        return RatPoly(derived_coeffs)
    
    # Нахождение неопределённого интеграла
    def anti_differentiate(self) -> 'RatPoly':
        '''Finds the antiderivative (integral) of the polynomial.
        @requires: None
        @modifies: None
        @effects: Integrates the polynomial and adds a free constant term.
        @raises: None
        @returns: RatPoly'''
        integral_coeffs = [(coeff / RatNum(i)) for i, coeff in enumerate(self.coeffs, start=1)]
        integral_coeffs.insert(0, RatNum(0))  # Добавляем свободный член
        return RatPoly(integral_coeffs)
    
    # Интегрирование
    def integrate(self, lower_bound: RatNum, upper_bound: RatNum) -> RatNum:
        '''Computes the definite integral of the polynomial within given bounds.
        @requires: lower_bound ϵ RatNum, upper_bound ϵ RatNum
        @modifies: None
        @effects: Evaluates the antiderivative at the bounds and takes the difference.
        @raises: None
        @returns: RatNum'''
        antiderivative = self.anti_differentiate()
        upper_value = antiderivative.eval(upper_bound)
        lower_value = antiderivative.eval(lower_bound)
        return upper_value - lower_value
    
    # Получить значение полинома в конкретной точке
    def value_of(self, point: RatNum) -> RatNum:
        '''Evaluates the polynomial at a specific point.
        @requires: point ϵ RatNum
        @modifies: None
        @effects: Same as the eval method.
        @raises: None
        @returns: RatNum'''
        return self.eval(point)
    
    # Строковое представление полинома
    def __str__(self) -> str:
        '''Represents the polynomial in a human-readable form.
        @requires: None
        @modifies: None
        @effects: Builds a string representation of the polynomial.
        @raises: None
        @returns: str'''
        terms = []
        for i, coeff in reversed(list(enumerate(self.coeffs))):
            term_str = ""
            if abs(coeff._numerator) > 0:
                if i == 0:
                    term_str = str(coeff)
                elif i == 1:
                    term_str = f"{coeff}x"
                else:
                    term_str = f"{coeff}x^{i}"
            
            if term_str:
                terms.append(term_str)
        return " + ".join(terms) if terms else "0"
    
    # Хэширование
    def __hash__(self) -> int:
        '''Generates a unique hashcode for the polynomial.
        @requires: None
        @modifies: None
        @effects: Uses the built-in hash function on the tuple of coefficients.
        @raises: None
        @returns: int'''
        return hash(tuple(self.coeffs))
    
    # Проверка равенства полиномов
    def __eq__(self, other: object) -> bool:
        '''Tests equality of two polynomials.
        @requires: other should be an instance of type RatPoly.
        @modifies: None
        @effects: Compares coefficients arrays element-wise.
        @raises: None
        @returns: bool'''
        if not isinstance(other, RatPoly):
            return False
        return self.coeffs == other.coeffs


# Основные тесты для класса рациональных чисел
r1 = RatNum(1, 2)
print(r1.float_value())  # Должно вывести 0.5
print(r1.int_value())    # Должно вывести 0
print(str(r1))           # Должно вывести "1/2"

# Основной тест для полиномов
p1 = RatPoly([RatNum(1), RatNum(2)])
print(p1.value_of(RatNum(3)))  # Должно вернуть 7

# Продвинутые тесты
p2 = p1.differentiate()
print(p2)  # Должно показать "2"

p3 = p1.integrate(RatNum(0), RatNum(1))
print(p3)  # Должно показать "2.5"

# Дополнительные тесты
r2 = RatNum(3, 4)
r3 = r1 + r2
print(r3)  # Должно вернуться "5/4"

p4 = RatPoly([RatNum(1), RatNum(1), RatNum(1)])  # x^2 + x + 1
p5 = p4 * p4
print(p5)  # Должно показать "1 + 2x + 3x^2 + 2x^3 + x^4"