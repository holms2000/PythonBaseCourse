import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.messagebox import showerror, showwarning, showinfo
import psycopg2
from contextlib import closing
import math
from datetime import datetime
from hashlib import sha256
from typing import List, Dict, Optional
from functools import partial
import os
from dotenv import load_dotenv

load_dotenv()

# Настройки подключения к базе данных
'''
вариант с .env
db_config = {
    'dbname': os.getenv("DBNAME"),
    'user': os.getenv("LOGIN"),
    'password':os.getenv("PASSWORD"),
    'host': os.getenv("HOST"),
    'port': os.getenv("PORT")
}
'''
db_config = {
    'dbname': 'farmers_db',
    'user': 'sasha',
    'password': '1973',
    'host': 'localhost',
    'port': '5433'
}

# Радиус Земли в милях
EARTH_RADIUS_MILES = 3958.8

class Tooltip:
    def __init__(self, widget, text, delay=500):
        '''
        Initializes a tooltip for a widget.
        @requires: widget ϵ Widget, text ϵ string
        @modifies: None
        @effects: Creates a tooltip object bound to the widget.
        @raises: None
        @returns: None
        '''
        self.widget, self.text, self.delay = widget, text, delay
        self._after_id = None
        self._tip = None
        widget.bind("<Enter>", self._schedule)
        widget.bind("<Leave>", self._hide)
        widget.bind("<ButtonPress>", self._hide)
        widget.bind("<Motion>", self._move)

    def _schedule(self, _=None):
        '''
        Schedules the appearance of the tooltip after a delay.
        @requires: None
        @modifies: Internal timer states
        @effects: Triggers tooltip display after a timeout.
        @raises: None
        @returns: None
        '''
        self._cancel()
        self._after_id = self.widget.after(self.delay, self._show)

    def _show(self):
        '''
        Displays the tooltip near the widget.
        @requires: Tooltip initialized
        @modifies: None
        @effects: Shows the tooltip next to the widget.
        @raises: None
        @returns: None
        '''
        if self._tip:
            return
        self._tip = tk.Toplevel(self.widget)
        self._tip.wm_overrideredirect(True)
        self._tip.wm_attributes("-topmost", True)
        tk.Label(self._tip, text=self.text, bg="#ffffe0",
                 relief="solid", bd=1, justify="left").pack(ipadx=4, ipady=2)
        self._move()

    def _move(self, event=None):
        '''
        Moves the tooltip to follow the pointer motion.
        @requires: Event ϵ MouseEvent (optional)
        @modifies: Position of the tooltip
        @effects: Repositions the tooltip dynamically.
        @raises: None
        @returns: None
        '''
        if not self._tip:
            return
        x = (event.x_root + 12) if event else self.widget.winfo_rootx() + 12
        y = (event.y_root + 8) if event else self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        self._tip.geometry(f"+{x}+{y}")

    def _hide(self, _=None):
        '''
        Hides the tooltip immediately.
        @requires: Tooltip shown
        @modifies: Visibility of the tooltip
        @effects: Closes the tooltip instantly.
        @raises: None
        @returns: None
        '''
        self._cancel()
        if self._tip:
            self._tip.destroy()
            self._tip = None

    def _cancel(self):
        '''
        Cancels pending actions regarding tooltip visibility.
        @requires: Pending actions exist
        @modifies: Cancelled internal timers
        @effects: Stops future tooltip display/hide actions.
        @raises: None
        @returns: None
        '''
        if self._after_id:
            self.widget.after_cancel(self._after_id)
            self._after_id = None

# Example:
# btn = ttk.Button(root, text="Hover me")
# Tooltip(btn, "Click to submit", delay=700)

# Класс для работы с базой данных
class DatabaseConnection:
    def __init__(self, db_config):
        '''
        Constructs a database connection handler.
        @requires: db_config ϵ dict
        @modifies: None
        @effects: Stores the database configuration internally.
        @raises: None
        @returns: None
        '''
        self.db_config = db_config

    def execute_query(self, query, params=None):
        '''
        Executes a SQL query and returns the results.
        @requires: query ϵ string, params ϵ tuple|list (optional)
        @modifies: None
        @effects: Runs the SQL query.
        @raises: Possible exceptions from psycopg2 library
        @returns: Results of the executed query.
        '''
        with closing(psycopg2.connect(**self.db_config)) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()

    def insert_data(self, table, data):
        '''
        Inserts data into a specified table.
        @requires: table ϵ string, data ϵ dict
        @modifies: Data inserted into the database
        @effects: Adds a new record to the database.
        @raises: Exceptions related to database insertion errors
        @returns: None
        '''
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        values = tuple(data.values())
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders});"
        with closing(psycopg2.connect(**self.db_config)) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, values)
                conn.commit()

    def update_data(self, table, set_values, condition):
        '''
        Updates existing records in a table.
        @requires: table ϵ string, set_values ϵ dict, condition ϵ dict
        @modifies: Records are modified in the database
        @effects: Changes the attributes of matched records.
        @raises: Errors during database updates
        @returns: None
        '''
        set_clause = ", ".join([f"{key}=%s" for key in set_values.keys()])
        where_clause = " AND ".join([f"{k}=%s" for k in condition.keys()])
        values = list(set_values.values()) + list(condition.values())
        query = f"UPDATE {table} SET {set_clause} WHERE {where_clause};"
        with closing(psycopg2.connect(**self.db_config)) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, values)
                conn.commit()

    def delete_data(self, table, condition):
        '''
        Deletes records from a table based on a condition.
        @requires: table ϵ string, condition ϵ dict
        @modifies: Records removed from the database
        @effects: Removes records satisfying the condition.
        @raises: Potential database deletion errors
        @returns: None
        '''
        where_clause = " AND ".join([f"{k}=%s" for k in condition.keys()])
        values = tuple(condition.values())
        query = f"DELETE FROM {table} WHERE {where_clause};"
        with closing(psycopg2.connect(**self.db_config)) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, values)
                conn.commit()

# Класс для работы с пользователями
class UserManager:
    def __init__(self, db_connector):
        '''
        Initializes a user management object.
        @requires: db_connector ϵ DatabaseConnection
        @modifies: None
        @effects: Prepares the user manager for operation.
        @raises: None
        @returns: None
        '''
        self.db_connector = db_connector

    def check_user_exists(self, username):
        '''
        Checks if a user exists in the database.
        @requires: username ϵ string
        @modifies: None
        @effects: Queries the database for the user.
        @raises: None
        @returns: Boolean indicating existence of the user.
        '''
        query = "SELECT COUNT(*) FROM users WHERE username=%s;"
        result = self.db_connector.execute_query(query, (username,))
        return result[0][0] > 0

    def create_user(self, username, password, firstname, lastname):
        '''
        Registers a new user account.
        @requires: username ϵ string, password ϵ string, firstname ϵ string, lastname ϵ string
        @modifies: Users added to the database
        @effects: Inserts a new user into the database.
        @raises: Exception if username already exists
        @returns: None
        '''
        hashed_password = sha256(password.encode()).hexdigest()
        data = {
            'username': username,
            'password_hash': hashed_password,
            'firstname': firstname,
            'lastname': lastname
        }
        self.db_connector.insert_data('users', data)

    def verify_login(self, username, password):
       '''
        Verifies a user's login attempt.
        @requires: username ϵ string, password ϵ string
        @modifies: None
        @effects: Compares hashed passwords.
        @raises: None
        @returns: Authentication success/failure.
        '''
       query = "SELECT password_hash, firstname, lastname FROM users WHERE username=%s;"
       result = self.db_connector.execute_query(query, (username,))
       if not result:
         return False
       stored_hash, first_name, last_name = result[0]
       provided_hash = sha256(password.encode()).hexdigest()
       return (stored_hash == provided_hash, first_name, last_name)

# Класс для работы с отзывами
class ReviewManager:
    def __init__(self, db_connector):
        '''
        Initializes a review manager.
        @requires: db_connector ϵ DatabaseConnection
        @modifies: None
        @effects: Configures the review manager.
        @raises: None
        @returns: None
        '''
        self.db_connector = db_connector

    def add_review(self, fmid, rating, comment, author):
        '''
        Adds a new review for a market.
        @requires: fmid ϵ integer, rating ϵ integer, comment ϵ string, author ϵ string
        @modifies: Reviews added to the database
        @effects: Increases number of reviews for the market.
        @raises: None
        @returns: None
        '''
        data = {
            'fmid': fmid,
            'rating': rating,
            'comment': comment,
            'author': author
        }
        self.db_connector.insert_data('reviews', data)

    def get_reviews_by_fmid(self, fmid):
        '''
        Fetches reviews for a specific market.
        @requires: fmid ϵ integer
        @modifies: None
        @effects: Retrieving reviews from the database.
        @raises: None
        @returns: List of reviews for the market.
        '''
        # Сначала получаем отзывы, включая авторство
        query = "SELECT * FROM reviews WHERE fmid=%s;"
        results = self.db_connector.execute_query(query, (fmid,))
        reviews_with_authors = [dict(zip(('id', 'fmid', 'rating', 'comment', 'author'), row)) for row in results]

        # Проверяем наличие авторов
        if not reviews_with_authors:
            return []  # Возвращаем пустой список, если нет отзывов

        # Далее собираем имена и фамилии пользователей по каждому авторскому логину
        authors = {review['author'] for review in reviews_with_authors}
        names_query = "SELECT username, firstname, lastname FROM users WHERE username IN (%s);"
        placeholder = ','.join(['%s'] * len(authors))
        names_results = self.db_connector.execute_query(names_query % placeholder, tuple(authors))
        users_names_map = {row[0]: f'{row[1]} {row[2]}' for row in names_results}

        # Формируем окончательные отзывы с именами и фамилиями
        final_reviews = []
        for review in reviews_with_authors:
            full_name = users_names_map.get(review['author'], '')
            final_reviews.append({
                'id': review['id'],
                'fmid': review['fmid'],
                'rating': review['rating'],
                'comment': review['comment'],
                'fullname': full_name
            })
        return final_reviews

    def edit_review(self, fmid, new_rating, new_comment, author):
        '''
        Modifies an existing review.
        @requires: fmid ϵ integer, new_rating ϵ integer, new_comment ϵ string, author ϵ string
        @modifies: Existing review in the database
        @effects: Updates the review details.
        @raises: None
        @returns: None
        '''
        query = "UPDATE reviews SET rating=%s, comment=%s WHERE fmid=%s AND author=%s;"
        with closing(psycopg2.connect(**self.db_connector.db_config)) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (new_rating, new_comment, fmid, author))
                conn.commit()

    def remove_review(self, fmid, author):
        '''
        Deletes a review created by a specific user.
        @requires: fmid ϵ integer, author ϵ string
        @modifies: Removal of review from the database
        @effects: Decreases total reviews count.
        @raises: None
        @returns: None
        '''
        query = "DELETE FROM reviews WHERE fmid=%s AND author=%s;"
        with closing(psycopg2.connect(**self.db_connector.db_config)) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (fmid, author))
                conn.commit()
    
    def user_has_reviewed(self, fmid, author):
        '''
        Checks if a user has previously submitted a review for a market.
        @requires: fmid ϵ integer, author ϵ string
        @modifies: None
        @effects: Queries the database for past reviews.
        @raises: None
        @returns: Boolean indicating prior submission.
        '''
        """Проверяет, оставил ли пользователь отзыв по этому рынку."""
        query = "SELECT COUNT(*) FROM reviews WHERE fmid=%s AND author=%s;"
        result = self.db_connector.execute_query(query, (fmid, author))
        return result[0][0] > 0
    
# Класс для работы с рынками
class MarketManager:
    def __init__(self, db_connector):
        '''
        Initializes a market manager.
        @requires: db_connector ϵ DatabaseConnection
        @modifies: None
        @effects: Establishes connection between manager and DB.
        @raises: None
        @returns: None
        '''
        self.db_connector = db_connector

    def calculate_average_rating(self, fmid):
        '''
        Computes the average rating for a market.
        @requires: fmid ϵ integer
        @modifies: None
        @effects: Queries ratings from the database.
        @raises: None
        @returns: Float representing average rating.
        '''
        # Запрос для получения среднего рейтинга конкретного рынка
        query = "SELECT COALESCE(AVG(rating), 0) AS avg_rating FROM reviews WHERE fmid=%s;"
        result = self.db_connector.execute_query(query, (fmid,))
        return result[0][0] if result else 0

    def find_market_by_criteria(self, **kwargs):
        '''
        Searches for markets based on filters.
        @requires: Keyword arguments for filtering
        @modifies: None
        @effects: Selects relevant markets from the database.
        @raises: None
        @returns: List of filtered markets.
        '''
        # Основной запрос на получение списков рынков по критериям
        markets = self.base_find_market_by_criteria(**kwargs)

        # Вычисление среднего рейтинга для каждого рынка
        '''
        for market in markets:
            average_rating = self.calculate_average_rating(market['FMID'])
            market['average_rating'] = average_rating
        '''
        return markets

    def base_find_market_by_criteria(self, **kwargs):
        '''
        Searches for markets based on various filter criteria.

        This method constructs a dynamic SQL query depending on the keyword arguments passed.
        It joins tables to retrieve comprehensive market details along with address and coordinate information.

        @requires: At least one filter criterion must be provided (such as city, state, etc.)
        @modifies: None
        @effects: Generates and executes a complex SQL query to fetch matching markets.
        @raises: If any issue occurs while executing the query, an exception will be thrown.
        @returns: A list of dictionaries, each representing a market's details, including its address and coordinates.
        '''
        # Базовый метод поиска, аналогичный вашему оригинальному запросу
        conditions = []
        args = []
        if kwargs.get('city'):
            conditions.append("addresses.city=%s")
            args.append(kwargs['city'])
        if kwargs.get('state'):
            conditions.append("addresses.state=%s")
            args.append(kwargs['state'])
        if kwargs.get('zip_code'):
            conditions.append("addresses.zip=%s")
            args.append(kwargs['zip_code'])
        if kwargs.get('max_distance') and kwargs.get('latitude') and kwargs.get('longitude'):
            distance_condition = f"""ACOS(SIN(RADIANS({kwargs['latitude']}))*SIN(RADIANS(coordinates.latitude)) +
                                     COS(RADIANS({kwargs['latitude']}))*COS(RADIANS(coordinates.latitude)) *
                                     COS(RADIANS(coordinates.longitude-{kwargs['longitude']})))*{EARTH_RADIUS_MILES} <= %s"""
            conditions.append(distance_condition)
            args.append(kwargs['max_distance'])
        if kwargs.get('market_name_part'):
            conditions.append("LOWER(markets.MarketName) LIKE LOWER(%s)")
            args.append('%' + kwargs['market_name_part'].lower() + '%')
        if kwargs.get('fmid'):
            conditions.append("markets.FMID=%s")
            args.append(kwargs['fmid'])

        base_query = """SELECT markets.*, addresses.street, addresses.city, addresses.county, addresses.state, addresses.zip,
                             coordinates.latitude, coordinates.longitude"""
        query = f"{base_query}\nFROM markets\nJOIN addresses ON markets.address_id=addresses.id\nJOIN coordinates ON markets.coordinate_id=coordinates.id"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        results = self.db_connector.execute_query(query, args)
        return [dict(zip(('id', 'FMID', 'MarketName', 'website', 'address_id', 'coordinate_id', 'update_time', 'street', 'city', 'county', 'state', 'zip', 'latitude', 'longitude'), row)) for row in results]
    
    def sort_markets(self, markets, field, order="desc"):
       '''
        Sorts a list of markets by a specified attribute.
        @requires: markets ϵ List[Dict], field ϵ string
        @modifies: None
        @effects: Sorts the input list of markets.
        @raises: None
        @returns: Sorted list of market dictionaries.
       '''
       if field == 'rating':
            # Замещение None на 0 для правильного сравнения
            sorted_markets = sorted(markets, key=lambda x: x['average_rating'] or 0, reverse=(order != "asc"))
       else:
            sorted_markets = sorted(markets, key=lambda x: x[field], reverse=(order != "asc"))
       return sorted_markets
        
    def paginate_results(self, markets):
        '''
        Divides a large dataset into smaller chunks (pages).
        @requires: markets ϵ List[Dict]
        @modifies: None
        @effects: Groups markets into pages.
        @raises: None
        @returns: Paginated results split across multiple lists.
        '''
        PAGE_SIZE = 10
        pages = []
        num_pages = math.ceil(len(markets) / PAGE_SIZE)
        for i in range(num_pages):
            start = i * PAGE_SIZE
            end = start + PAGE_SIZE
            pages.append(markets[start:end])
        return pages
    
    def show_details(self, fmid_or_name, review_manager, logged_in_user):
        '''
        Retrieves detailed information about a market, including reviews.
        @requires: fmid_or_name ϵ string, review_manager ϵ ReviewManager, logged_in_user ϵ string
        @modifies: None
        @effects: Pulls market details and reviews from the database.
        @raises: None
        @returns: Detailed description of the market.
        '''
        try:
            fmid = int(fmid_or_name)
            markets = self.find_market_by_criteria(fmid=fmid)
        except ValueError:
            markets = self.find_market_by_criteria(market_name_part=fmid_or_name)
        if not markets:
            return "Рынок не найден."
        market = markets[0]

        # Дополнительные запросы для связанной информации
        # Социальные сети
        social_link_query = "SELECT * FROM social_links WHERE market_id=%s;"
        social_link_result = self.db_connector.execute_query(social_link_query, (market["id"],))
        social_links = {}
        if social_link_result:
            sl = social_link_result[0]
            social_links = {"Facebook": sl[2],
                            "Twitter": sl[3],
                            "YouTube": sl[4],
                            "Other Media": sl[4]}

        # Способы оплаты
        payment_option_query = "SELECT * FROM payment_options WHERE market_id=%s;"
        payment_option_result = self.db_connector.execute_query(payment_option_query, (market["id"],))
        payment_options = {}
        if payment_option_result:
            po = payment_option_result[0]
            payment_options = {"Кредитные карты": po[2],
                               "Программа WIC": po[3],
                               "Денежные средства по программе WIC": po[4],
                               "Программа SFMNP": po[5],
                               "Программа SNAP": po[6]}

        # Продукты
        product_query = "SELECT * FROM products WHERE market_id=%s;"
        product_result = self.db_connector.execute_query(product_query, (market["id"],))
        products = []
        product_columns = ['organic', 'baked_goods', 'cheese', 'crafts', 'flowers', 'eggs', 'seafood', 'herbs', 'vegetables', 'honey', 'jams', 'maple', 'meat', 'nursery', 'nuts', 'plants', 'poultry', 'prepared', 'soap', 'trees', 'wine', 'coffee', 'beans', 'fruits', 'grains', 'juices', 'mushrooms', 'pet_food', 'tofu', 'wild_harvested']
        
        for col, val in zip(product_columns, product_result[0]):
           if val:
             products.append(col.replace("_", " ").capitalize())
        
        '''
        if product_result:
            pr = product_result[0]
            for column, value in pr.items():
                if value:
                    products.append(column.replace("_", " ").capitalize())
        '''
        # График работы
        schedule_query = "SELECT * FROM operating_schedule WHERE market_id=%s ORDER BY season_number ASC;"
        schedule_result = self.db_connector.execute_query(schedule_query, (market["id"],))
        schedules = []
        if schedule_result:
            for row in schedule_result:
                schedules.append({"Season Number": row[2],
                                  "Season Date": row[3],
                                  "Season Time": row[4]})

        # Основная информация о рынке
        details = f"""
        Подробная информация о рынке FMID: {market['FMID']} 
        Название: {market['MarketName']}
        Адрес: {market['street']}, {market['city']}, {market['state']}, {market['zip']}
        Координаты: широта={market['latitude']}, долгота={market['longitude']}
        Сайт: {market['website']}
        Обновлено: {market['update_time']}

        --- СОЦИАЛЬНЫЕ СЕТИ ---
        """
        for platform, link in social_links.items():
            details += f"{platform}: {link}\n"

        details += "\n--- СПОСОБЫ ОПЛАТЫ ---\n"
        for option, available in payment_options.items():
            details += f"{option}: {'Да' if available else 'Нет'}\n"

        details += "\n--- ПРОДУКТЫ НА РЫНКЕ ---\n"
        for prod in products:
            details += f"{prod} "

        details += "\n--- ГРАФИК РАБОТЫ ---\n"
        for sched in schedules:
            details += f"Сезон {sched['Season Number']}: {sched['Season Date']}, Время работы: {sched['Season Time']}\n"

        # Отзывы
        reviews = review_manager.get_reviews_by_fmid(market['FMID'])
        if reviews:
            details += "\n--- ОТЗЫВЫ ---\n"
            for rev in reviews:
                details += f"Автор: {rev['fullname']}, Рейтинг: {rev['rating']}, Комментарий: {rev['comment']}\n"
        else:
            details += "\nОтзывов нет.\n"
        return details

# Главный класс приложения с Tkinter
class FarmersMarketsApp(tk.Tk):
    def __init__(self, db_connector):
        '''
        Initializes the main application window.
        @requires: db_connector ϵ DatabaseConnection
        @modifies: Main window structure
        @effects: Builds the GUI and prepares it for use.
        @raises: None
        @returns: None
        '''
        super().__init__()
        self.title("Приложение фермерских рынков")
        self.geometry("800x650")
        self.db_connector = db_connector
        self.user_mgr = UserManager(db_connector)
        self.review_mgr = ReviewManager(db_connector)
        self.market_mgr = MarketManager(db_connector)
        self.logged_in_user = None
        self.details_window = None  # Переменная для отслеживания открытого окна деталей
        self.login_window()

    def login_window(self):
        '''
        Renders the login window.
        @requires: Application initialization completed
        @modifies: Root window content
        @effects: Presents the login form.
        @raises: None
        @returns: None
        '''
        login_frame = tk.Frame(self)
        login_frame.pack(fill="both", expand=True)

        label_username = ttk.Label(login_frame, text="Имя пользователя:", font=("Arial", 14))
        label_username.pack(padx=10, pady=10)
        entry_username = ttk.Entry(login_frame, width=30)
        entry_username.pack(padx=10, pady=5)
        entry_username.focus_set()  # Устанавливаем фокус на поле логина

        # Переключение на поле пароля при нажатии Enter
        entry_username.bind("<Return>", lambda event: entry_password.focus_set())

        label_password = ttk.Label(login_frame, text="Пароль:", font=("Arial", 14))
        label_password.pack(padx=10, pady=10)
        entry_password = ttk.Entry(login_frame, show="*", width=30)
        entry_password.pack(padx=10, pady=5)

        # Авторизация при нажатии Enter в поле пароля
        entry_password.bind("<Return>", lambda event: self.authenticate(entry_username.get(), entry_password.get()))

        button_login = ttk.Button(login_frame, text="Войти", command=lambda: self.authenticate(entry_username.get(), entry_password.get()))
        button_login.pack(padx=10, pady=10)

        # Кнопка регистрации доступна, если пользователь не залогинился
        if not self.logged_in_user:
            button_register = ttk.Button(login_frame, text="Зарегистрироваться", command=self.register_window)
            button_register.pack(padx=10, pady=10)
            Tooltip(button_register, "Нажмите для регистрации в программе", delay=700)

    def authenticate(self, username, password):
       '''
        Validates user credentials at login.
        @requires: username ϵ string, password ϵ string
        @modifies: Current session status
        @effects: Logs in or shows error messages.
        @raises: None
        @returns: Authentication outcome.
       '''
       auth_result = self.user_mgr.verify_login(username, password)
       if isinstance(auth_result, bool):
         if auth_result:
            self.logged_in_user = username
            self.clear_login_screen()
         else:
            messagebox.showerror("Ошибка", "Неверные данные для входа.")
       elif isinstance(auth_result, tuple):
         verified, first_name, last_name = auth_result
         if verified:
            self.logged_in_user = username
            self.logged_in_fullname = f"{first_name} {last_name}"  # Сохраняем полное имя
            self.clear_login_screen()
         else:
            messagebox.showerror("Ошибка", "Неверные данные для входа.")

    def clear_login_screen(self):
        '''
        Cleans up the login screen after successful login.
        @requires: Successful login
        @modifies: Window contents
        @effects: Switches to the main application view.
        @raises: None
        @returns: None
        '''
        # Очищаем старое содержимое окна
        for widget in self.winfo_children():
            widget.destroy()

        # Создаем главную часть приложения
        self.main_app()

    def register_window(self):
        '''
        Displays the registration form.
        @requires: No active user session
        @modifies: Root window content
        @effects: Enables user sign-up functionality.
        @raises: None
        @returns: None
        '''
        # Форма регистрации нового пользователя
        register_frame = tk.Frame(self)
        register_frame.pack(fill="both", expand=True)

        label_firstname = ttk.Label(register_frame, text="Имя:", font=("Arial", 14))
        label_firstname.pack(padx=10, pady=10)
        entry_firstname = ttk.Entry(register_frame, width=30)
        entry_firstname.pack(padx=10, pady=5)

        label_lastname = ttk.Label(register_frame, text="Фамилия:", font=("Arial", 14))
        label_lastname.pack(padx=10, pady=10)
        entry_lastname = ttk.Entry(register_frame, width=30)
        entry_lastname.pack(padx=10, pady=5)

        label_username = ttk.Label(register_frame, text="Имя пользователя:", font=("Arial", 14))
        label_username.pack(padx=10, pady=10)
        entry_username = ttk.Entry(register_frame, width=30)
        entry_username.pack(padx=10, pady=5)

        label_password = ttk.Label(register_frame, text="Пароль:", font=("Arial", 14))
        label_password.pack(padx=10, pady=10)
        entry_password = ttk.Entry(register_frame, show="*", width=30)
        entry_password.pack(padx=10, pady=5)

        button_register = ttk.Button(register_frame, text="Зарегистрироваться", command=lambda: self.register_user(entry_firstname.get(), entry_lastname.get(), entry_username.get(), entry_password.get()))
        button_register.pack(padx=10, pady=10)

    def register_user(self, firstname, lastname, username, password):
        '''
        Registers a new user account.
        @requires: Valid inputs
        @modifies: User database
        @effects: Adds a new user to the system.
        @raises: Error if username already exists
        @returns: Registration status.
        '''
        if self.user_mgr.check_user_exists(username):
            messagebox.showerror("Ошибка", "Такой пользователь уже существует.")
        else:
            self.user_mgr.create_user(username, password, firstname, lastname)
            messagebox.showinfo("Успех", "Вы успешно зарегистрированы.")
            #self.login_window()

    def open_details_window(self, fmid):
        '''
        Opens a modal window displaying detailed information about a farmer's market.

        This method creates a pop-up window showing extended details about a specific market, including reviews.
        It also allows editing or deleting previous reviews made by the current user or creating a new review if none exists yet.

        @requires: fmid must be a valid unique identifier for a market.
        @modifies: Updates the graphical user interface by opening a new window.
        @effects: Displays detailed information about the market and provides options for managing reviews.
        @raises: No direct exceptions are raised here, but possible issues could arise indirectly through dependent methods like show_details or grab_set.
        @returns: None
        '''
        # Если окно уже открыто, поднимаем его поверх остальных окон
        if self.details_window is not None and self.details_window.winfo_exists():
          self.details_window.lift()
          return

        # Создаем новое окно
        self.details_window = tk.Toplevel(self)
        self.details_window.title("Подробности о рынке")
        self.details_window.geometry("800x600")
        
        # Убедимся, что окно полностью прорисовано перед захватом фокуса
        self.details_window.update_idletasks()  # <<< Здесь обрабатываются все обновления GUI

        # Блокируем взаимодействие с главным окном до закрытия модального окна
        self.details_window.transient(self)   # Делаем дочерним окном основного окна
        self.details_window.grab_set()        # Захватываем фокус на данное окно

        # Получаем детали выбранного рынка
        details = self.market_mgr.show_details(str(fmid), self.review_mgr, self.logged_in_user)

        # Выводим информацию о рынке в Text виджет
        text_area = tk.Text(self.details_window,height=5, wrap=tk.WORD)
        text_area.insert(tk.END, details)
        #text_area.pack(fill="both", expand=True)
        
        text_area.pack(fill="both", expand=True)
        scrollbar_y = ttk.Scrollbar(text_area, orient="vertical", command=text_area.yview)
        scrollbar_y.pack(side="right", fill="y")
        text_area.configure(yscrollcommand=scrollbar_y.set)

        # Проверяем, оставил ли пользователь отзыв по этому рынку
        has_existing_review = self.review_mgr.user_has_reviewed(fmid, self.logged_in_user)

        # Фрейм для формы отзыва
        frame_review = tk.Frame(self.details_window)
        frame_review.pack(fill="x", padx=10, pady=10)

        # Определим, какую форму показать
        if has_existing_review:
          # Пользователь уже оставил отзыв, позволим изменить или удалить
          existing_review = self.review_mgr.get_reviews_by_fmid(fmid)[0]

          # Поля для редактирования отзыва
          label_edit_review = ttk.Label(frame_review, text="Редактирование вашего отзыва:")
          label_edit_review.grid(row=0, columnspan=2, sticky='w')

          label_new_rating = ttk.Label(frame_review, text="Новый рейтинг (1-5):")
          label_new_rating.grid(row=1, column=0, sticky='w')
          entry_new_rating = ttk.Entry(frame_review, width=10)
          entry_new_rating.insert(0, str(existing_review['rating']))
          entry_new_rating.grid(row=1, column=1, sticky='w')

          label_new_comment = ttk.Label(frame_review, text="Новый комментарий:")
          label_new_comment.grid(row=2, column=0, sticky='w')
          entry_new_comment = ttk.Entry(frame_review, width=30)
          entry_new_comment.insert(0, existing_review['comment'])
          entry_new_comment.grid(row=2, column=1, sticky='w')

          # Кнопки для сохранения изменений и удаления отзыва
          button_save_changes = ttk.Button(frame_review, text="Сохранить изменения",
                                      command=lambda: self.save_review_changes(
                                          fmid, entry_new_rating.get(), entry_new_comment.get(), text_area))
          button_save_changes.grid(row=3, column=0, pady=10)

          button_delete_review = ttk.Button(frame_review, text="Удалить отзыв",
                                         command=lambda: self.delete_review(fmid))
          button_delete_review.grid(row=3, column=1, pady=10)

        else:
           # Пользователь не оставлял отзыв, показываем форму для создания нового отзыва
           label_create_review = ttk.Label(frame_review, text="Создать новый отзыв:")
           label_create_review.grid(row=0, columnspan=2, sticky='w')

           label_new_rating_create = ttk.Label(frame_review, text="Рейтинг (1-5):")
           label_new_rating_create.grid(row=1, column=0, sticky='w')
           entry_new_rating_create = ttk.Entry(frame_review, width=10)
           entry_new_rating_create.grid(row=1, column=1, sticky='w')

           label_new_comment_create = ttk.Label(frame_review, text="Комментарий:")
           label_new_comment_create.grid(row=2, column=0, sticky='w')
           entry_new_comment_create = ttk.Entry(frame_review, width=30)
           entry_new_comment_create.grid(row=2, column=1, sticky='w')

           # Кнопка для отправки нового отзыва
           button_send_new_review = ttk.Button(frame_review, text="Отправить новый отзыв",
                                          command=lambda: self.send_new_review(
                                              fmid, entry_new_rating_create.get(), entry_new_comment_create.get(), text_area))
           button_send_new_review.grid(row=3, columnspan=2, pady=10)

        # Заблокируем изменение размера окна
        self.details_window.resizable(False, False)

        # Обновляем окно перед захватом фокуса
        self.details_window.update_idletasks()
        self.details_window.grab_set()

        # После завершения взаимодействия освобождаем захваченный фокус
        self.details_window.protocol("WM_DELETE_WINDOW", self.on_close_details_window)
    
    def on_close_details_window(self):
        '''
        Handles the closure of the details window.

        This method releases focus back to the parent window and destroys the details window.

        @requires: The details window must have been opened earlier.
        @modifies: Releases the captured focus and removes the details window from memory.
        @effects: Closes the details window and restores normal interaction with the main application window.
        @raises: No explicit exceptions, though implicit ones might occur due to improperly handled windows.
        @returns: None
        '''
        # Освобождаем фокус и закрываем окно
        self.details_window.grab_release()
        self.details_window.destroy()

    def send_new_review(self, fmid, rating, comment, text_area):
       '''
       Sends a new review for a specific market.

       This method handles adding a new review only if the user hasn't reviewed the market before.
       It validates the entered rating, adds the review to the database, and refreshes the market details.

       @requires: fmid must be a valid market identifier, rating must be an integer between 1 and 5, comment must be a string, and the user must be authenticated.
       @modifies: Database by inserting a new review and re-rendering the market details in the GUI.
       @effects: Updates the displayed details in the details window.
       @raises: ValueError if the rating cannot be converted to an integer.
       @returns: None
       '''
       # Этот метод вызывается только если пользователь еще не оставлял отзыв
       if not self.logged_in_user:
         messagebox.showwarning("Предупреждение", "Необходимо войти в систему.")
         return

       try:
           rating_value = int(rating)
           if 1 <= rating_value <= 5:
              self.review_mgr.add_review(fmid, rating_value, comment, self.logged_in_user)
            
              # Обновляем информацию о рынке
              updated_details = self.market_mgr.show_details(str(fmid), self.review_mgr, self.logged_in_user)
              text_area.config(state=tk.NORMAL)
              text_area.delete(1.0, tk.END)
              text_area.insert(tk.END, updated_details)
              text_area.config(state=tk.DISABLED)
            
              #messagebox.showinfo("Успех", "Ваш отзыв успешно отправлен.")
           else:
              messagebox.showwarning("Предупреждение", "Рейтинг должен быть от 1 до 5.")
       except ValueError:
           messagebox.showwarning("Предупреждение", "Недопустимый формат рейтинга.")

    def save_review_changes(self, fmid, new_rating, new_comment, text_area):
       '''
       Saves changes to an existing review for a market.

       This method processes edits to an existing review, validating the new rating and saving the changes to the database.
       Afterwards, it refreshes the displayed market details in the GUI.

       @requires: fmid must be a valid market identifier, new_rating must be an integer between 1 and 5, new_comment must be a string, and the user must be authenticated.
       @modifies: Updates the review in the database and re-rendering the market details in the GUI.
       @effects: Updates the displayed details in the details window.
       @raises: ValueError if the new rating cannot be converted to an integer.
       @returns: None
       '''
       if not self.logged_in_user:
         messagebox.showwarning("Предупреждение", "Необходимо войти в систему.")
         return
       try:
           rating_value = int(new_rating)
           if 1 <= rating_value <= 5:
              self.review_mgr.edit_review(fmid, rating_value, new_comment, self.logged_in_user)
            
              # Перезапрашиваем новую информацию о рынке после изменения отзыва
              updated_details = self.market_mgr.show_details(str(fmid), self.review_mgr, self.logged_in_user)
            
              # Обновляем текстовую область
              text_area.config(state=tk.NORMAL)
              text_area.delete(1.0, tk.END)
              text_area.insert(tk.END, updated_details)
              text_area.config(state=tk.DISABLED)
            
              #messagebox.showinfo("Успех", "Ваш отзыв успешно обновлён.")
           else:
              messagebox.showwarning("Предупреждение", "Рейтинг должен быть от 1 до 5.")
       except ValueError:
           messagebox.showwarning("Предупреждение", "Недопустимый формат рейтинга.")

    def delete_review(self, fmid):
        '''
        Deletes a review associated with a specific market.

        This method prompts the user for confirmation before removing the review from the database.
        If confirmed, the review is permanently deleted, and a success message is displayed.

        @requires: fmid must be a valid market identifier, and the user must be authenticated.
        @modifies: Removes the review from the database.
        @effects: Asks for user confirmation and displays feedback upon completion.
        @raises: No explicit exceptions, but potential issues may arise if the review doesn't exist.
        @returns: None
        '''
        if not self.logged_in_user:
            messagebox.showwarning("Предупреждение", "Необходимо войти в систему.")
            return
        answer = messagebox.askyesno("Подтверждение", "Вы действительно хотите удалить этот отзыв?")
        if answer:
            self.review_mgr.remove_review(fmid, self.logged_in_user)
            messagebox.showinfo("Успех", "Ваш отзыв удален.")

    def on_row_double_click(self, event):
        '''
        Handles the action triggered by double-clicking on a row in the treeview.

        This method retrieves the FMID (unique identifier) of the clicked market row and opens a details window for that market.

        @requires: An event triggered by a double click on a row in the treeview widget.
        @modifies: Opens a new window to display additional details about the selected market.
        @effects: Calls the `open_details_window()` method to render detailed information about the chosen market.
        @raises: No explicit exceptions, but underlying methods called may throw errors.
        @returns: None
        '''
        tree = event.widget
        selected_item = tree.selection()[0]  # Получаем первую выбранную строку
        fmid = tree.item(selected_item)['values'][0]  # FMID хранится в первой колонке
        self.open_details_window(fmid)

    def main_app(self):
        '''
        Sets up the core application interface.
        @requires: User logged in successfully
        @modifies: Layout of the main window
        @effects: Arranges tabs and other controls.
        @raises: None
        @returns: None
        '''
        # Закладочная панель
        self.tab_control = ttk.Notebook(self)
        self.tab_view_all = ttk.Frame(self.tab_control)
        self.tab_search = ttk.Frame(self.tab_control)
        self.tab_add_review = ttk.Frame(self.tab_control)
        self.tab_control.add(self.tab_view_all, text="Просмотр рынков")
        self.tab_control.add(self.tab_search, text="Поиск рынков")
        #self.tab_control.add(self.tab_add_review, text="Добавить отзыв")
        
        # Важно вызвать метод установки вкладки ДО добавления вкладочной панели
        self.setup_add_review_tab()

        self.tab_control.pack(expand=True, fill="both")
        
        # Кнопка для загрузки всех рынков
        button_view_all = ttk.Button(self.tab_view_all, text="Показать все рынки", command=self.load_all_markets)
        button_view_all.pack(pady=10)

        # Таблица для всех рынков
        self.tree_view_all = ttk.Treeview(self.tab_view_all, columns=("FMID", "Название", "Адрес"), show="headings")
        self.tree_view_all.heading("FMID", text="FMID")
        self.tree_view_all.column("FMID",minwidth=0,width=50)
        self.tree_view_all.heading("Название", text="Название")
        self.tree_view_all.column("Название",minwidth=0,width=250)
        self.tree_view_all.heading("Адрес", text="Адрес")
        self.tree_view_all.column("Адрес",minwidth=0,width=300)
        self.tree_view_all.pack(side="left", fill="both", expand=True)
        scrollbar_y = ttk.Scrollbar(self.tab_view_all, orient="vertical", command=self.tree_view_all.yview)
        scrollbar_y.pack(side="right", fill="y")
        self.tree_view_all.configure(yscrollcommand=scrollbar_y.set)
        
        Tooltip(self.tree_view_all, "Вход в подробности рынка, двойной клик на строке с рынком.", delay=700)

        # Обработчик двойного клика для таблицы всех рынков
        self.tree_view_all.bind('<Double-Button-1>', self.on_row_double_click)

        # Вкладка поиска рынков
        '''
        label_search_city = ttk.Label(self.tab_search, text="Город:", font=("Arial", 14))
        label_search_city.pack(pady=5)
        entry_search_city = ttk.Entry(self.tab_search, width=30)
        entry_search_city.pack(pady=5)

        label_search_state = ttk.Label(self.tab_search, text="Штат:", font=("Arial", 14))
        label_search_state.pack(pady=5)
        entry_search_state = ttk.Entry(self.tab_search, width=30)
        entry_search_state.pack(pady=5)
        
        button_search = ttk.Button(self.tab_search, text="Искать", command=lambda: self.search_markets(entry_search_city.get(), entry_search_state.get()))
        button_search.pack(pady=10)
        '''
         # Вызов функции для поиска
        button_search = ttk.Button(self.tab_search, text="Искать", command=self.open_search_dialog)
        button_search.pack(pady=10)
        
        # Таблица для результатов поиска
        self.tree_search = ttk.Treeview(self.tab_search, columns=("FMID", "Название", "Адрес"), show="headings")
        self.tree_search.heading("FMID", text="FMID")
        self.tree_search.column("FMID",minwidth=0,width=50)
        self.tree_search.heading("Название", text="Название")
        self.tree_search.column("Название",minwidth=0,width=250)
        self.tree_search.heading("Адрес", text="Адрес")
        self.tree_search.column("Адрес",minwidth=0,width=300)
        self.tree_search.pack(side="left", fill="both", expand=True)
        scrollbar_y_search = ttk.Scrollbar(self.tab_search, orient="vertical", command=self.tree_search.yview)
        scrollbar_y_search.pack(side="right", fill="y")
        self.tree_search.configure(yscrollcommand=scrollbar_y_search.set)
        
        Tooltip(self.tree_search, "Вход в подробности рынка, двойной клик на строке с рынком.", delay=700)

        # Обработчик двойного клика для таблицы поиска
        self.tree_search.bind('<Double-Button-1>', self.on_row_double_click)

        # Вкладка для добавления отзыва
        '''
        label_add_review = ttk.Label(self.tab_add_review, text="Добавить отзыв", font=("Arial", 14))
        label_add_review.pack(pady=10)
        label_add_review_fmid = ttk.Label(self.tab_add_review, text="FMID рынка:", font=("Arial", 14))
        label_add_review_fmid.pack(pady=5)
        entry_add_review_fmid = ttk.Entry(self.tab_add_review, width=30)
        entry_add_review_fmid.pack(pady=5)

        label_add_review_rating = ttk.Label(self.tab_add_review, text="Рейтинг (1-5):", font=("Arial", 14))
        label_add_review_rating.pack(pady=5)
        entry_add_review_rating = ttk.Entry(self.tab_add_review, width=30)
        entry_add_review_rating.pack(pady=5)

        label_add_review_comment = ttk.Label(self.tab_add_review, text="Комментарий:", font=("Arial", 14))
        label_add_review_comment.pack(pady=5)
        entry_add_review_comment = ttk.Entry(self.tab_add_review, width=30)
        entry_add_review_comment.pack(pady=5)

        button_add_review = ttk.Button(self.tab_add_review, text="Отправить отзыв", command=lambda: self.add_review(entry_add_review_fmid.get(), entry_add_review_rating.get(), entry_add_review_comment.get()))
        button_add_review.pack(pady=10)
        ''' 

    def load_all_markets(self):
        '''
        Populates the market listing section with all markets.
        @requires: Access to the database
        @modifies: Listing view
        @effects: Lists all available markets.
        @raises: None
        @returns: None
        '''
        markets = self.market_mgr.find_market_by_criteria()
        if markets:
            # Очистим таблицу перед загрузкой новых данных
            for child in self.tree_view_all.get_children():
                self.tree_view_all.delete(child)
            for market in markets:
                self.tree_view_all.insert("", "end", values=(market['FMID'], market['MarketName'], f"{market['street']}, {market['city']}, {market['state']}, {market['zip']}"))
        else:
            messagebox.showwarning("Предупреждение", "Нет доступных рынков.")

    def search_markets(self, city, state):
        '''
        Filters markets by city and state.
        @requires: city ϵ string, state ϵ string
        @modifies: Search results panel
        @effects: Displays matching markets.
        @raises: None
        @returns: None
        '''
        markets = self.market_mgr.find_market_by_criteria(city=city, state=state)
        if markets:
            # Очистим таблицу перед загрузкой новых данных
            for child in self.tree_search.get_children():
                self.tree_search.delete(child)
            for market in markets:
                self.tree_search.insert("", "end", values=(market['FMID'], market['MarketName'], f"{market['street']}, {market['city']}, {market['state']}, {market['zip']}"))
        else:
            messagebox.showwarning("Предупреждение", "Рынков не найдено.")
            
    
    def add_review(self, fmid, rating, comment):
        '''
        Allows users to leave a review for a market.
        @requires: fmid ϵ integer, rating ϵ integer, comment ϵ string
        @modifies: Reviews collection
        @effects: Appends a new review to the database.
        @raises: Validation errors
        @returns: Success or failure notification.
        '''
        if not self.logged_in_user:
            messagebox.showwarning("Предупреждение", "Необходимо войти в систему.")
            return
        try:
            rating_value = int(rating)
            if 1 <= rating_value <= 5:
                self.review_mgr.add_review(fmid, rating_value, comment, self.logged_in_user)
                messagebox.showinfo("Успех", "Отзыв успешно отправлен.")
            else:
                messagebox.showwarning("Предупреждение", "Рейтинг должен быть от 1 до 5.")
        except ValueError:
            messagebox.showwarning("Предупреждение", "Недопустимый формат рейтинга.")

    def setup_add_review_tab(self):
        '''
        Configures the "Add Review" tab in the notebook control.

        This method sets up the layout for the "Add Review" tab, which includes a search button, a treeview widget for displaying search results, and binding an event listener for handling double clicks on rows.

        @requires: None
        @modifies: GUI components inside the "Add Review" tab.
        @effects: Organizes widgets and binds event handlers within the tab.
        @raises: No explicit exceptions, but some operations might implicitly raise exceptions if widgets are misconfigured.
        @returns: None
        '''
        # Установка вкладки "Добавить отзыв"
        tab_add_review = ttk.Frame(self.tab_control)
        self.tab_control.add(tab_add_review, text="Добавить отзыв")

        # Кнопка поиска
        button_search = ttk.Button(tab_add_review, text="Искать", command=self.open_search_dialog_from_add_review)
        button_search.pack(pady=10)

        # Таблица для отображения результатов поиска
        self.tree_search_results = ttk.Treeview(tab_add_review, columns=("FMID", "Название", "Адрес"), show="headings")
        self.tree_search_results.heading("FMID", text="FMID")
        self.tree_search_results.column("FMID",minwidth=0,width=50)
        self.tree_search_results.heading("Название", text="Название")
        self.tree_search_results.column("Название",minwidth=0,width=250)
        self.tree_search_results.heading("Адрес", text="Адрес")
        self.tree_search_results.column("Адрес",minwidth=0,width=300)
        
        self.tree_search_results.pack(side="top", fill="both", expand=True)
        
        Tooltip(self.tree_search_results, "Вход в подробности рынка, двойной клик на строке с рынком.", delay=700)

        # Привязываем событие double-click к методу перехода в подробности
        self.tree_search_results.bind('<Double-Button-1>', self.on_row_double_click)

    def open_search_dialog_from_add_review(self):
       '''
       Opens a search dialog for selecting a search mode.

       This method presents a modal dialog allowing the user to choose between two modes of searching:
       1. By FMID (a unique market identifier),
       2. By part of the market name.

       Once the selection is made, the dialog captures the search term and triggers further processing.

       @requires: None
       @modifies: GUI by rendering a new top-level window.
       @effects: Provides a choice of search modes and initiates subsequent search logic.
       @raises: No explicit exceptions, but potential issues could arise if widgets are incorrectly configured.
       @returns: None
       '''
       # Диалоговое окно для выбора режима поиска
       dialog = tk.Toplevel(self)
       dialog.title("Выбор режима поиска")

       # Радио-кнопки для выбора режима поиска
       mode_choice = tk.IntVar()
       mode_choice.set(1)  # Изначально выбрано FMID

       fm_radio = ttk.Radiobutton(dialog, text="Поиск по FMID", variable=mode_choice, value=1)
       fm_radio.pack(pady=5)

       name_radio = ttk.Radiobutton(dialog, text="Поиск по части имени рынка", variable=mode_choice, value=2)
       name_radio.pack(pady=5)

       # Поле для ввода данных
       entry_field = ttk.Entry(dialog, width=30)
       entry_field.pack(pady=10)

       # Кнопка поиска
       button_search = ttk.Button(dialog, text="Искать", command=lambda: self.perform_search_from_add_review(mode_choice.get(), entry_field.get(), dialog))
       button_search.pack(pady=10)    
    
    def perform_search_from_add_review(self, mode, search_term, dialog):
       '''
        Performs a search based on the selected mode and provided search term.

        Depending on the selected mode, this method searches either by FMID (unique market identifier) or by a substring of the market name.
        Upon finding matches, it clears old search results, inserts new entries into the treeview, and closes the search dialog.

        @requires: mode must be 1 (for FMID-based search) or 2 (for name-based search), search_term must be a non-empty string, and dialog must be a valid Tkinter TopLevel window.
        @modifies: Content of the treeview widget and optionally modifies the dialog window.
        @effects: Refreshes the treeview with search results and closes the search dialog.
        @raises: ValueError if an unsupported search mode is used.
        @returns: None
       '''  
       # Очищаем старые результаты
       for child in self.tree_search_results.get_children():
          self.tree_search_results.delete(child)

       # Основываемся на выборе пользователя
       if mode == 1:  # Поиск по FMID
           markets = self.market_mgr.find_market_by_criteria(fmid=search_term)
       elif mode == 2:  # Поиск по части имени рынка
            markets = self.market_mgr.find_market_by_criteria(market_name_part=search_term)
       else:
             raise ValueError("Неподдержанный режим поиска!")

       # Добавляем результаты в дерево
       if markets:
         for market in markets:
            self.tree_search_results.insert("", "end", values=(market['FMID'], market['MarketName'], f"{market['street']}, {market['city']}, {market['state']}, {market['zip']}"))
         dialog.destroy()  # Закрытие окна поиска
       else:
            #messagebox.showwarning("Предупреждение", "Рынков не найдено.")
            #dialog.destroy()  # Закрытие окна поиска
            self._no_results_label = ttk.Label(dialog, text="Рынков не найдено.", foreground="red")
            self._no_results_label.pack(pady=5)

    def perform_search(self, city, state, zip_code, latitude, longitude, max_distance, apply_sort, sort_order, dialog):
       '''
       Conducts a search for farmers' markets based on the provided criteria.

       This method filters markets using location-specific parameters such as city, state, ZIP code, geographic coordinates, and maximum distance.
       Optionally, it calculates and sorts the results by average rating.

       @requires: City, state, and other filters should be valid strings; latitude, longitude, and max_distance must be convertible to floats if applicable.
       @modifies: Updates the treeview widget with search results.
       @effects: Clears old search results, performs a database query, and refills the treeview with new results.
       @raises: ValueError if invalid numeric conversions occur for latitude, longitude, or max_distance.
       @returns: None
       '''
       # Фильтрация параметров поиска
       kwargs = {}
       if city.strip(): kwargs['city'] = city
       if state.strip(): kwargs['state'] = state
       if zip_code.strip(): kwargs['zip_code'] = zip_code
       if latitude.strip() and longitude.strip() and max_distance.strip():
         kwargs['latitude'] = float(latitude)
         kwargs['longitude'] = float(longitude)
         kwargs['max_distance'] = float(max_distance)

       # Первый этап поиска без расчёта среднего рейтинга
       markets = self.market_mgr.find_market_by_criteria(**kwargs)

       # Если включен флаг сортировки по рейтингу
       if apply_sort:
         # Теперь здесь производим расчет среднего рейтинга
         for market in markets:
             average_rating = self.market_mgr.calculate_average_rating(market['FMID'])
             market['average_rating'] = average_rating

         # Сортируем рынки по среднему рейтингу
         markets = self.market_mgr.sort_markets(markets, 'rating', sort_order)

       # Остальная логика вывода результатов остаётся прежней...
       if markets:
         # Очистим старую информацию
         for item in self.tree_search.get_children():
             self.tree_search.delete(item)

         # Записываем новые результаты в TreeView
         for market in markets:
            self.tree_search.insert("", "end", values=(market['FMID'], market['MarketName'], f"{market['street']}, {market['city']}, {market['state']}, {market['zip']}"))

         # Закрываем диалог поиска
         dialog.destroy()
       else:
          # Если ничего не найдено, покажем предупреждение
          no_results_label = ttk.Label(dialog, text="Рынков не найдено.", foreground="red")
          no_results_label.pack(pady=5)
    
    def on_row_double_click(self, event):
        '''
        Handles the double-click event on a row in the search results.

        When a user double-clicks on a row in the search results treeview, this method extracts the FMID (unique market identifier) of the selected market and opens a details window for that market.

        @requires: The event parameter contains a valid treeview widget reference.
        @modifies: None
        @effects: Opens a new window with detailed information about the selected market.
        @raises: No explicit exceptions, but internal calls may raise errors.
        @returns: None
        '''
        # Обрабатываем выбор определенного рынка из результатов поиска
        tree = event.widget
        selected_item = tree.selection()[0]
        fmid = tree.item(selected_item)['values'][0]
        self.open_details_window(fmid)

    def show_tooltip_message(self, message, duration_ms=2000):
        '''
        Displays a floating tooltip-like message above the application window.

        This method creates a small semi-transparent popup window (tooltip) that appears briefly over the application, providing quick notifications or hints.

        @requires: message must be a non-empty string.
        @modifies: Creates a temporary Toplevel window.
        @effects: Briefly shows a translucent tooltip-style window at the upper-right corner of the screen.
        @raises: No explicit exceptions, but potential issues may arise if GUI elements are mishandled.
        @returns: None
        '''
        tooltip = tk.Toplevel(self)
        tooltip.overrideredirect(True)  # Без декораций и границы окна
        tooltip.attributes('-alpha', 0.9)  # Немного прозрачный фон
        tooltip.attributes('-topmost', True)  # Всегда сверху

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        tooltip_width = 200
        tooltip_height = 50
        x_pos = screen_width - tooltip_width - 10  # Позиция справа вверху
        y_pos = 10
        tooltip.geometry(f"{tooltip_width}x{tooltip_height}+{x_pos}+{y_pos}")

        label = ttk.Label(tooltip, text=message, background="#ffffcc", relief="solid", padding=5)
        label.pack()

        # Автоматически закрываем окно после указанного времени
        tooltip.after(duration_ms, tooltip.destroy)

    def open_search_dialog(self):
       '''
       Opens a search dialog window to collect user-specified search criteria.

       This method generates a modal dialog window where users can provide search terms, such as city, state, ZIP code, geolocation coordinates, and sorting preferences. Based on these parameters, it subsequently invokes the search process.

       @requires: None
       @modifies: Creates a new Toplevel window and places interactive widgets within it.
       @effects: Displays a modal dialog with configurable input fields and buttons to initiate the search.
       @raises: No explicit exceptions, but potential issues could arise if widget configurations are incorrect.
       @returns: None
       '''
       # Окно поиска
       dialog = tk.Toplevel(self)
       dialog.title("Критерии поиска")

       # Город
       label_city = ttk.Label(dialog, text="Город:", font=("Arial", 14))
       label_city.pack(pady=5)
       entry_city = ttk.Entry(dialog, width=30)
       entry_city.pack(pady=5)

       # Штат
       label_state = ttk.Label(dialog, text="Штат:", font=("Arial", 14))
       label_state.pack(pady=5)
       entry_state = ttk.Entry(dialog, width=30)
       entry_state.pack(pady=5)

       # Индекс
       label_zip = ttk.Label(dialog, text="Индекс (необязательно):", font=("Arial", 14))
       label_zip.pack(pady=5)
       entry_zip = ttk.Entry(dialog, width=30)
       entry_zip.pack(pady=5)

       # Широта
       label_lat = ttk.Label(dialog, text="Широта для расчета расстояния (необязательно):", font=("Arial", 14))
       label_lat.pack(pady=5)
       entry_lat = ttk.Entry(dialog, width=30)
       entry_lat.pack(pady=5)

       # Долгота
       label_lon = ttk.Label(dialog, text="Долгота для расчета расстояния (необязательно):", font=("Arial", 14))
       label_lon.pack(pady=5)
       entry_lon = ttk.Entry(dialog, width=30)
       entry_lon.pack(pady=5)
       
       # Инициализируем виджет для дистанции вне области видимости
       self.entry_dist = None

       # Расстояние
       
       label_dist = ttk.Label(dialog, text="Максимальное расстояние (мили):", font=("Arial", 14))
       label_dist.pack(pady=5)
       entry_dist = ttk.Entry(dialog, width=30)
       entry_dist.pack(pady=5)
       
       # Применять сортировку?
       var_apply_sort = tk.BooleanVar(value=False)
       chk_apply_sort = ttk.Checkbutton(dialog, text="Применить сортировку по рейтингу?", variable=var_apply_sort)
       chk_apply_sort.pack(pady=5)
       
       # Порядок сортировки
       var_sort_order = tk.StringVar(value="desc")  # По умолчанию сортировка убывающая
       chk_sort_asc = ttk.Checkbutton(dialog, text="Сортировать по возрастанию?", variable=var_sort_order, onvalue="asc", offvalue="desc")
       chk_sort_asc.pack(pady=5)

       # Кнопка для запуска поиска
       button_search = ttk.Button(dialog, text="Искать", command=lambda: self.perform_search(
        entry_city.get(),
        entry_state.get(),
        entry_zip.get(),
        entry_lat.get(),
        entry_lon.get(),
        getattr(self.entry_dist, 'get', lambda : '')(),  # Используем getattr для безопасной обработки отсутствия поля
        var_apply_sort.get(),
        var_sort_order.get(),
        dialog
       ))
       button_search.pack(pady=10)

# Точка входа в приложение
if __name__ == "__main__":
    db_connector = DatabaseConnection(db_config)
    app = FarmersMarketsApp(db_connector)
    app.mainloop()
		