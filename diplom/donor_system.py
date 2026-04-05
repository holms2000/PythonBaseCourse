import tkinter as tk
from tkinter import ttk, messagebox
import psycopg2
import hashlib
from contextlib import closing
import os
from dotenv import load_dotenv
import sys

# --- НАСТРОЙКИ ПОДКЛЮЧЕНИЯ К БД ---
env_path = os.path.join(sys.path[0], '.env.example')
if not load_dotenv(env_path):
    load_dotenv()

DB_CONFIG = {
    "dbname": os.getenv("DBNAME"),
    "user": os.getenv("LOGIN"),
    "password": os.getenv("PASSWORD"),
    "host": os.getenv("HOST"),
    "port": os.getenv("PORT")
}
# ------------------------------------------------------


class DatabaseConnection:
    """Класс для работы с базой данных PostgreSQL с использованием контекстного менеджера."""
    def __init__(self, db_config):
        self.db_config = db_config

    def execute_query(self, query, params=None):
        '''Выполняет запрос SELECT и возвращает результат.'''
        '''
        with closing(psycopg2.connect(**self.db_config)) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
        '''
        try:
            with closing(psycopg2.connect(**self.db_config)) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    conn.commit()
                    return cursor.fetchall()
        except Exception as e:
            # Это покажет полную ошибку в терминале, где вы запускаете скрипт
            print(f"--- ОШИБКА БАЗЫ ДАННЫХ ---")
            print(f"Запрос: {query}")
            print(f"Параметры: {params}")
            print(f"Тип ошибки: {type(e).__name__}")
            print(f"Сообщение: {e}")  # <-- ЭТО ТО, ЧТО НАМ НУЖНО
            print(f"------------------------")
            
            messagebox.showerror("Ошибка БД", str(e))
            return None
            
    def execute_update(self, query, params=None):
        '''Выполняет запрос INSERT, UPDATE, DELETE.'''
        try:
            with closing(psycopg2.connect(**self.db_config)) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    conn.commit()
                    return True
        except Exception as e:
            messagebox.showerror("Ошибка БД", str(e))
            return False


class AuthWindow(tk.Tk):
    """Окно авторизации и регистрации."""
    def __init__(self):
        super().__init__()
        self.current_user_id = None
        self.current_user_login = None
        
        self.title("Система учёта доноров")
        self.geometry("300x250")
        self.resizable(False, False)
        
        # --- Элементы интерфейса: Логин ---
        tk.Label(self, text="Логин:").pack(pady=5)
        self.login_entry = tk.Entry(self)
        self.login_entry.pack(pady=5)

        # --- Элементы интерфейса: Пароль ---
        tk.Label(self, text="Пароль:").pack(pady=5)
        self.pass_entry = tk.Entry(self, show="*")
        self.pass_entry.pack(pady=5)

        # --- Элементы интерфейса: Кнопки ---
        self.login_btn = tk.Button(self, text="Войти", command=self.login)
        self.login_btn.pack(pady=10)
        
        tk.Button(self, text="Регистрация", command=self.open_register).pack(pady=5)

        # --- Привязка горячих клавиш (Навигация по Enter) ---
        # 1. Переход фокуса с поля "Логин" на поле "Пароль"
        self.login_entry.bind('<Return>', lambda event: self.pass_entry.focus_set())
        
        # 2. Переход с поля "Пароль" на кнопку "Войти"
        self.pass_entry.bind('<Return>', lambda event: self.login_btn.invoke())

    def login(self, event=None):
       """
       Метод авторизации пользователя.
       Принимает event=None для совместимости с биндом клавиш.
       """
       login = self.login_entry.get()
       password = self.pass_entry.get()
    
       if not login or not password:
           messagebox.showwarning("Ошибка", "Заполните все поля")
           return

       password_hash = hashlib.sha256(password.encode()).hexdigest()
    
       db = DatabaseConnection(DB_CONFIG)
    
       result = db.execute_query(
           "SELECT id, login FROM users WHERE login = %s AND passwordhash = %s",
           (login, password_hash)
       )

       if result is None:
           messagebox.showerror("Ошибка", "Не удалось выполнить запрос к базе данных.")
    
       elif not result: 
           messagebox.showerror("Ошибка", "Неверный логин или пароль")
    
       else:
            self.current_user_id = result[0][0]
            self.current_user_login = result[0][1]
        
            self.destroy()
            MainMenu(self.current_user_id, self.current_user_login).mainloop()
            
    def open_register(self):
        """
        Открывает окно регистрации.
        Создаёт его без родителя-мастера (None) для избежания конфликтов,
        и передаёт ссылку на себя для обратного вызова.
        """
        register_window = RegisterWindow(None)
        register_window.parent_auth = self 

    def on_register_success(self, login, password):
        """
        Метод обратного вызова из RegisterWindow.
        Автоматически подставляет логин и пароль в поля и выполняет вход.
        """
        # Очищаем поля на случай, если там были старые данные
        self.login_entry.delete(0, tk.END)
        self.pass_entry.delete(0, tk.END)
        
        # Вставляем новые данные
        self.login_entry.insert(0, login)
        self.pass_entry.insert(0, password)
        
        # Вызываем метод входа
        self.login()

class RegisterWindow(tk.Toplevel):
    """Окно регистрации нового пользователя."""
    def __init__(self, parent):
        """
        Инициализация окна регистрации.
        :param parent: Параметр передается в Toplevel, но не используется для логики.
                       Окно создается с parent=None для избежания конфликтов.
        """
        super().__init__(parent)
        # Ссылка на окно авторизации будет присвоена вручную после создания окна
        self.parent_auth = None 

        self.title("Регистрация")
        self.geometry("300x240")
        self.resizable(False, False)
        
        # --- Элементы интерфейса: Логин ---
        tk.Label(self, text="Логин:").pack(pady=5)
        self.login_entry = tk.Entry(self)
        self.login_entry.pack(pady=5)

        # --- Элементы интерфейса: Пароль ---
        tk.Label(self, text="Пароль:").pack(pady=5)
        self.pass_entry = tk.Entry(self, show="*")
        self.pass_entry.pack(pady=5)
        
        # --- Элементы интерфейса: Кнопка регистрации ---
        self.register_btn = tk.Button(self, text="Зарегистрироваться", command=self.register)
        self.register_btn.pack(pady=10)

        # --- Элементы интерфейса: Статусное поле ---
        self.status_label = tk.Label(self, text="", fg="black")
        self.status_label.pack(pady=5)

        # --- Привязка горячих клавиш (Навигация по Enter) ---
        # 1. Переход фокуса с поля "Логин" на поле "Пароль"
        self.login_entry.bind('<Return>', lambda event: self.pass_entry.focus_set())
        
        # 2. Переход фокуса с поля "Пароль" на кнопку "Зарегистрироваться"
        self.pass_entry.bind('<Return>', lambda event: self.register_btn.invoke())

    def register(self):
        """Обработчик нажатия кнопки 'Зарегистрироваться'."""
        # Блокируем кнопку, чтобы избежать повторных нажатий во время запроса
        self.register_btn.config(state=tk.DISABLED)
        
        # Очищаем статус перед началом операции
        self.status_label.config(text="", fg="black")

        login = self.login_entry.get().strip()
        password = self.pass_entry.get().strip()
        
        # Валидация: проверка на пустые поля
        if not login or not password:
            self.status_label.config(text="⚠ Заполните все поля", fg="red")
            self.register_btn.config(state=tk.NORMAL) # Разблокируем кнопку
            return

        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        db = DatabaseConnection(DB_CONFIG)
        
        try:
            success = db.execute_update(
                "INSERT INTO users (login, passwordhash) VALUES (%s, %s)",
                (login, password_hash)
            )
            
            if success:
                self.status_label.config(text="✅ Регистрация прошла успешно!", fg="green")
                # Вызываем метод для передачи данных родителю и закрытия окна
                self._notify_parent_and_close()
            else:
                # Если success == False, ошибка уже показана в messagebox внутри execute_update
                self.status_label.config(text="❌ Ошибка регистрации", fg="red")
                self.register_btn.config(state=tk.NORMAL)

        except Exception as e:
            # Обработка непредвиденных ошибок (например, разрыв соединения с БД)
            self.status_label.config(text=f"⚠ Ошибка: {str(e)}", fg="red")
            self.register_btn.config(state=tk.NORMAL)

    def _notify_parent_and_close(self):
        """
        Внутренний метод для передачи данных родительскому окну и закрытия.
        Проверяет наличие родительского окна перед вызовом его метода.
        """
        login = self.login_entry.get()
        password = self.pass_entry.get()

        # Проверяем, что ссылка на родительское окно существует
        # и у него есть метод для обработки успешной регистрации.
        if hasattr(self, 'parent_auth') and hasattr(self.parent_auth, 'on_register_success'):
            self.parent_auth.on_register_success(login, password)
        
        self.destroy() # Закрываем текущее окно регистрации


class MainMenu(tk.Tk):
    """Главное меню после авторизации."""
    def __init__(self, user_id, user_login):
        super().__init__()
        self.user_id = user_id
        self.user_login = user_login
        
        self.title(f"Главное меню | Пользователь: {user_login}")
        self.geometry("400x200")
        
        # Создаем фрейм для кнопок и размещаем его по центру с помощью grid + sticky
        btn_frame = tk.Frame(self)
        btn_frame.pack(expand=True)
         
        ttk.Button(btn_frame, text="Добавить донора и биоматериал", command=lambda: self.open_add_donor()).grid(row=0, column=0, padx=50, pady=20)
        ttk.Button(btn_frame, text="Поиск доноров / биоматериалов", command=lambda: self.open_search()).grid(row=1, column=0, padx=50, pady=20)


    def open_add_donor(self):
         AddDonorWindow()

    def open_search(self):
         SearchWindow()


class AddDonorWindow(tk.Toplevel):
    """Окно для ввода данных донора и биоматериала."""
    def __init__(self):
        super().__init__()
        # Словари для хранения переменных полей
        self.donor_entries = {}  # Ключ: название поля, Значение: StringVar
        self.bio_entries = {}

        # --- Вкладки ---
        self.tab_control = ttk.Notebook(self)
        self.donor_tab = ttk.Frame(self.tab_control)
        self.bio_tab = ttk.Frame(self.tab_control)
        
        # Вкладка 1: Донор (активна сразу)
        self.tab_control.add(self.donor_tab, text='Данные донора')
        
        # --- Поля донора ---
        fields_donor = {
            "Пол (М/Ж)": ("combobox", ('М', 'Ж')),
            "Дата рождения (ГГГГ-ММ-ДД)": ("entry", 10),
            "Группа крови": ("combobox", ('O(I)', 'A(II)', 'B(III)', 'AB(IV)')),
            "Резус-фактор": ("combobox", ('+', '-')),
            "Дети (Да/Нет)": ("combobox", ('Да', 'Нет')),
            "Рост (см)": ("entry", 5),
            "Вес (кг)": ("entry", 5),
            "Национальность": ("combobox", ('Русский', 'Украинец','Белорусс')),
            "Цвет волос": ("combobox", ('Блондин', 'Брюнет','Шатен')),
            "Волосы (тип)": ("combobox", ('Прямые', 'Вьющиеся')),
            "Разрез глаз": ("combobox", ('Прямой', 'Раскосый')),
            "Цвет глаз": ("combobox", ('Зеленые', 'Серные')),
            "Нос (форма)": ("combobox", ('Прямые', 'Вьющиеся')),
            "Овал лица": ("combobox", ('Круглое', 'Полное')),
            "Лоб": ("combobox", ('Широкий', 'Узкий')),
            "Телосложение": ("combobox", ('Нормальное', 'Рахитическое')),
            "Размер одежды": ("entry", 10),
            "Размер обуви": ("entry", 10),
            "Образование": ("combobox", ('Высшее', 'Среднее')),
            "Профессия": ("entry", 50),
            "Наличие стигм (Да/Нет)": ("combobox", ('Да', 'Нет')),
        }
        
        row_count = 0
        for label_text, (widget_type, params) in fields_donor.items():
            tk.Label(self.donor_tab, text=label_text).grid(row=row_count, column=0, sticky="e", padx=5, pady=2)
            
            if widget_type == "entry":
                entry_var = tk.StringVar()
                entry = tk.Entry(self.donor_tab, textvariable=entry_var, width=params)
                # Привязываем маску для даты рождения
                if label_text == "Дата рождения (ГГГГ-ММ-ДД)":
                    entry.bind('<KeyRelease>', self.on_date_input)
                entry.grid(row=row_count, column=1, sticky="w", padx=5, pady=2)
                self.donor_entries[label_text] = entry_var
                
            elif widget_type == "combobox":
                combo_var = tk.StringVar()
                combo = ttk.Combobox(self.donor_tab, textvariable=combo_var, values=params, state='readonly')
                combo.grid(row=row_count, column=1, sticky="w", padx=5, pady=2)
                self.donor_entries[label_text] = combo_var
                
            row_count += 1

        # Статусное поле для вкладки "Донор"
        self.save_status_label = tk.Label(self.donor_tab, text="", fg="black")
        self.save_status_label.grid(row=row_count, column=0, columnspan=2, pady=(10, 0))
        
        row_count += 1
        ttk.Button(self.donor_tab,
                  text="Сохранить донора и перейти к биоматериалу",
                  command=self.save_donor).grid(row=row_count, column=0, columnspan=2, pady=15)
        
        # --- Поля биоматериала (на второй вкладке) ---
        fields_bio = {
            "Наименование биоматериала": ("combobox", ('сперма', 'ооцит', 'эмбрион')),
            "Дата получения (ГГГГ-ММ-ДД)": ("entry", 10),
            "Срок годности (ГГГГ-ММ-ДД)": ("entry", 10),
            "Тип материала": ("combobox", ('крио', 'нативный')),
            "Количество материала": ("entry", 10),
            "Единицы измерения": ("combobox", ('ед', 'мл')),
            }
        
        row_bio_count = 0
        for label_text, (widget_type, params) in fields_bio.items():
            tk.Label(self.bio_tab, text=label_text).grid(row=row_bio_count, column=0, sticky="e", padx=5, pady=2)
            
            if widget_type == "entry":
                entry_var = tk.StringVar()
                entry = tk.Entry(self.bio_tab, textvariable=entry_var, width=params)
                # Привязываем маску для дат биоматериала
                if "Дата" or "Срок"  in label_text:
                    entry.bind('<KeyRelease>', self.on_date_input)
                entry.grid(row=row_bio_count, column=1, sticky="w", padx=5, pady=2)
                self.bio_entries[label_text] = entry_var
                
            elif widget_type == "combobox":
                combo_var = tk.StringVar()
                combo = ttk.Combobox(self.bio_tab, textvariable=combo_var, values=params, state='readonly')
                combo.grid(row=row_bio_count, column=1, sticky="w", padx=5, pady=2)
                self.bio_entries[label_text] = combo_var
                
            row_bio_count += 1

        # Статусное поле для вкладки "Биоматериал"
        self.bio_status_label = tk.Label(self.bio_tab, text="", fg="black")
        self.bio_status_label.grid(row=row_bio_count, column=0, columnspan=2, pady=(10, 0))
        row_bio_count += 1

        tk.Label(self.bio_tab, text="Генетический паспорт").grid(row=row_bio_count, column=0, sticky="e", padx=5, pady=10)
        self.bio_genetic_passport_var = tk.BooleanVar()
        ttk.Checkbutton(self.bio_tab, variable=self.bio_genetic_passport_var).grid(row=row_bio_count, column=1, sticky="w")
        
        row_bio_count += 1
        ttk.Button(self.bio_tab,
                  text="Сохранить биоматериал и закрыть окно",
                  command=self.save_biological_material).grid(row=row_bio_count, column=0, columnspan=2, pady=15)
        
        self.tab_control.pack(expand=True, fill='both')
        
        self.donor_id = None 

    def on_date_input(self, event):
       """
       Форматирует ввод в поле даты по маске ГГГГ-ММ-ДД.
       """
       widget = event.widget
       current_text = widget.get()

       # Удаляем все символы, кроме цифр
       digits = ''.join(filter(str.isdigit, current_text))
       
       new_text = ""
       # Собираем новую строку с маской
       if len(digits) > 4:
           new_text = f"{digits[:4]}-"
           if len(digits) > 6:
               new_text += f"{digits[4:6]}-{digits[6:8]}"
           else:
               new_text += f"{digits[4:6]}"
       else:
           new_text = digits[:4]

       new_text = new_text[:10]

       # Обновляем поле только если текст изменился (предотвращает рекурсию)
       if current_text != new_text:
           widget.delete(0, tk.END)
           widget.insert(0, new_text)

       # Управление позицией курсора
       cursor_pos = widget.index(tk.INSERT)
       
       # Если курсор находится на месте дефиса или в конце строки при наличии следующего дефиса,
       # сдвигаем его вправо или на следующую логическую позицию.
       if cursor_pos < len(new_text):
           next_char = new_text[cursor_pos] if cursor_pos < len(new_text) else None
           if next_char == '-':
               widget.icursor(cursor_pos + 1)
           elif cursor_pos == 4 and len(new_text) > 5: # После ввода года курсор переходит к месяцу
               widget.icursor(5)
           elif cursor_pos == 7 and len(new_text) > 8: # После ввода месяца курсор переходит к дню
               widget.icursor(8)


    def save_donor(self):
       """Сохраняет данные донора в БД и активирует вторую вкладку."""
       data = {field: var.get() for field, var in self.donor_entries.items()}

       # Обработка булевых значений Да/Нет
       data['Дети (Да/Нет)'] = data['Дети (Да/Нет)'] == 'Да'
       data['Наличие стигм (Да/Нет)'] = data['Наличие стигм (Да/Нет)'] == 'Да'

       # Проверка обязательных полей донора с выводом под кнопкой
       required_fields = ['Пол (М/Ж)', 'Дата рождения (ГГГГ-ММ-ДД)', 'Группа крови', 'Резус-фактор']
       missing_fields = [field for field in required_fields if not data.get(field)]

       if missing_fields:
           error_text = "⚠ Не заполнены обязательные поля: " + ", ".join(missing_fields)
           self.save_status_label.config(text=error_text, fg="red")
           return

       # Обработка пустых значений Роста и Веса (записываем 0)
       height = data.get('Рост (см)')
       data['Рост (см)'] = int(height) if height.strip() != "" else 0

       weight = data.get('Вес (кг)')
       data['Вес (кг)'] = int(weight) if weight.strip() != "" else 0

       db = DatabaseConnection(DB_CONFIG)
       
       query_donor = """
           INSERT INTO donors (
               sex, birth_date, blood_group, rh_factor,
               children, height, weight,
               nationality, hair_color, hair_type,
               eye_shape, eye_color, nose_shape,
               face_shape, forehead_shape,
               body_type, clothing_size, shoe_size,
               education, profession,
               stigma
           ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
           RETURNING id;
       """
       
       params_donor = (
           data['Пол (М/Ж)'], data['Дата рождения (ГГГГ-ММ-ДД)'], data['Группа крови'], data['Резус-фактор'],
           data['Дети (Да/Нет)'], data['Рост (см)'], data['Вес (кг)'],
           data['Национальность'], data['Цвет волос'], data['Волосы (тип)'],
           data['Разрез глаз'], data['Цвет глаз'], data['Нос (форма)'],
           data['Овал лица'], data['Лоб'],
           data['Телосложение'], data['Размер одежды'], data['Размер обуви'],
           data['Образование'], data['Профессия'],
           data['Наличие стигм (Да/Нет)']
       )
       
       result = db.execute_query(query_donor, params_donor)

       if result and len(result) > 0:
           self.donor_id = result[0][0]
           self.save_status_label.config(text=f"Данные донора сохранены. ID: {self.donor_id}", fg="green")
           
           # Активируем вторую вкладку для ввода биоматериала
           self.tab_control.add(self.bio_tab, text='Данные биоматериала')
           self.tab_control.select(1)
           
           # Очищаем статусное поле при успешном переходе
           self.save_status_label.config(text="")
           
       else:
           self.save_status_label.config(text="Ошибка при сохранении данных донора.", fg="red")


    def save_biological_material(self):
       """Сохраняет данные биоматериала в БД."""
       if not self.donor_id:
           self.bio_status_label.config(text="❌ Ошибка: сначала необходимо сохранить данные донора.", fg="red")
           return

       data = {field: var.get() for field, var in self.bio_entries.items()}

       # Проверка обязательных полей биоматериала с выводом под кнопкой
       required_fields = ['Наименование биоматериала', 'Дата получения (ГГГГ-ММ-ДД)', 'Срок годности (ГГГГ-ММ-ДД)', 'Количество материала']
       missing_fields = [field for field in required_fields if not data.get(field)]

       if missing_fields:
           error_text = "⚠ Не заполнены обязательные поля биоматериала: " + ", ".join(missing_fields)
           self.bio_status_label.config(text=error_text, fg="red")
           return

       # Валидация количества материала (должно быть числом)
       try:
           quantity = float(data['Количество материала'])
       except ValueError:
           self.bio_status_label.config(text="❌ Ошибка: 'Количество материала' должно быть числом.", fg="red")
           return

       db = DatabaseConnection(DB_CONFIG)
       
       query_bio = """
           INSERT INTO biological_materials (
               id_donor, name_bio,
               date_i, date_end,
               material_type,
               quantity,
               unit,
               genetic_passport
           ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s);
       """
       
       params_bio = (
           self.donor_id,
           data['Наименование биоматериала'],
           data['Дата получения (ГГГГ-ММ-ДД)'],
           data['Срок годности (ГГГГ-ММ-ДД)'],
           data['Тип материала'],
           quantity,
           data['Единицы измерения'],
           True if self.bio_genetic_passport_var.get() else False
       )
       
       success = db.execute_update(query_bio, params_bio)

       if success:
           self.bio_status_label.config(text="✅ Данные биоматериала успешно сохранены!", fg="green")
           
           # Небольшая задержка перед закрытием окна для прочтения сообщения
           self.after(1500, self.destroy) 
           
       else:
          self.bio_status_label.config(text="❌ Не удалось сохранить данные в базу данных.", fg="red")

class SearchWindow(tk.Toplevel):
    """Окно для поиска доноров по различным критериям."""
    def __init__(self):
        super().__init__()
        self.title("Поиск доноров")
        self.geometry("850x600")

        # 1. Инициализация всех переменных StringVar в самом начале
        self.search_group_blood = tk.StringVar()
        self.search_rh_factor = tk.StringVar()
        self.search_eye_color = tk.StringVar()
        self.search_nationality = tk.StringVar()
        self.search_profession = tk.StringVar()

        # 2. Словарь конфигурации для полей поиска
        # Это заменяет сложную логику if/else и делает код надежнее
        search_fields_config = {
            "Группа крови:": {
                "var": self.search_group_blood,
                "type": "combobox",
                "values": ['O(I)', 'A(II)', 'B(III)', 'AB(IV)']
            },
            "Резус-фактор:": {
                "var": self.search_rh_factor,
                "type": "combobox",
                "values": ['+', '-']
            },
            "Цвет глаз:": {
                "var": self.search_eye_color,
                "type": "entry",
                "width": 20
            },
            "Национальность:": {
                "var": self.search_nationality,
                "type": "entry",
                "width": 20
            },
            "Профессия:": {
                "var": self.search_profession,
                "type": "entry",
                "width": 20
            }
        }

        # --- Блок создания виджетов для ввода критериев ---
        search_frame_top = tk.Frame(self)
        search_frame_top.pack(pady=10)
        
        row_search_count = 0
        for label_text, config in search_fields_config.items():
            # Создаем Label
            tk.Label(search_frame_top, text=label_text).grid(
                row=(row_search_count//3)*2 + 1,
                column=(row_search_count%3)*2,
                sticky="e", padx=5, pady=2
            )
            
            # Создаем виджет (Combobox или Entry) на основе конфигурации
            if config["type"] == "combobox":
                widget = ttk.Combobox(
                    search_frame_top,
                    textvariable=config["var"],
                    values=config["values"],
                    state='readonly',
                    width=config.get("width", 15)
                )
            else:
                widget = tk.Entry(
                    search_frame_top,
                    textvariable=config["var"],
                    width=config["width"]
                )
                
            widget.grid(
                row=(row_search_count//3)*2 + 1,
                column=(row_search_count%3)*2 + 1,
                sticky="w", padx=5, pady=2
            )
            row_search_count += 1

        # Кнопка "Найти"
        ttk.Button(search_frame_top,
                  text="Найти",
                  command=self.perform_search).grid(row=3, column=0, columnspan=3, pady=10)

        # --- Блок создания таблицы результатов ---
        columns = ("id", "Пол", "Дата рождения", "Группа крови", "Резус",
                   "Цвет глаз", "Национальность", "Профессия")
        
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.tree.heading(col, text=col.capitalize().replace('_', ' '))
            self.tree.column(col, minwidth=0, width=100, stretch=False)
            
        self.tree.column("id", width=30)
        self.tree.pack(padx=10, pady=10, fill='both', expand=True)

        # --- Блок кнопок действий ---
        btn_frame_bottom = tk.Frame(self)
        btn_frame_bottom.pack(pady=5)

        ttk.Button(btn_frame_bottom,
                  text="Добавить биоматериал для выбранного донора",
                  command=self.add_bio_for_selected).pack(side='left', padx=5)

        ttk.Button(btn_frame_bottom,
                  text="Закрыть",
                  command=self.destroy).pack(side='right', padx=5)


    def perform_search(self):
        """Выполняет поиск доноров в БД по заданным критериям."""
        conditions = []
        params = []

        # Сбор условий для запроса WHERE из заполненных полей
        if self.search_group_blood.get():
            conditions.append("blood_group = %s")
            params.append(self.search_group_blood.get())

        if self.search_rh_factor.get():
            conditions.append("rh_factor = %s")
            params.append(self.search_rh_factor.get())

        if self.search_eye_color.get():
            conditions.append("eye_color ILIKE %s")
            params.append(f"%{self.search_eye_color.get()}%")

        if self.search_nationality.get():
            conditions.append("nationality ILIKE %s")
            params.append(f"%{self.search_nationality.get()}%")

        if self.search_profession.get():
            conditions.append("profession ILIKE %s")
            params.append(f"%{self.search_profession.get()}%")

        query = """
            SELECT id, sex, birth_date, blood_group, rh_factor, eye_color, nationality, profession 
            FROM donors
        """
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        db = DatabaseConnection(DB_CONFIG)
        
        try:
            result = db.execute_query(query, params)
            
            # Очистка таблицы перед вставкой новых данных
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Заполнение таблицы результатами поиска
            for row in result:
                self.tree.insert("", "end", values=row)

            if not result:
                messagebox.showinfo("Результат", "Доноры по заданным критериям не найдены.")

        except Exception as e:
            messagebox.showerror("Ошибка поиска", str(e))
            
    def add_bio_for_selected(self):
       """
       Открывает окно добавления биоматериала для донора,
       выбранного в таблице результатов поиска.
       """
       selected_item = self.tree.selection()
       
       if not selected_item:
           messagebox.showwarning("Предупреждение", "Пожалуйста, выберите донора из списка.")
           return

       # Получаем ID донора из первого столбца таблицы (индекс 'id' или позиция 0 в values)
       donor_id = self.tree.item(selected_item[0])['values'][0]
       
       # Открываем окно добавления биоматериала, передавая ID донора
       AddBioWindow(donor_id)       

class AddBioWindow(tk.Toplevel):
    """Окно для добавления биоматериала к существующему донору."""
    def __init__(self, donor_id):
        super().__init__()
        self.title(f"Добавление биоматериала для донора ID: {donor_id}")
        self.geometry("650x350")
        
        # Сохраняем ID донора как атрибут класса
        self.donor_id = donor_id 

        # --- Поля биоматериала ---
        self.bio_entries = {} # Словарь для хранения переменных полей

        fields_bio = {
            "Наименование биоматериала": ("entry", 40),
            "Дата получения (ГГГГ-ММ-ДД)": ("entry", 10),
            "Срок годности (ГГГГ-ММ-ДД)": ("entry", 10),
            "Тип материала": ("entry", 30),
            "Количество материала": ("entry", 10),
            "Единицы измерения": ("entry", 10),
        }

        row_count = 0
        for label_text, (widget_type, params) in fields_bio.items():
            tk.Label(self, text=label_text).grid(row=row_count, column=0, sticky="e", padx=5, pady=2)
            
            if widget_type == "entry":
                entry_var = tk.StringVar()
                entry = tk.Entry(self, textvariable=entry_var, width=params)
                
                # Добавляем маску для полей даты
                if "Дата" in label_text:
                    entry.bind('<KeyRelease>', self.on_date_input)
                    
                entry.grid(row=row_count, column=1, sticky="w", padx=5, pady=2)
                self.bio_entries[label_text] = entry_var
                
            row_count += 1

        # Флаг генетического паспорта
        tk.Label(self, text="Генетический паспорт").grid(row=row_count, column=0, sticky="e", padx=5, pady=10)
        self.bio_genetic_passport_var = tk.BooleanVar()
        ttk.Checkbutton(self, variable=self.bio_genetic_passport_var).grid(row=row_count, column=1, sticky="w")
        
        row_count += 1

        # --- ФИКС: Используем новый метод save_and_close ---
        ttk.Button(self,
                  text="Сохранить биоматериал и закрыть окно",
                  command=self.save_and_close).grid(row=row_count, column=0, columnspan=2, pady=15)
         
    def on_date_input(self, event):
        """Форматирует ввод в поле даты по маске ГГГГ-ММ-ДД."""
        widget = event.widget
        current_text = widget.get()
        digits = ''.join(filter(str.isdigit, current_text))
        
        new_text = ""
        if len(digits) > 4:
            new_text = f"{digits[:4]}-{digits[4:6]}"
            if len(digits) > 6:
                new_text += f"-{digits[6:8]}"
        elif len(digits) > 0:
            new_text = digits[:4]

        new_text = new_text[:10]

        if current_text != new_text:
            widget.delete(0, tk.END)
            widget.insert(0, new_text)

        cursor_pos = widget.index(tk.INSERT)
        if cursor_pos < len(new_text) and new_text[cursor_pos] == '-':
            widget.icursor(cursor_pos + 1)
            
    def save_and_close(self):
       """Сохраняет данные биоматериала в БД и закрывает окно."""
       data = {field: var.get() for field, var in self.bio_entries.items()}

       required_fields = ['Наименование биоматериала', 'Дата получения (ГГГГ-ММ-ДД)', 'Срок годности (ГГГГ-ММ-ДД)', 'Количество материала']
       for field in required_fields:
           if not data.get(field):
               messagebox.showerror("Ошибка заполнения", f"Поле '{field}' обязательно для заполнения.")
               return

       db = DatabaseConnection(DB_CONFIG)
       
       query_bio = """
           INSERT INTO biological_materials (
               id_donor, name_bio,
               date_i, date_end,
               material_type,
               quantity,
               unit,
               material_status,
               genetic_passport
           ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s);
       """
       
       params_bio = (
           self.donor_id,
           data['Наименование биоматериала'],
           data['Дата получения (ГГГГ-ММ-ДД)'],
           data['Срок годности (ГГГГ-ММ-ДД)'],
           data['Тип материала'],
           float(data['Количество материала']),
           data['Единицы измерения'],
           True if self.bio_genetic_passport_var.get() else False
       )
       
       success = db.execute_update(query_bio, params_bio)

       if success:
           messagebox.showinfo("Успех", "Данные биоматериала успешно сохранены!")
           self.destroy()

if __name__ == "__main__":
    app = AuthWindow()
    app.mainloop()