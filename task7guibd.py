import tkinter as tk
from tkinter import ttk, messagebox
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
db_config = {
    'dbname': 'farmers_db',
    'user': 'sasha',
    'password': '1973',
    'host': 'localhost',
    'port': '5433'
}

# Радиус Земли в милях
EARTH_RADIUS_MILES = 3958.8

# Класс для работы с базой данных
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

# Класс для работы с пользователями
class UserManager:
    def __init__(self, db_connector):
        self.db_connector = db_connector

    def check_user_exists(self, username):
        query = "SELECT COUNT(*) FROM users WHERE username=%s;"
        result = self.db_connector.execute_query(query, (username,))
        return result[0][0] > 0

    def create_user(self, username, password, firstname, lastname):
        hashed_password = sha256(password.encode()).hexdigest()
        data = {
            'username': username,
            'password_hash': hashed_password,
            'firstname': firstname,
            'lastname': lastname
        }
        self.db_connector.insert_data('users', data)

    def verify_login(self, username, password):
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
        self.db_connector = db_connector

    def add_review(self, fmid, rating, comment, author):
        data = {
            'fmid': fmid,
            'rating': rating,
            'comment': comment,
            'author': author
        }
        self.db_connector.insert_data('reviews', data)

    def get_reviews_by_fmid(self, fmid):
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
        query = "UPDATE reviews SET rating=%s, comment=%s WHERE fmid=%s AND author=%s;"
        with closing(psycopg2.connect(**self.db_connector.db_config)) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (new_rating, new_comment, fmid, author))
                conn.commit()

    def remove_review(self, fmid, author):
        query = "DELETE FROM reviews WHERE fmid=%s AND author=%s;"
        with closing(psycopg2.connect(**self.db_connector.db_config)) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (fmid, author))
                conn.commit()
    
    def user_has_reviewed(self, fmid, author):
        """Проверяет, оставил ли пользователь отзыв по этому рынку."""
        query = "SELECT COUNT(*) FROM reviews WHERE fmid=%s AND author=%s;"
        result = self.db_connector.execute_query(query, (fmid, author))
        return result[0][0] > 0
    
# Класс для работы с рынками
class MarketManager:
    def __init__(self, db_connector):
        self.db_connector = db_connector

    def find_market_by_criteria(self, **kwargs):
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

    def sort_markets(self, markets, field, reverse=False):
        sorted_markets = sorted(markets, key=lambda x: x[field], reverse=reverse)
        return sorted_markets

    def paginate_results(self, markets):
        PAGE_SIZE = 10
        pages = []
        num_pages = math.ceil(len(markets) / PAGE_SIZE)
        for i in range(num_pages):
            start = i * PAGE_SIZE
            end = start + PAGE_SIZE
            pages.append(markets[start:end])
        return pages
    def show_details(self, fmid_or_name, review_manager, logged_in_user):
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
        super().__init__()
        self.title("Приложение фермерских рынков")
        self.geometry("800x600")
        self.db_connector = db_connector
        self.user_mgr = UserManager(db_connector)
        self.review_mgr = ReviewManager(db_connector)
        self.market_mgr = MarketManager(db_connector)
        self.logged_in_user = None
        self.details_window = None  # Переменная для отслеживания открытого окна деталей
        self.login_window()

    def login_window(self):
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

    def authenticate(self, username, password):
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
        # Очищаем старое содержимое окна
        for widget in self.winfo_children():
            widget.destroy()

        # Создаем главную часть приложения
        self.main_app()

    def register_window(self):
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
        if self.user_mgr.check_user_exists(username):
            messagebox.showerror("Ошибка", "Такой пользователь уже существует.")
        else:
            self.user_mgr.create_user(username, password, firstname, lastname)
            messagebox.showinfo("Успех", "Вы успешно зарегистрированы.")
            self.login_window()

    def open_details_window(self, fmid):
        # Если окно уже открыто, поднимаем его поверх остальных окон
        if self.details_window is not None and self.details_window.winfo_exists():
          self.details_window.lift()
          return

        # Создаем новое окно
        self.details_window = tk.Toplevel(self)
        self.details_window.title("Подробности о рынке")
        self.details_window.geometry("600x400")

        # Получаем детали выбранного рынка
        details = self.market_mgr.show_details(str(fmid), self.review_mgr, self.logged_in_user)

        # Выводим информацию о рынке в Text виджет
        text_area = tk.Text(self.details_window,height=5, wrap=tk.WORD)
        text_area.insert(tk.END, details)
        text_area.pack(fill="both", expand=True)

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
    
    def send_new_review(self, fmid, rating, comment, text_area):
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
        if not self.logged_in_user:
            messagebox.showwarning("Предупреждение", "Необходимо войти в систему.")
            return
        answer = messagebox.askyesno("Подтверждение", "Вы действительно хотите удалить этот отзыв?")
        if answer:
            self.review_mgr.remove_review(fmid, self.logged_in_user)
            messagebox.showinfo("Успех", "Ваш отзыв удален.")

    def on_row_double_click(self, event):
        tree = event.widget
        selected_item = tree.selection()[0]  # Получаем первую выбранную строку
        fmid = tree.item(selected_item)['values'][0]  # FMID хранится в первой колонке
        self.open_details_window(fmid)

    def main_app(self):
        # Закладочная панель
        self.tab_control = ttk.Notebook(self)
        self.tab_view_all = ttk.Frame(self.tab_control)
        self.tab_search = ttk.Frame(self.tab_control)
        self.tab_add_review = ttk.Frame(self.tab_control)
        self.tab_control.add(self.tab_view_all, text="Просмотр рынков")
        self.tab_control.add(self.tab_search, text="Поиск рынков")
        self.tab_control.add(self.tab_add_review, text="Добавить отзыв")
        self.tab_control.pack(expand=True, fill="both")
        
        # Кнопка для загрузки всех рынков
        button_view_all = ttk.Button(self.tab_view_all, text="Показать все рынки", command=self.load_all_markets)
        button_view_all.pack(pady=10)

        # Таблица для всех рынков
        self.tree_view_all = ttk.Treeview(self.tab_view_all, columns=("FMID", "Название", "Адрес"), show="headings")
        self.tree_view_all.heading("FMID", text="FMID")
        self.tree_view_all.heading("Название", text="Название")
        self.tree_view_all.heading("Адрес", text="Адрес")
        self.tree_view_all.pack(side="left", fill="both", expand=True)
        scrollbar_y = ttk.Scrollbar(self.tab_view_all, orient="vertical", command=self.tree_view_all.yview)
        scrollbar_y.pack(side="right", fill="y")
        self.tree_view_all.configure(yscrollcommand=scrollbar_y.set)

        # Обработчик двойного клика для таблицы всех рынков
        self.tree_view_all.bind('<Double-Button-1>', self.on_row_double_click)

        # Вкладка поиска рынков
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

        # Таблица для результатов поиска
        self.tree_search = ttk.Treeview(self.tab_search, columns=("FMID", "Название", "Адрес"), show="headings")
        self.tree_search.heading("FMID", text="FMID")
        self.tree_search.heading("Название", text="Название")
        self.tree_search.heading("Адрес", text="Адрес")
        self.tree_search.pack(side="left", fill="both", expand=True)
        scrollbar_y_search = ttk.Scrollbar(self.tab_search, orient="vertical", command=self.tree_search.yview)
        scrollbar_y_search.pack(side="right", fill="y")
        self.tree_search.configure(yscrollcommand=scrollbar_y_search.set)

        # Обработчик двойного клика для таблицы поиска
        self.tree_search.bind('<Double-Button-1>', self.on_row_double_click)

        # Вкладка для добавления отзыва
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

    def load_all_markets(self):
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

# Точка входа в приложение
if __name__ == "__main__":
    db_connector = DatabaseConnection(db_config)
    app = FarmersMarketsApp(db_connector)
    app.mainloop()
		