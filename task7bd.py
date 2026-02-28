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

    def edit_review(self, fmid: str, new_rating: int, new_comment: str, author: str):
        """Редактирует существующий отзыв."""
        query = "UPDATE reviews SET rating=%s, comment=%s WHERE fmid=%s AND author=%s;"
        with closing(psycopg2.connect(**self.db_connector.db_config)) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (new_rating, new_comment, fmid, author))
                conn.commit()

    def remove_review(self, fmid: str, author: str):
        """Удаляет отзыв текущего пользователя."""
        query = "DELETE FROM reviews WHERE fmid=%s AND author=%s;"
        with closing(psycopg2.connect(**self.db_connector.db_config)) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (fmid, author))
                conn.commit()
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
        longitude: float = None,
        market_name_part: Optional[str] = None,
        fmid: Optional[int] = None  
        ) -> List[Dict]:
        conditions = []
        args = []
        
        if city:
            conditions.append("addresses.city=%s")
            args.append(city)
        if state:
            conditions.append("addresses.state=%s")
            args.append(state)
        if zip_code:
            conditions.append("addresses.zip=%s")
            args.append(zip_code)
            
        # Расстояние считаем только при наличии координат
        if max_distance_miles is not None and latitude is not None and longitude is not None:
        # Перемещаем расчет расстояния внутрь WHERE
          distance_condition = f"""ACOS(SIN(RADIANS({latitude}))*SIN(RADIANS(coordinates.latitude)) +
                                 COS(RADIANS({latitude}))*COS(RADIANS(coordinates.latitude)) *
                                 COS(RADIANS(coordinates.longitude-{longitude}))) * {EARTH_RADIUS_MILES} <= %s"""
          conditions.append(distance_condition)
          args.append(max_distance_miles)
    
        # Поиск по частичному названию
        if market_name_part:
            conditions.append("LOWER(markets.MarketName) LIKE LOWER(%s)")
            args.append('%' + market_name_part.lower() + '%')
        # Добавили условие поиска по FMID
        if fmid is not None:
           conditions.append("markets.FMID=%s")  # Прямой поиск по FMID
           args.append(fmid)

        # Формируем базовый запрос
        base_query = """SELECT markets.*, addresses.street, addresses.city, addresses.county, addresses.state, addresses.zip,
                            coordinates.latitude, coordinates.longitude"""
    
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

    def show_details(self, fmid_or_name: str, review_manager: ReviewManager, logged_in_user: Optional[str]):
        # Попытка определить тип ввода: FMID или название
        try:
            fmid = int(fmid_or_name)
            markets = self.find_market_by_criteria(fmid=fmid)
        except ValueError:
            # Если введен фрагмент названия, производим поиск по нему
            markets = self.find_market_by_criteria(market_name_part=fmid_or_name)
        
        if not markets:
            print("Рынок не найден.")
            cmd = input("Для возврата в список отобранных рынков введите любой символ: ").lower()
            return ''
        
        # Если найдено несколько рынков, предложить пользователю выбрать нужный
        if len(markets) > 1:
            print("Найдено несколько рынков, выберите один:")
            for idx, mkt in enumerate(markets):
                print(f"{idx + 1}. {mkt['MarketName']} (FMID: {mkt['FMID']}, город: {mkt['city']})")
            while True:
                     selected_idx = int(input("Выберите номер рынка: ")) - 1
                     
                     # Проверяем валидность индекса
                     if selected_idx > 0 and selected_idx < len(markets):
                       market = markets[selected_idx]
                       break  # Выход из цикла при успешном выборе
                     else:
                          print(f"Ошибка: Номер рынка вне диапазона от 1 до {len(markets)}. Выберите снова.")
        else:
            market = markets[0]
        
        # Загружаем дополнительные поля
        query = """SELECT markets.*, addresses.street, addresses.city, addresses.county, addresses.state, addresses.zip, coordinates.latitude, coordinates.longitude, social_links.facebook_url, social_links.twitter_url, social_links.youtube_url, social_links.other_media_url
                   FROM markets
                   JOIN addresses ON markets.address_id=addresses.id
                   JOIN coordinates ON markets.coordinate_id=coordinates.id
                   LEFT JOIN social_links ON markets.id=social_links.market_id
                   WHERE FMID=%s;"""
        result = self.db_connector.execute_query(query, (market['FMID'],))
        if not result:
            return None
        market = result[0]
        
        # Получаем график работы рынка
        schedule_query = "SELECT * FROM operating_schedule WHERE market_id=%s ORDER BY season_number ASC;"
        schedules = self.db_connector.execute_query(schedule_query, (market[0],))
        schedule_info = "\n".join([
            f"Сезон {i+1}: {sched[3]} ({sched[4]})"
            for i, sched in enumerate(schedules)
        ]) if schedules else "График работы не указан."
        
        # Получаем перечень продуктов, продаваемых на рынке
        product_query = "SELECT * FROM products WHERE market_id=%s;"
        products_result = self.db_connector.execute_query(product_query, (market[0],))
        product_info = "\nПродукты:\n"
        product_columns = ['organic', 'baked_goods', 'cheese', 'crafts', 'flowers', 'eggs', 'seafood', 'herbs', 'vegetables', 'honey', 'jams', 'maple', 'meat', 'nursery', 'nuts', 'plants', 'poultry', 'prepared', 'soap', 'trees', 'wine', 'coffee', 'beans', 'fruits', 'grains', 'juices', 'mushrooms', 'pet_food', 'tofu', 'wild_harvested']
        for col, val in zip(product_columns, products_result[0]):
           if val:
            product_info += f"{col.replace('_', ' ').title()}: Да "
        
        # Генерируем подробную информацию о рынке
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
        Другие медиа: {market[17]}
        График работы:
        {schedule_info}
        Продукты:
        {product_info}
        Дата последнего обновления: {market[6]}
        """
        print(details)
        # Получаем все отзывы по этому рынку
        reviews = review_manager.get_reviews_by_fmid(market[1])
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
        
        # Проверяем, оставил ли текущий пользователь отзыв
        has_existing_review = any(rev["author"] == logged_in_user for rev in reviews)

        if logged_in_user:
          if has_existing_review:
            print("\nВы уже оставили отзыв. Хотите изменить или удалить?")
            change_action = input("Хотите изменить ([C]orrection) или удалить ([D]elete) свой отзыв? Или вернуться обратно ([B]ack)? ").strip().upper()
            if change_action == "C":  # Редактировать отзыв
                new_rating = int(input("Новый рейтинг (от 1 до 5): "))
                new_comment = input("Новый комментарий: ")
                review_manager.edit_review(market[1], new_rating, new_comment, logged_in_user)
                print("Отзыв обновлён.")
            elif change_action == "D":  # Удалить отзыв
                review_manager.remove_review(market[1], logged_in_user)
                print("Отзыв удалён.")
          else:
            # Возможность оставить новый отзыв
            want_to_add_review = input("Хотите оставить отзыв? (Y/N): ").strip().upper()
            if want_to_add_review == "Y":
                while True:
                     rating_input = input("Оцените рынок (от 1 до 5 звёзд): ")
                     try:
                         rating = int(rating_input)
                         if rating < 1 or rating > 5:
                           raise ValueError("Рейтинг должен быть числом от 1 до 5.")
                           break
                     except ValueError:
                           print("Ошибка: Неправильный формат оценки. Используйте числа от 1 до 5.")
                comment = input("Комментарий (можно оставить пустым): ")
                review_manager.add_review(market[1], rating, comment, logged_in_user)
                print("Отзыв успешно добавлен.")

        # Пауза перед возвратом в главное меню
        quit = input('Введите любую букву для возврата в список:')
        return ''

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
                    # Запрашиваем имя и фамилию пользователя из базы данных
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
        
        cmd = input("Следующая страница ('n'), предыдущая ('p'), подробности ('d'), назад ('b'): ").lower()
        if cmd == 'n':
            current_page += 1
        elif cmd == 'p':
            current_page -= 1
        elif cmd == 'd':
            detail_choice = input("Введите FMID или название рынка для подробностей: ")
            details = manager.show_details(detail_choice, review_manager, logged_in_user)
            if details:
                print("\nПодробная информация о рынке:")
                print(details)
                cmd = input("Для возврата введите любой символ: ").lower()
            '''
            else:
                print("Рынок не найден.")
            '''
        elif cmd == 'b':
            break
        else:
            print("Неправильная команда.")

def filter_and_sort_by_fixed_rating(filtered_markets: List[Dict], review_manager: ReviewManager, order='desc'):
    """
    Возвращает список уже предварительно отфильтрованных рынков, отсортированных по зафиксированному рейтингу (от 1 до 5).
    :param filtered_markets: предварительный список отфильтрованных рынков
    :param review_manager: объект ReviewManager
    :param order: порядок сортировки ('asc' — возрастающая, 'desc' — убывающая)
    :return: список объектов рынка, отсортированный по рейтингу
    """
    # Строим словарь рейтингов для каждого рынка
    rated_markets = []
    for market in filtered_markets:
        reviews = review_manager.get_reviews_by_fmid(market['FMID'])
        # Выбираем лучший (самый высокий) рейтинг для рынка
        best_rating = max(review['rating'] for review in reviews) if reviews else 0
        rated_markets.append({'market': market, 'best_rating': best_rating})

    # Сортируем рынки по лучшему рейтингу
    rated_markets.sort(key=lambda x: x['best_rating'], reverse=(order != 'asc'))

    return [rm['market'] for rm in rated_markets]

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
    do_sort = input("Применить сортировку по рейтингу? [Y]/N: ").strip().upper() != 'N'
    
    # Определим порядок сортировки только если сортировка включена
    if do_sort:
        sort_order = input("Порядок сортировки по рейтингу [A]scending/[D]escending (оставьте пустым для Descending): ").strip().upper() or 'DESC'
    else:
        sort_order = None  # Неважно, если сортировка отключена

    if lat and lon:
        max_dist_input = input("Максимальное расстояние в милях: ")
        if max_dist_input.strip():
            max_dist = float(max_dist_input)
        else:
            max_dist = None  # Если поле пустое, устанавливаем None
        found_markets = manager.find_market_by_criteria(city, state, zip_code, max_dist, float(lat), float(lon))
    else:
        found_markets = manager.find_market_by_criteria(city, state, zip_code)

     # Фильтруем и сортируем по рейтингу
     # Производим сортировку только если сортировка включена
    if do_sort:
        filtered_markets = filter_and_sort_by_fixed_rating(found_markets, review_manager, sort_order)
    else:
        filtered_markets = found_markets  # Сохраняем исходный порядок, если сортировка отключена


    if found_markets:
        pages = manager.paginate_results(filtered_markets)
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
                        # Запрашиваем имя и фамилию пользователя из базы данных
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
                detail_choice = input("Введите FMID или название рынка для подробностей: ")
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
# ...
def add_review(review_manager: ReviewManager, market_manager: MarketManager, logged_in_user: str):
    """
    Добавляет новый отзыв пользователю.
    Поддерживает поиск рынка как по FMID, так и по частичному названию.
    """
    # Спрашиваем FMID или название рынка
    fmid_or_name = input("Введите FMID или название рынка: ")
    
    # Ищем рынок по указанному значению
    try:
        # Пробуем преобразовать значение в число, предполагая, что это FMID
        fmid = int(fmid_or_name)
        markets = market_manager.find_market_by_criteria(fmid=fmid)
    except ValueError:
        # Иначе рассматриваем как название и выполняем поиск по названию
        markets = market_manager.find_market_by_criteria(market_name_part=fmid_or_name)
    
    if not markets:
        print("Рынок не найден.")
        return
    
    # Если найдена одна запись, используем её
    if len(markets) == 1:
        chosen_market = markets[0]['FMID']
    else:
        # Предлагают выбрать среди найденных рынков
        print("Найдено несколько рынков, выберите один:")
        for idx, mkt in enumerate(markets):
            print(f"{idx + 1}. {mkt['MarketName']} (FMID: {mkt['FMID']}, город: {mkt['city']})")
        while True:
                     selection = int(input("Выберите номер рынка: ")) - 1
                     
                     # Проверяем валидность индекса
                     if selection > 0 and selection < len(markets):
                       chosen_market = markets[selection]['FMID']
                       break  # Выход из цикла при успешном выборе
                     else:
                          print(f"Ошибка: Номер рынка вне диапазона от 1 до {len(markets)}. Выберите снова.")
    
    # Теперь получаем полную информацию о выбранном рынке
    detailed_market = market_manager.find_market_by_criteria(fmid=chosen_market)[0]
    
    # Дополнительный запрос для получения полной информации
    query_full_info = """SELECT markets.*, addresses.street, addresses.city, addresses.county, addresses.state, addresses.zip, coordinates.latitude, coordinates.longitude, social_links.facebook_url, social_links.twitter_url, social_links.youtube_url, social_links.other_media_url
                         FROM markets
                         JOIN addresses ON markets.address_id=addresses.id
                         JOIN coordinates ON markets.coordinate_id=coordinates.id
                         LEFT JOIN social_links ON markets.id=social_links.market_id
                         WHERE FMID=%s;"""
    result = market_manager.db_connector.execute_query(query_full_info, (chosen_market,))
    if not result:
        return None
    market = result[0]
    
    # Получаем график работы рынка
    schedule_query = "SELECT * FROM operating_schedule WHERE market_id=%s ORDER BY season_number ASC;"
    schedules = market_manager.db_connector.execute_query(schedule_query, (market[0],))
    schedule_info = "\n".join([
        f"Сезон {i+1}: {sched[3]} ({sched[4]})"
        for i, sched in enumerate(schedules)
    ]) if schedules else "График работы не указан."
    
    # Получаем перечень продуктов, продаваемых на рынке
    product_query = "SELECT * FROM products WHERE market_id=%s;"
    products_result = market_manager.db_connector.execute_query(product_query, (market[0],))
    product_info = "\nПродукты:\n"
    product_columns = ['organic', 'baked_goods', 'cheese', 'crafts', 'flowers', 'eggs', 'seafood', 'herbs', 'vegetables', 'honey', 'jams', 'maple', 'meat', 'nursery', 'nuts', 'plants', 'poultry', 'prepared', 'soap', 'trees', 'wine', 'coffee', 'beans', 'fruits', 'grains', 'juices', 'mushrooms', 'pet_food', 'tofu', 'wild_harvested']
    for col, val in zip(product_columns, products_result[0]):
        if val:
            product_info += f"{col.replace('_', ' ').title()}: Да "
    
    # Печать всей доступной информации о рынке
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
        Другие медиа: {market[17]}
        График работы:
        {schedule_info}
        Продукты:
        {product_info}
        Дата последнего обновления: {market[6]}
        """
    print(details)
    '''   
    print(f"FMID: {market['FMID']}")
    print(f"Название: {market['MarketName']}")
    print(f"Улица: {market['street']}")
    print(f"Город: {market['city']}")
    print(f"Округ: {market['county']}")
    print(f"Штат: {market['state']}")
    print(f"Веб-сайт: {market['website']}")
    print(f"Социальные сети:")
    print(f"Facebook: {market['facebook_url']}")
    print(f"Twitter: {market['twitter_url']}")
    print(f"Youtube: {market['youtube_url']}")
    print(f"Другие медиа: {market['other_media_url']}")
    print(f"График работы:\n{schedule_info}")
    print(f"Продукты:\n{product_info}")
    print(f"Дата последнего обновления: {market['update_time']}")
    '''
    # Получаем и печатаем существующие отзывы
    reviews = review_manager.get_reviews_by_fmid(chosen_market)
    if reviews:
        print("\nОтзывы пользователей:")
        for rev in reviews:
            # Берём имя и фамилию пользователя по логину из БД
            query_get_username = "SELECT firstname, lastname FROM users WHERE username=%s;"
            user_data = market_manager.db_connector.execute_query(query_get_username, (rev['author'],))
            if user_data:
                first_name, last_name = user_data[0]
                full_name = f"{first_name} {last_name}"
            else:
                full_name = "(неизвестный)"
            print(f"Автор: {full_name} | Рейтинг: {rev['rating']} | Коммент.: {rev['comment']}")
    else:
        print("\nОтзывов пока нет.")

    existing_review = next((r for r in reviews if r['author'] == logged_in_user), None)
    
    if existing_review:
        # Пользователь уже оставил отзыв
        print("\nВы уже оценили этот рынок.")
        print(f"Текущий рейтинг: {existing_review['rating']}, Комментарий: {existing_review['comment']}")
        action = input("Хотите изменить ([C]orrection) или удалить ([D]elete) свой отзыв? Или вернуться обратно ([B]ack)? ").strip().upper()
        
        if action == 'C':
            # Изменить отзыв
            while True:
                try:
                    new_rating = int(input("Введите новый рейтинг (от 1 до 5): "))
                    if 1 <= new_rating <= 5:
                        break
                    else:
                        print("Рейтинг должен быть числом от 1 до 5.")
                except ValueError:
                    print("Ошибка: введённое значение должно быть числом.")
            new_comment = input("Введите новый комментарий: ")
            review_manager.edit_review(chosen_market, new_rating, new_comment, logged_in_user)
            print("Отзыв успешно изменён.")
        elif action == 'D':
            # Удалить отзыв
            review_manager.remove_review(chosen_market, logged_in_user)
            print("Отзыв успешно удалён.")
        else:
            print("Возвращаемся в предыдущее меню.")
    else:
        # Новый отзыв
        want_to_add_review = input("Хотите оставить отзыв? (Y/N): ").strip().upper()
        if want_to_add_review == "Y":
          while True:
               try:
                   rating = int(input("\nОцените рынок (от 1 до 5 звёзд): "))
                   if 1 <= rating <= 5:
                     break
                   else:
                        print("Ошибочный диапазон. Введите число от 1 до 5.")
               except ValueError:
                     print("Ошибка: введённое значение должно быть числом.")
          comment = input("Комментарий (можно оставить пустым): ")
          review_manager.add_review(chosen_market, rating, comment, logged_in_user)
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
            add_review(review_mgr, market_mgr, logged_in_user)
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