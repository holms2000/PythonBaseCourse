import psycopg2
from contextlib import closing
import math
from datetime import datetime
from hashlib import sha256
from typing import List, Dict, Optional
from functools import partial

# Константы
EARTH_RADIUS_MILES = 3958.8  # Радиус Земли в милях

# Конфигурация подключения к базе данных
db_config = {
    'dbname': 'farmers_db',
    'user': 'sasha',
    'password': '1973',
    'host': 'localhost',
    'port': '5433'
}

# Класс для управления соединением с базой данных
class DatabaseConnection:
    def __init__(self, db_config):
        self.db_config = db_config

    def execute_query(self, query, params=None):
        with closing(psycopg2.connect(**self.db_config)) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()

    def insert_data(self, table, data):
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        values = tuple(data.values())
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders});"
        with closing(psycopg2.connect(**self.db_config)) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, values)
                conn.commit()

    def update_data(self, table, set_values, condition):
        set_clause = ", ".join([f"{key}=%s" for key in set_values.keys()])
        where_clause = " AND ".join([f"{k}=%s" for k in condition.keys()])
        values = list(set_values.values()) + list(condition.values())
        query = f"UPDATE {table} SET {set_clause} WHERE {where_clause};"
        with closing(psycopg2.connect(**self.db_config)) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, values)
                conn.commit()

    def delete_data(self, table, condition):
        where_clause = " AND ".join([f"{k}=%s" for k in condition.keys()])
        values = tuple(condition.values())
        query = f"DELETE FROM {table} WHERE {where_clause};"
        with closing(psycopg2.connect(**self.db_config)) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, values)
                conn.commit()

# Менеджер пользователей
class UserManager:
    def __init__(self, db_connector):
        self.db_connector = db_connector

    def check_user_exists(self, username: str) -> bool:
        query = "SELECT COUNT(*) FROM users WHERE username=%s;"
        result = self.db_connector.execute_query(query, (username,))
        return result[0][0] > 0

    def create_user(self, username: str, password: str, firstname: str, lastname: str):
        hashed_password = sha256(password.encode()).hexdigest()
        data = {
            'username': username,
            'password_hash': hashed_password,
            'firstname': firstname,
            'lastname': lastname
        }
        self.db_connector.insert_data('users', data)

    def verify_login(self, username: str, password: str) -> bool:
        query = "SELECT password_hash FROM users WHERE username=%s;"
        result = self.db_connector.execute_query(query, (username,))
        if not result:
            return False
        stored_hash = result[0][0]
        provided_hash = sha256(password.encode()).hexdigest()
        return stored_hash == provided_hash

# Менеджер отзывов
class ReviewManager:
    def __init__(self, db_connector):
        self.db_connector = db_connector

    def add_review(self, fmid: str, rating: int, comment: str, author: str):
        data = {
            'fmid': fmid,
            'rating': rating,
            'comment': comment,
            'author': author
        }
        self.db_connector.insert_data('reviews', data)

    def get_reviews_by_fmid(self, fmid: str) -> List[Dict]:
        query = "SELECT * FROM reviews WHERE fmid=%s;"
        results = self.db_connector.execute_query(query, (fmid,))
        return [dict(zip(('id', 'fmid', 'rating', 'comment', 'author'), row)) for row in results]

    def delete_review(self, fmid: str, author: str):
        condition = {'fmid': fmid, 'author': author}
        self.db_connector.delete_data('reviews', condition)

# Менеджер рынков
class MarketManager:
    def __init__(self, db_connector):
        self.db_connector = db_connector

    def find_market_by_criteria(
        self,
        city: Optional[str] = None,
        state: Optional[str] = None,
        zip_code: Optional[str] = None,
        max_distance_miles: float = None,
        latitude: float = None,
        longitude: float = None
    ) -> List[Dict]:
        conditions = []
        args = []
        
        if city:
            conditions.append("addresses.city=%s")
            args.append(city)
        if state:
            conditions.append("markets.state=%s")
            args.append(state)
        if zip_code:
            conditions.append("addresses.zip=%s")
            args.append(zip_code)
            
        # Расстояние считаем только при наличии координат
        if max_distance_miles is not None and latitude is not None and longitude is not None:
            distance_sql = f"""ACOS(SIN(RADIANS(%s))*SIN(RADIANS(coordinates.latitude)) +
                                COS(RADIANS(%s))*COS(RADIANS(coordinates.latitude)) *
                                COS(RADIANS(coordinates.longitude-%s))) * %s AS distance"""
            conditions.append(f"distance <= %s")
            args.extend([latitude, latitude, longitude, EARTH_RADIUS_MILES, max_distance_miles])
    
        # Формируем базовый запрос
        base_query = """SELECT markets.*, addresses.street, addresses.city, addresses.county, addresses.state, addresses.zip,
                            coordinates.latitude, coordinates.longitude"""
        if max_distance_miles:
            base_query += f", {distance_sql}"  # добавляем вычисленное поле distance
    
        # Объединение таблиц
        query = f"{base_query}\nFROM markets\nJOIN addresses ON markets.address_id=addresses.id\nJOIN coordinates ON markets.coordinate_id=coordinates.id"
    
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
    
        results = self.db_connector.execute_query(query, args)
        return [dict(zip(('id', 'FMID', 'MarketName', 'website', 'address_id', 'coordinate_id', 'update_time', 'street', 'city', 'county', 'state', 'zip', 'latitude', 'longitude', 'distance' if max_distance_miles else ''), row)) for row in results]

    def sort_markets(self, markets: List[Dict], field: str, reverse=False) -> List[Dict]:
        sorted_markets = sorted(markets, key=lambda x: x[field], reverse=reverse)
        return sorted_markets

    def paginate_results(self, markets: List[Dict]) -> List[List[Dict]]:
        PAGE_SIZE = 10
        pages = []
        num_pages = math.ceil(len(markets) / PAGE_SIZE)
        for i in range(num_pages):
            start = i * PAGE_SIZE
            end = start + PAGE_SIZE
            pages.append(markets[start:end])
        return pages

    def show_details(self, fmid: str, review_manager: ReviewManager, logged_in_user: Optional[str]):
        query = """SELECT markets.*, addresses.street, addresses.city, addresses.county, addresses.state, addresses.zip, coordinates.latitude, coordinates.longitude, social_links.facebook_url, social_links.twitter_url, social_links.youtube_url, social_links.other_media_url
                   FROM markets
                   JOIN addresses ON markets.address_id=addresses.id
                   JOIN coordinates ON markets.coordinate_id=coordinates.id
                   LEFT JOIN social_links ON markets.id=social_links.market_id
                   WHERE FMID=%s;"""
        result = self.db_connector.execute_query(query, (fmid,))
        if not result:
            return None
        market = result[0]
        # Получаем график работы рынка
        schedule_query = "SELECT * FROM operating_schedule WHERE market_id=%s ORDER BY season_number ASC;"
        schedules = self.db_connector.execute_query(schedule_query, (market[0],))  # Используем индексирование кортежа
        schedul = schedules[0]
        schedule_info = "\n".join([
            f"Сезон {i+1}: {schedul[3]} ({schedul[4]})"
            for i, sched in enumerate(schedules)
        ]) if schedules else "График работы не указан."

        # Получаем перечень продуктов, продаваемых на рынке
        product_query = "SELECT * FROM products WHERE market_id=%s;"
        products_result = self.db_connector.execute_query(product_query, (market[0],))  # Аналогично, обращаемся по индексу
        if products_result:
            product_info = "\nПродукты:\n"
            product_row = products_result[0]
            prod=['organic','baked_goods','cheese','crafts','flowers','eggs','seafood','herbs','vegetables','honey','jams','maple','meat','nursery','nuts','plants','poultry','prepared','soap','trees','wine','coffee','beans','fruits','grains','juices','mushrooms','pet_food','tofu','wild_harvested']
            i = 0
            for value in product_row:
                if value==True:
                   product_info += f"{prod[i]}: Да " #\n"
                i+=1
        else:
            product_info = "Продукты отсутствуют."

        details = f"""
        Подробная информация о рынке FMID: {market[1]} 
        Название: {market[2]}
        Улица: {market[7]}
        Город: {market[8]}
        Округ: {market[9]}
        Штат: {market[10]}
        Индекс: {market[11]}
        Широта: {market[12]}, Долгота: {market[13]}
        Веб-сайт: {market[3]}
        Социальные сети:
        Facebook: {market[14]}
        Twitter: {market[15]}
        Youtube: {market[16]}
        Other media: {market[17]}
        График работы:
        {schedule_info}
        {product_info}
        Дата последнего обновления: {market[6]}
        """
        print(details)
        # Получаем все отзывы по этому рынку
        reviews = review_manager.get_reviews_by_fmid(fmid)
        print("\nОтзывы от всех пользователей:")
        for rev in reviews:
            # Взять имя и фамилию пользователя по логину из БД
            query_get_username = "SELECT firstname, lastname FROM users WHERE username=%s;"
            user_data = self.db_connector.execute_query(query_get_username, (rev['author'],))
            if user_data:
                first_name, last_name = user_data[0]
                full_name = f"{first_name} {last_name}"
            else:
                full_name = "(неизвестный)"
            print(f"Автор: {full_name} | Рейтинг: {rev['rating']} | Коммент.: {rev['comment']}")
        quit = input('введите любую букву для возврата в список:')
        return '' #details

# Вспомогательная функция показа основного меню
def prompt_menu() -> str:
    """
    Показывает основное меню и возвращает выбор пользователя.
    """
    menu_items = [
        ("Просмотреть все рынки", "view_all"),
        ("Искать рынок", "search"),
        ("Оставить отзыв", "add_review"),
        ("Выход", "exit")
    ]
    print("\nМеню:")
    for idx, item in enumerate(menu_items):
        print(f"{idx + 1}. {item[0]}")
    choice = input("Ваш выбор: ")
    try:
        menu = menu_items[int(choice)-1][1]
    except:
        menu = choice
    return menu

# Просмотр всех рынков
def view_all_markets(manager: MarketManager, review_manager: ReviewManager, logged_in_user: Optional[str]):
    """
    Функция просмотра всех рынков с пагинацией и отображением отзывов.
    """
    all_markets = manager.find_market_by_criteria()
    if not all_markets:
        print("Нет данных о рынках.")
        return
    pages = manager.paginate_results(all_markets)
    current_page = 0
    while current_page < len(pages):
        print(f"\nСтраница {current_page + 1}:")
        for market in pages[current_page]:
           # Получаем отзывы для текущего рынка
          reviews = review_manager.get_reviews_by_fmid(market['FMID'])
          reviews_str = ""
          if reviews:
            for rev in reviews:
                # Прямо запрашиваем имя и фамилию пользователя из базы данных
                query_get_username = "SELECT firstname, lastname FROM users WHERE username=%s;"
                user_data = manager.db_connector.execute_query(query_get_username, (rev['author'],))
                if user_data:
                    first_name, last_name = user_data[0]
                    full_name = f"{first_name} {last_name}"
                else:
                    full_name = "(неизвестный)"
                reviews_str += f"    Автор: {full_name} | Рейтинг: {rev['rating']} | Коммент.: {rev['comment']}\n"
          else:
            reviews_str = "    Нет отзывов.\n"
          print(f"- Название: {market['MarketName']}\n"
                  f"  FMID: {market['FMID']}\n"
                  f"  Город: {market['city']}\n"
                  f"  Штат: {market['state']}\n"
                  f"  Индекс: {market['zip']}\n"
                  f"  Отзывы:\n{reviews_str}\n")
        cmd = input("Следующая страница ('n'), предыдущая ('p'), подробнее ('d'), назад ('b'): ").lower()
        if cmd == 'n':
            current_page += 1
        elif cmd == 'p':
            current_page -= 1
        elif cmd == 'd':
            detail_choice = input("Введите FMID рынка для подробностей: ")
            details = manager.show_details(detail_choice, review_manager, logged_in_user)
            if details:
                print("\nПодробная информация о рынке:")
                print(details)
                cmd = input("Для возврата введите любой символ: ").lower()
            else:
                print("Рынок не найден.")
        elif cmd == 'b':
            break
        else:
            print("Неправильная команда.")

# Поиск рынков
def search_markets(manager: MarketManager, review_manager: ReviewManager, logged_in_user: Optional[str]):
    """
    Функция поиска рынков по заданным критериям.
    """
    city = input("Город (оставьте пустым, если не важен): ") or None
    state = input("Штат (оставьте пустым, если не важен): ") or None
    zip_code = input("Индекс (оставьте пустым, если не важен): ") or None
    lat = input("Широта для расчета расстояния (оставьте пустым, если не важно): ") or None
    lon = input("Долгота для расчета расстояния (оставьте пустым, если не важно): ") or None
    if lat and lon:
        max_dist = float(input("Максимальное расстояние в милях: "))
        found_markets = manager.find_market_by_criteria(city, state, zip_code, max_dist, float(lat), float(lon))
    else:
        found_markets = manager.find_market_by_criteria(city, state, zip_code)
    if found_markets:
        pages = manager.paginate_results(found_markets)
        current_page = 0
        while current_page < len(pages):
            print(f"\nСтраница {current_page + 1}:")
            for market in pages[current_page]:
                # Получаем отзывы для текущего рынка
                reviews = review_manager.get_reviews_by_fmid(market['FMID'])
                # Определяем строку с отзывами или уведомление об их отсутствии
                reviews_str = ""
                if reviews:
                  for rev in reviews:
                  # Прямо запрашиваем имя и фамилию пользователя из базы данных
                      query_get_username = "SELECT firstname, lastname FROM users WHERE username=%s;"
                      user_data = manager.db_connector.execute_query(query_get_username, (rev['author'],))
                      if user_data:
                        first_name, last_name = user_data[0]
                        full_name = f"{first_name} {last_name}"
                      else:
                          full_name = "(неизвестный)"
                  reviews_str += f"    Автор: {full_name} | Рейтинг: {rev['rating']} | Коммент.: {rev['comment']}\n"
                else:
                     reviews_str = "    Нет отзывов.\n"
                print(f"- Название: {market['MarketName']}\n"
                      f"  FMID: {market['FMID']}\n"
                      f"  Город: {market['city']}\n"
                      f"  Штат: {market['state']}\n"
                      f"  Индекс: {market['zip']}\n"
                      f"  Отзывы:\n{reviews_str}\n")
            cmd = input("Следующая страница ('n'), предыдущая ('p'), подробнее ('d'), назад ('b'): ").lower()
            if cmd == 'n':
                current_page += 1
            elif cmd == 'p':
                current_page -= 1
            elif cmd == 'd':
                detail_choice = input("Введите FMID рынка для подробностей: ")
                details = manager.show_details(detail_choice, review_manager, logged_in_user)
                if details:
                    print("\nПодробная информация о рынке:")
                    print(details)
                    cmd = input("Для возврата введите любой символ: ").lower()
                else:
                    print("Рынок не найден.")
            elif cmd == 'b':
                break
            else:
                print("Неправильная команда.")
    else:
        print("Нет соответствующих рынков.")

# Оставление отзыва
def add_review(review_manager: ReviewManager, logged_in_user: str):
    """
    Добавляем новый отзыв пользователю.
    """
    fmid = input("Введите FMID рынка: ")
    rating = int(input("Оцените рынок (1-5 звезд): "))
    comment = input("Комментарий (можете оставить пустым): ")
    review_manager.add_review(fmid, rating, comment, logged_in_user)
    print("Отзыв успешно добавлен.")

# Основная логика приложения
def run_application(logged_in_user):
    """
    Основной цикл работы приложения.
    """
    review_mgr = ReviewManager(db_connector)
    market_mgr = MarketManager(db_connector)
    user_mgr = UserManager(db_connector)
    while True:
        action = prompt_menu()
        if action == "exit":
            print("До свидания!")
            break
        elif action == "view_all":
            view_all_markets(market_mgr, review_mgr, logged_in_user)
        elif action == "search":
            search_markets(market_mgr, review_mgr, logged_in_user)
        elif action == "add_review":
            if logged_in_user is None:
                print("Сначала войдите в аккаунт.")
                continue
            add_review(review_mgr, logged_in_user)
        else:
            print("Неизвестная операция.")

# Логин или регистрация пользователя
def login_or_register(user_mgr: UserManager):
    """
    Вход или регистрация пользователя.
    """
    while True:
        choice = input("Хотите войти (L) или зарегистрироваться (R)? (Q для выхода): ").upper()
        if choice == 'L':
            username = input("Логин пользователя: ")
            password = input("Пароль: ")
            if user_mgr.verify_login(username, password):
                print(f"Привет, {username}!")
                return username
            else:
                print("Неверные данные. Попробуйте снова.")
        elif choice == 'R':
            username = input("Создать новый логин: ")
            password = input("Создать новый пароль: ")
            firstname = input("Ввести имя пользователя: ")
            lastname = input("Ввести фамилию пользователя: ")
            try:
                user_mgr.create_user(username, password, firstname, lastname)
                print(f"Поздравляю, {firstname} {lastname}! Вы зарегистрировались.")
                return username
            except Exception as e:
                print(e)
        elif choice == 'Q':
            exit()
        else:
            print("Некорректная команда.")

# Точка входа в приложение
if __name__ == "__main__":
    db_connector = DatabaseConnection(db_config)
    user_mgr = UserManager(db_connector)
    logged_in_user = login_or_register(user_mgr)
    run_application(logged_in_user)