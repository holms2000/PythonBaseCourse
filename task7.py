import csv
import os
import sys
import math
from datetime import datetime
from hashlib import sha256
from typing import List, Dict, Optional
from functools import partial


# Константы
MARKETS_CSV = 'Export.csv'
REVIEWS_CSV = 'reviews.csv'
USERS_CSV = 'users.csv'
MAX_REVIEWS_PER_PAGE = 10
PAGE_SIZE = 10  # Размер страницы для пагинации

# Формула Haversine для расчета расстояния
EARTH_RADIUS_MILES = 3958.8  # Радиус Земли в милях

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    ''' 
    @requires: lat1, lon1, lat2, lon2 ϵ float
    @modifies: None
    @effects: None
    @raises: None
    @returns: distance between two points on the earth using Haversine formula
    '''
    """
    Расчет расстояния между двумя точками на Земле с использованием формулы Haversine.
    """
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return EARTH_RADIUS_MILES * c


class ReviewManager:
    def __init__(self, reviews_csv: str):
        self.reviews_csv = reviews_csv
        self.load_reviews()

    def load_reviews(self):
        ''' 
        @requires: None
        @modifies: None
        @effects: Loads reviews data from a CSV file into memory
        @raises: None
        @returns: None
        '''
        """
        Загружает существующие отзывы из CSV.
        """
        if not os.path.exists(self.reviews_csv):
            with open(self.reviews_csv, 'w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=['fmid', 'rating', 'comment', 'author'])
                writer.writeheader()
            self.reviews = []
        else:
            with open(self.reviews_csv, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                self.reviews = list(reader)

    def add_review(self, fmid: str, rating: int, comment: str, author: str):
        ''' 
        @requires: fmid, rating, comment, author ϵ string
        @modifies: Reviews list and CSV file
        @effects: Adds a new review to the system
        @raises: None
        @returns: None
        '''
        """
        Добавляет новый отзыв к выбранному фермерскому рынку.
        """
        new_review = {
            'fmid': fmid,
            'rating': rating,
            'comment': comment,
            'author': author
        }
        self.reviews.append(new_review)
        self.save_reviews()

    def save_reviews(self):
        ''' 
        @requires: None
        @modifies: Reviews CSV file
        @effects: Writes reviews back to the CSV file
        @raises: None
        @returns: None
        '''
        """
        Сохраняет отзывы в CSV-файл.
        """
        with open(self.reviews_csv, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=self.reviews[0].keys())
            writer.writeheader()
            writer.writerows(self.reviews)

    def get_reviews_by_fmid(self, fmid: str) -> List[Dict]:
        ''' 
        @requires: fmid ϵ string
        @modifies: None
        @effects: Filters reviews based on fmid
        @raises: None
        @returns: All reviews of specific market
        '''
        """
        Возвращает все отзывы конкретного рынка.
        """
        return [review for review in self.reviews if review['fmid'] == fmid]
    
    def delete_review(self, fmid: str, author: str):
        ''' 
        @requires: fmid, author ϵ string
        @modifies: Reviews list and CSV file
        @effects: Deletes a user's review for a particular market
        @raises: None
        @returns: Boolean indicating success/failure
        '''
        """
        Удаляет отзыв пользователя по идентификатору рынка и авторству.
        """
        # Проходим по отзывам и находим тот, который соответствует запросу
        to_delete = next((review for review in self.reviews if review['fmid'] == fmid and review['author'] == author), None)
        if to_delete:
            self.reviews.remove(to_delete)
            self.save_reviews()
            return True
        return False

    def select_review_to_delete(self, fmid: str, author: str):
        ''' 
        @requires: fmid, author ϵ string
        @modifies: None
        @effects: Helps user choose which review to delete
        @raises: None
        @returns: Selected review object or None
        '''
        """
        Помогает пользователю выбрать отзыв для удаления.
        """
        matching_reviews = [review for review in self.reviews if review['fmid'] == fmid and review['author'] == author]
        if not matching_reviews:
            print("Нет отзывов, доступных для удаления.")
            return None
        print("Доступные отзывы для удаления:")
        for idx, review in enumerate(matching_reviews):
            print(f"{idx+1}. Рейтинг: {review['rating']}, Комментарий: {review['comment']}")
        choice = input("Выберите номер отзыва для удаления (или введите 'q' для отмены): ")
        if choice.lower() == 'q':
            return None
        try:
            index = int(choice) - 1
            selected_review = matching_reviews[index]
            return selected_review
        except (IndexError, ValueError):
            print("Недопустимый выбор.")
            return None

class UserManager:
    def __init__(self, users_csv: str):
        self.users_csv = users_csv
        self.load_users()

    def load_users(self):
       ''' 
       @requires: None
       @modifies: None
       @effects: Loads user information from a CSV file
       @raises: None
       @returns: None
       '''
       if not os.path.exists(self.users_csv):
         with open(self.users_csv, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=['username', 'password_hash', 'firstname', 'lastname'])
            writer.writeheader()
         self.users = {}
       else:
        with open(self.users_csv, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            # Здесь обязательно нужен полный словарь, а не пара "ключ-значение"
            self.users = {row['username']: row for row in reader}

    def check_user_exists(self, username: str) -> bool:
        ''' 
        @requires: username ϵ string
        @modifies: None
        @effects: Checks whether a user exists
        @raises: None
        @returns: Boolean indicating existence
        '''
        """
        Проверяет наличие пользователя.
        """
        return username in self.users

    def create_user(self, username: str, password: str, firstname: str, lastname: str):
       ''' 
       @requires: username, password, firstname, lastname ϵ string
       @modifies: Users dictionary and CSV file
       @effects: Creates a new user account
       @raises: ValueError if validation fails
       @returns: None
       '''
       """
       Создание нового пользователя с хэшированным паролем.
       """
       # Проверка, что все поля заполнены
       if not username.strip() or not password.strip() or not firstname.strip() or not lastname.strip():
         raise ValueError("Все поля должны быть заполнены.")
    
       if self.check_user_exists(username):
         raise ValueError("Пользователь уже существует.")
       hashed_password = sha256(password.encode()).hexdigest()
       # Создаем словарь пользователя
       user_dict = {
        'username': username,
        'password_hash': hashed_password,
        'firstname': firstname,
        'lastname': lastname
       }
       # Добавляем нового пользователя в словарь
       self.users[username] = user_dict
       self.save_users()

    def verify_login(self, username: str, password: str) -> bool:
       ''' 
       @requires: username, password ϵ string
       @modifies: None
       @effects: Authenticates user credentials
       @raises: None
       @returns: Boolean indicating successful login
       '''
       """
       Аутентификация пользователя.
       """
       if username not in self.users:
         print("Пользователь не найден.")
         return False
       user_data = self.users[username]
       stored_hash = user_data['password_hash']
       provided_hash = sha256(password.encode()).hexdigest()
       if stored_hash != provided_hash:
         print("Неверный пароль.")
       return stored_hash == provided_hash

    def save_users(self):
       ''' 
       @requires: None
       @modifies: Users CSV file
       @effects: Persists user data to disk
       @raises: None
       @returns: None
       '''
       """
       Сохраняет пользователей в CSV-файл, дописывая новые данные.
       """
       # Если файл уже существует, читаем текущие данные
       if os.path.exists(self.users_csv):
         with open(self.users_csv, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            existing_data = list(reader)
       else:
           existing_data = []

       # Получаем новый список пользователей
       new_users_list = list(self.users.values())

       # Проверка корректности новых данных
       for user in new_users_list:
          assert isinstance(user, dict), f"Новый пользователь имеет неверный тип: {type(user)}"

       # Объединяем существующие данные с новыми пользователями
       final_data = existing_data + new_users_list

       # Открываем файл для записи
       with open(self.users_csv, 'w', newline='', encoding='utf-8') as file:
           fields = ['username', 'password_hash', 'firstname', 'lastname']
           writer = csv.DictWriter(file, fieldnames=fields)
           writer.writeheader()
           writer.writerows(final_data)


class MarketManager:
    def __init__(self, markets_csv: str):
        self.markets_csv = markets_csv
        self.load_markets()

    def load_markets(self):
        ''' 
         @requires: None
         @modifies: None
         @effects: Loads markets data from a CSV file
         @raises: None
         @returns: None
        '''
        """
        Загружает фермерские рынки из CSV.
        """
        if not os.path.exists(self.markets_csv):
            with open(self.markets_csv, 'w', newline='', encoding='utf-8') as file:
                fields = [
                    'FMID', 'MarketName', 'Website', 'Facebook', 'Twitter',
                    'Youtube', 'OtherMedia', 'street', 'city', 'county', 'state',
                    'zip', 'Season1Date', 'Season1Time', 'Season2Date', 'Season2Time',
                    'Season3Date', 'Season3Time', 'Season4Date', 'Season4Time', 'x', 'y',
                    'Location', 'Credit', 'WIC', 'WICcash', 'SFMNP', 'SNAP', 'Organic',
                    'Bakedgoods', 'Cheese', 'Crafts', 'Flowers', 'Eggs', 'Seafood',
                    'Herbs', 'Vegetables', 'Honey', 'Jams', 'Maple', 'Meat', 'Nursery',
                    'Nuts', 'Plants', 'Poultry', 'Prepared', 'Soap', 'Trees', 'Wine',
                    'Coffee', 'Beans', 'Fruits', 'Grains', 'Juices', 'Mushrooms',
                    'PetFood', 'Tofu', 'WildHarvested', 'updateTime'
                ]
                writer = csv.DictWriter(file, fieldnames=fields)
                writer.writeheader()
            self.markets = []
        else:
            with open(self.markets_csv, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                self.markets = list(reader)

    def find_market_by_criteria(
        self,
        city: Optional[str] = None,
        state: Optional[str] = None,
        zip_code: Optional[str] = None,
        max_distance_miles: float = None,
        latitude: float = None,
        longitude: float = None
    ) -> List[Dict]:
        ''' 
        @requires: city, state, zip_code ϵ string OR None, max_distance_miles, latitude, longitude ϵ float OR None
        @modifies: None
        @effects: Filters markets based on location criteria
        @raises: None
        @returns: Filtered list of markets
        '''
        """
        Выполняет фильтрацию по критериям города, штата, индекса и расстояния.
        """
        result = []
        for market in self.markets:
            if (
                (not city or market['city'].lower().strip() == city.lower()) and
                (not state or market['State'].lower().strip() == state.lower()) and
                (not zip_code or market['zip'].strip() == zip_code.strip())
            ):
                if max_distance_miles is not None and latitude is not None and longitude is not None:
                    market_lat = float(market['y'])
                    market_lon = float(market['x'])
                    dist = haversine_distance(latitude, longitude, market_lat, market_lon)
                    if dist > max_distance_miles:
                        continue
                result.append(market)
        return result

    def sort_markets(self, markets: List[Dict], field: str, reverse=False) -> List[Dict]:
        ''' 
        @requires: markets ϵ [], field ϵ string, reverse ϵ boolean
        @modifies: None
        @effects: Sorts markets by a specific attribute
        @raises: None
        @returns: Sorted list of markets
        '''
        """
        Сортирует фермы по указанному полю (например, рейтингу, названию и т.д.)
        """
        sorted_markets = sorted(markets, key=lambda x: x[field], reverse=reverse)
        return sorted_markets

    def paginate_results(self, markets: List[Dict]) -> List[List[Dict]]:
        ''' 
        @requires: markets ϵ []
        @modifies: None
        @effects: Divides results into multiple pages
        @raises: None
        @returns: Paginated lists of markets
        '''
        """
        Формирует страницы вывода для удобной визуализации результатов.
        """
        pages = []
        num_pages = math.ceil(len(markets) / PAGE_SIZE)
        for i in range(num_pages):
            start = i * PAGE_SIZE
            end = start + PAGE_SIZE
            pages.append(markets[start:end])
        return pages
    
    def show_details(self, fmid: str, review_manager: ReviewManager, logged_in_user: Optional[str]):
        ''' 
        @requires: fmid ϵ string, review_manager ϵ ReviewManager instance, logged_in_user ϵ string OR None
        @modifies: None
        @effects: Displays detailed info about a market including reviews
        @raises: None
        @returns: Detailed market information or None
        '''
        """
        Показывает подробную информацию о рынке по его FMID и даёт возможность удалить отзыв.
        """
        for market in self.markets:
           if market['FMID'] == fmid:
            details = f"""
            Подробная информация о рынке FMID: {market['FMID']}
            Название: {market['MarketName']}
            Улица: {market['street']}
            Город: {market['city']}
            Округ: {market['County']}
            Штат: {market['State']}
            Индекс: {market['zip']}
            Широта: {market['y']}, Долгота: {market['x']}
            Веб-сайт: {market['Website']}
            Социальные сети: Facebook={market['Facebook']}, Twitter={market['Twitter']}, YouTube={market['Youtube']},Other Media={market['OtherMedia']}"
            Начало сезонов работы: {market['Season1Date']},({market['Season1Time']}), {market['Season2Date']} ({market['Season2Time']}), {market['Season3Date']} ({market['Season3Time']}), {market['Season4Date']} ({market['Season4Time']})"
            Типы принимаемых оплат: Кредитные карты={'Да' if market['Credit'] == 'Y' else 'Нет'}, WIC={'Да' if market['WIC'] == 'Y' else 'Нет'}, WIC Cash={'Да' if market['WICcash'] == 'Y' else 'Нет'}, SFMNP={'Да' if market['SFMNP'] == 'Y' else 'Нет'}, SNAP={'Да' if market['SNAP'] == 'Y' else 'Нет'}"  
            Органические продукты: {'Да' if market['Organic'] == 'Yes' else 'Нет'}"
            Продукты: выпечка={'Да' if market['Bakedgoods'] == 'Y' else 'Нет'}, сыры={'Да' if market['Cheese'] == 'Y' else 'Нет'}, ремесленные изделия={'Да' if market['Crafts'] == 'Y' else 'Нет'}, цветы={'Да' if market['Flowers'] == 'Yes' else 'Нет'}, яйца={'Да' if market['Eggs'] == 'Y' else 'Нет'}, морепродукты={'Да' if market['Seafood'] == 'Y' else 'Нет'}, травы={'Да' if market['Herbs'] == 'Y' else 'Нет'}, овощи={'Да' if market['Vegetables'] == 'Y' else 'Нет'}, мёд={'Да' if market['Honey'] == 'Y' else 'Нет'}, варенья={'Да' if market['Jams'] == 'Y' else 'Нет'}, кленовый сироп={'Да' if market['Maple'] == 'Y' else 'Нет'}, мясо={'Да' if market['Meat'] == 'Y' else 'Нет'}, питомники растений={'Да' if market['Nursery'] == 'Y' else 'Нет'}, орехи={'Да' if market['Nuts'] == 'Yes' else 'Нет'}, растения={'Да' if market['Plants'] == 'Y' else 'Нет'}, домашняя птица={'Да' if market['Poultry'] == 'Y' else 'Нет'}, приготовленные блюда={'Да' if market['Prepared'] == 'Y' else 'Нет'}, косметика={'Да' if market['Soap'] == 'Y' else 'Нет'}, деревья={'Да' if market['Trees'] == 'Y' else 'Нет'}, вина={'Да' if market['Wine'] == 'Y' else 'Нет'}, кофе={'Да' if market['Coffee'] == 'Y' else 'Нет'}, бобовые={'Да' if market['Beans'] == 'Y' else 'Нет'}, фрукты={'Да' if market['Fruits'] == 'Y' else 'Нет'}, зерновые={'Да' if market['Grains'] == 'Y' else 'Нет'}, свежевыжатый сок={'Да' if market['Juices'] == 'Y' else 'Нет'}, грибы={'Да' if market['Mushrooms'] == 'Y' else 'Нет'}, корм для домашних животных={'Да' if market['PetFood'] == 'Y' else 'Нет'}, тофу={'Да' if market['Tofu'] == 'Y' else 'Нет'}, дикорастущие продукты={'Да' if market['WildHarvested'] == 'Y' else 'Нет'}"
            Последнее обновление информации: {market['updateTime']}"
            """
            print(details)
            # Получаем все отзывы по этому рынку
            reviews = review_manager.get_reviews_by_fmid(fmid)
            
            # Отделяем отзывы текущего пользователя
            user_reviews = [review for review in reviews if review['author'] == logged_in_user]

            # Выводим общую информацию о рынке и все отзывы
            print("\nОтзывы от всех пользователей:")
            for rev in reviews:
                    # Взять имя и фамилию пользователя по логину
                    user_data = user_mgr.users.get(rev['author'], {})
                    full_name = f"{user_data.get('firstname')} {user_data.get('lastname')}"
                    print(f"Автор: {full_name} | Рейтинг: {rev['rating']} | Коммент.: {rev['comment']}")
            # Если пользователь залогинен, определяем дальнейшие шаги
            if logged_in_user:
                    # Если у пользователя уже есть отзыв на этот рынок
                    if user_reviews:
                        print("\nУ вас уже есть отзыв на этот рынок:")
                        for idx, review in enumerate(user_reviews):
                            print(f"{idx+1}. Рейтинг: {review['rating']}, Комментарий: {review['comment']}")

                        # Предлагаем пользователю удалить или изменить отзыв
                        choice = input("Выберите номер отзыва для обновления или удаления (или введите 'q' для отмены): ")
                        if choice.lower() == 'q':
                            pass
                        else:
                            try:
                                index = int(choice) - 1
                                selected_review = user_reviews[index]
                                
                                update_choice = input("Хотите обновить (U) или удалить (D) отзыв? ")
                                if update_choice.upper() == 'U':
                                    new_rating = input("Новая оценка (от 1 до 5 звезд): ")
                                    new_comment = input("Новый комментарий (можете оставить пустым): ")
                                    
                                    updated_review = {
                                        'fmid': fmid,
                                        'rating': new_rating,
                                        'comment': new_comment,
                                        'author': logged_in_user
                                    }
                                    # Удаляем старый отзыв и добавляем новый
                                    review_manager.delete_review(selected_review['fmid'], logged_in_user)
                                    review_manager.add_review(updated_review['fmid'], int(updated_review['rating']), updated_review['comment'], logged_in_user)
                                    print("Отзыв успешно обновлён.")
                                elif update_choice.upper() == 'D':
                                    deleted = review_manager.delete_review(selected_review['fmid'], logged_in_user)
                                    if deleted:
                                        print("Отзыв успешно удалён.")
                                    else:
                                        print("Ошибка при удалении отзыва.")
                                else:
                                    print("Неверный выбор.")
                            except (IndexError, ValueError):
                                print("Недопустимый выбор.")
                    else:
                        # Если отзыва нет, запрашиваем создание нового
                        rating = input("Пожалуйста, поставьте свою оценку этому рынку (от 1 до 5 звезд): ")
                        if rating.isdigit() and 1 <= int(rating) <= 5:
                            comment = input("Напишите ваш отзыв (если хотите пропустить, нажмите Enter): ")
                            review_manager.add_review(fmid, int(rating), comment, logged_in_user)
                            print("Отзыв успешно добавлен.")
                        else:
                            print("Введено неправильное значение оценки.")

            return details 
        return None

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


def view_all_markets(manager: MarketManager, review_manager: ReviewManager, logged_in_user: Optional[str]):
    ''' 
    @requires: manager ϵ MarketManager instance, review_manager ϵ ReviewManager instance, logged_in_user ϵ string OR None
    @modifies: None
    @effects: Outputs all markets with pagination support
    @raises: None
    @returns: None
    '''
    """
    Функция просмотра всех рынков с пагинацией и отображением отзывов.
    """
    all_markets = manager.markets
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
            # Определяем строку с отзывами или уведомление об их отсутствии
            reviews_str = ""
            if reviews:
                for rev in reviews:
                    # Взять имя и фамилию пользователя по логину
                    user_data = user_mgr.users.get(rev['author'], {})
                    full_name = f"{user_data.get('firstname')} {user_data.get('lastname')}"
                    
                    reviews_str += f"    Автор: {full_name} | Рейтинг: {rev['rating']} | Коммент.: {rev['comment']}\n"
            else:
                reviews_str = "    Нет отзывов.\n"
            
            print(f"- Название: {market['MarketName']}\n"
                  f"  FMID: {market['FMID']}\n"
                  f"  Город: {market['city']}\n"
                  f"  Штат: {market['State']}\n"
                  f"  Индекс: {market['zip']}\n"
                  f"  Отзывы:\n{reviews_str}\n")
        
        cmd = input("Следующая страница ('n'), предыдущая ('p'), подробнее ('d'), назад ('b'): ").lower()
        if cmd == 'n':
            current_page += 1
        elif cmd == 'p':
            current_page -= 1
        elif cmd == 'd':
            detail_choice = input("Введите FMID рынка для подробностей: ")
            details = manager.show_details(detail_choice,review_manager, logged_in_user)
            if details:
                print("\nПодробная информация о рынке:")
                print(details)
                cmd = input("для возврата введите любой символ: ").lower()
            else:
                print("Рынок не найден.")
        elif cmd == 'b':
            break
        else:
            print("Неправильная команда.")

def search_markets(manager: MarketManager, review_manager: ReviewManager, logged_in_user: Optional[str]):
    ''' 
    @requires: manager ϵ MarketManager instance, review_manager ϵ ReviewManager instance, logged_in_user ϵ string OR None
    @modifies: None
    @effects: Search markets by different filters
    @raises: None
    @returns: None
    '''
    """
    Функция поиска рынков по заданным критериям.
    """
    city = input("Город (оставьте пустым, если не важен): ") or None
    state = input("Штат (оставьте пустым, если не важен): ") or None
    zip_code = input("Индекс (оставьте пустым, если не важен): ") or None
    lat = input("Широта для расчёта расстояния (оставьте пустым, если не важно): ") or None
    lon = input("Долгота для расчёта расстояния (оставьте пустым, если не важно): ") or None
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
                #Определяем строку с отзывами или уведомление об их отсутствии
                reviews_str = ""
                if reviews:
                  for rev in reviews:
                    # Взять имя и фамилию пользователя по логину
                    user_data = user_mgr.users.get(rev['author'], {})
                    full_name = f"{user_data.get('firstname')} {user_data.get('lastname')}"
                    
                    reviews_str += f"    Автор: {full_name} | Рейтинг: {rev['rating']} | Коммент.: {rev['comment']}\n"
                else:
                     reviews_str = "    Нет отзывов.\n"

                print(f"- Название: {market['MarketName']}\n"
                      f"  FMID: {market['FMID']}\n"
                      f"  Город: {market['city']}\n"
                      f"  Штат: {market['State']}\n"
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
                   cmd = input("для возврата введите любой символ: ").lower()
                else:
                    print("Рынок не найден.")
            elif cmd == 'b':
                break
            else:
                print("Неправильная команда.")
    else:
        print("Нет соответствующих рынков.")


def add_review(review_manager: ReviewManager, logged_in_user: str):
    ''' 
    @requires: review_manager ϵ ReviewManager instance, logged_in_user ϵ string
    @modifies: None
    @effects: Add a new review for a specific market
    @raises: None
    @returns: None
    '''
    """
    Добавляем новый отзыв пользователю.
    """
    fmid = input("Введите FMID рынка: ")
    rating = int(input("Оцените рынок (1-5 звёзд): "))
    comment = input("Комментарий (можно оставить пустым): ")
    review_manager.add_review(fmid, rating, comment, logged_in_user)
    print("Отзыв успешно добавлен.")


def run_application(logged_in_user):
    ''' 
    @requires: logged_in_user ϵ string OR None
    @modifies: None
    @effects: Runs the main loop of the application
    @raises: None
    @returns: None
    '''
    """
    Основной цикл работы приложения.
    """
    review_mgr = ReviewManager(REVIEWS_CSV)
    market_mgr = MarketManager(MARKETS_CSV)
    user_mgr = UserManager(USERS_CSV)
    '''logged_in_user = None'''
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


def login_or_register(user_mgr: UserManager):
    ''' 
    @requires: user_mgr ϵ UserManager instance
    @modifies: logged_in_user variable
    @effects: Logs in or registers a new user
    @raises: None
    @returns: Username of logged-in user
    '''
    """
    Вход или регистрация пользователя.
    """
    global logged_in_user
    while True:
        choice = input("Хотите войти (L) или зарегистрироваться (R)? (Q для выхода): ").upper()
        if choice == 'L':
            username = input("Логин пользователя: ")
            password = input("Пароль: ")
            if user_mgr.verify_login(username, password):
                logged_in_user = username
                # Получаем полное представление пользователя
                user_data = user_mgr.users[logged_in_user]
                full_name = f"{user_data['firstname']} {user_data['lastname']}"
                print(f"Привет, {full_name}!")
                break
            else:
                print("Неверные данные. Попробуйте снова.")
        elif choice == 'R':
            username = input("Создать новый логин пользователя: ")
            password = input("Создать новый пароль: ")
            firstname = input("Введите имя пользователя: ")
            lastname = input("Введите фамилию пользователя: ")
            try:
                user_mgr.create_user(username, password, firstname, lastname)
                logged_in_user = username
                print(f"Поздравляю, {firstname} {lastname}! Вы зарегистрированы.")
                break
            except ValueError as e:
                print(e)
        elif choice == 'Q':
            sys.exit()
        else:
            print("Некорректная команда.")
    return logged_in_user
 
if __name__ == "__main__":
    user_mgr = UserManager(USERS_CSV)
    logged_in_user = login_or_register(user_mgr)
    run_application(logged_in_user)