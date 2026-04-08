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
            
            messagebox.showerror("Ошибка БД", str(e),parent=self)
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
            messagebox.showerror("Ошибка БД", str(e),parent=self)
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
           messagebox.showwarning("Ошибка", "Заполните все поля",parent=self)
           return

       password_hash = hashlib.sha256(password.encode()).hexdigest()
    
       db = DatabaseConnection(DB_CONFIG)
    
       result = db.execute_query(
           "SELECT id, login FROM users WHERE login = %s AND passwordhash = %s",
           (login, password_hash)
       )

       if result is None:
           messagebox.showerror("Ошибка", "Не удалось выполнить запрос к базе данных.",parent=self)
    
       elif not result: 
           messagebox.showerror("Ошибка", "Неверный логин или пароль",parent=self)
    
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
            "Национальность": ("combobox", ('Русский', 'Украинец','Белорус')),
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
       required_fields = ['Наименование биоматериала', 'Дата получения (ГГГГ-ММ-ДД)', 'Срок годности (ГГГГ-ММ-ДД)', 'Количество материала','Единицы измерения']
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
    """Окно для поиска доноров по всем полям таблицы."""
    def __init__(self):
        super().__init__()
        self.title("Поиск доноров")
        self.geometry("1200x800")
        self.resizable(True, True)

        # --- 1. Словарь для сопоставления имен колонок БД и отображаемых имен ---
        self.column_map = {
            "id": "ID",
            "sex": "Пол",
            "birth_date": "Дата рождения",
            "blood_group": "Группа крови",
            "rh_factor": "Резус-фактор",
            "children": "Дети",
            "height": "Рост (см)",
            "weight": "Вес (кг)",
            "nationality": "Национальность",
            "hair_color": "Цвет волос",
            "hair_type": "Тип волос",
            "eye_shape": "Разрез глаз",
            "eye_color": "Цвет глаз",
            "nose_shape": "Форма носа",
            "face_shape": "Овал лица",
            "forehead_shape": "Лоб",
            "body_type": "Телосложение",
            "clothing_size": "Размер одежды",
            "shoe_size": "Размер обуви",
            "education": "Образование",
            "profession": "Профессия",
            "stigma": "Наличие стигм"
        }

        # --- 2. ВОССТАНОВЛЕННЫЙ СЛОВАРЬ ЗНАЧЕНИЙ ДЛЯ COMBOBOX ---
        self.combobox_values = {
            "sex": ('М', 'Ж'),
            "blood_group": ('O(I)', 'A(II)', 'B(III)', 'AB(IV)'),
            "rh_factor": ('+', '-'),
            "children": ('Да', 'Нет'),
            "hair_color": ('Блондин', 'Брюнет', 'Шатен'),
            "hair_type": ('Прямые', 'Вьющиеся'),
            "eye_shape": ('Прямой', 'Раскосый'),
            "nationality": ('Русский', 'Украинец','Белорус'),
            # Исправленные дубликаты для корректной работы словаря
            "eye_color": ('Зеленые', 'Серные'),
            "nose_shape": ('Прямые', 'Вьющиеся'),
            "face_shape": ('Круглое', 'Полное'),
            "forehead_shape": ('Широкий', 'Узкий'),
            "body_type": ('Нормальное', 'Рахитическое'),
            "education": ('Высшее', 'Среднее'),
            "stigma": ('Да', 'Нет'),
        }

        # --- 3. Инициализация переменных для критериев поиска ---
        self.search_vars = {db_col: tk.StringVar() for db_col in self.column_map.keys()}
        
        # --- НОВЫЕ ПЕРЕМЕННЫЕ ДЛЯ ПОИСКА ПО МАТЕРИАЛУ ---
        self.search_vars['name_bio'] = tk.StringVar() # Наименование материала
        self.search_vars['material_type'] = tk.StringVar() # Тип материала

        # --- Блок интерфейса: Критерии поиска ---
        search_frame = tk.LabelFrame(self, text="Критерии поиска", padx=10, pady=10)
        search_frame.pack(pady=10, fill='x', padx=10)

        row_count = 0
        col_count = 0
        max_columns = 3

        # --- ОСТАЛЬНЫЕ ПОЛЯ ДОНОРА С ЛОГИКОЙ ВСТАВКИ ---
        for db_col, display_name in self.column_map.items():
            
             if col_count >= max_columns:
                 row_count += 1
                 col_count = 0

             tk.Label(search_frame, text=f"{display_name}:").grid(
                 row=row_count, column=col_count*2, sticky="e", padx=(0, 5), pady=2
             )
             
             # Создание виджета: Combobox или Entry
             if db_col in self.combobox_values:
                 widget = ttk.Combobox(
                     search_frame,
                     textvariable=self.search_vars[db_col],
                     values=self.combobox_values[db_col],
                     state='readonly',
                     width=25
                 )
                 self.search_vars[db_col].set('') 
                 
             elif db_col == "birth_date":
                 widget = tk.Entry(search_frame, textvariable=self.search_vars[db_col], width=25)
                 widget.bind('<KeyRelease>', self.on_date_input)
             
             else:
                 widget = tk.Entry(search_frame, textvariable=self.search_vars[db_col], width=25)

             widget.grid(row=row_count, column=col_count*2 + 1, sticky="w", padx=(5, 10), pady=2)
            
             # --- ЛОГИКА ВСТАВКИ НОВЫХ ПОЛЕЙ ПОСЛЕ 'stigma' ---
             if db_col == 'stigma':
                 
                 col_count += 1

                 if col_count < max_columns - 1:
                     
                     tk.Label(search_frame, text="Наименование материала:").grid(
                         row=row_count, column=col_count*2, sticky="e", padx=(20, 5), pady=2
                     )
                     widget_bio_name = ttk.Combobox(search_frame, textvariable=self.search_vars['name_bio'],values=("cперма","ооцит","эмбрион"), state='readonly', width=25)
                     widget_bio_name.grid(row=row_count, column=col_count*2 + 1, sticky="w", padx=(5, 10), pady=2)
                     
                     col_count += 1

                     tk.Label(search_frame, text="Тип материала:").grid(
                         row=row_count, column=col_count*2, sticky="e", padx=(20, 5), pady=2
                     )
                     widget_bio_type = ttk.Combobox(search_frame, textvariable=self.search_vars['material_type'],values=("крио","нативный"), state='readonly', width=25)
                     widget_bio_type.grid(row=row_count, column=col_count*2 + 1, sticky="w", padx=(5, 10), pady=2)
             
             col_count += 1

        # --- Кнопки управления поиском на одной строке ---
        button_frame = tk.Frame(search_frame)
        button_frame.grid(row=row_count + 1, column=0, columnspan=max_columns*2, pady=(15, 2), sticky="we")
        
        ttk.Button(button_frame, text="Найти", command=self.perform_search).pack(side='left', padx=(0, 10))
        ttk.Button(button_frame, text="Сброс", command=self.reset_search).pack(side='left')
        
         # Статусная метка (на новой строке)
        self.search_status_label = tk.Label(search_frame, text="", fg="grey")
        self.search_status_label.grid(row=row_count + 2, column=0, columnspan=max_columns*2, pady=(5, 10), sticky="we")

        # --- Блок интерфейса: Таблица результатов ---
        self.columns_db = list(self.column_map.keys())
        
         # Для отображения заголовков используем человекочитаемые имена
        self.columns_display = list(self.column_map.values())

        table_frame = tk.Frame(self)
        table_frame.pack(fill='both', expand=True, padx=10, pady=5)

        self.tree = ttk.Treeview(table_frame, columns=self.columns_db, show="headings")
         
         # Настройка колонок и заголовков (используем display имена)
        for i, col_db in enumerate(self.columns_db):
             display_name = self.columns_display[i]
             self.tree.heading(col_db, text=display_name)
             
             # Задаем начальные ширины колонок
             if col_db == 'id':
                 self.tree.column(col_db, width=40, anchor='center')
             elif col_db in ['sex', 'blood_group', 'rh_factor', 'children', 'stigma']:
                 self.tree.column(col_db, width=90, anchor='center')
             elif col_db in ['height', 'weight', 'shoe_size']:
                 self.tree.column(col_db, width=70, anchor='center')
             else:
                 self.tree.column(col_db, width=130) 
         
         # Настройка скроллбаров
        yscrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        xscrollbar = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscroll=yscrollbar.set, xscroll=xscrollbar.set)
         
         # Размещение с помощью grid для гибкости
        self.tree.grid(row=0, column=0, columnspan=2, sticky="nsew")
        xscrollbar.grid(row=1, column=0, columnspan=2, sticky="ew")
        yscrollbar.grid(row=0, column=2, sticky="ns")
         
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=5)
        
        ttk.Button(btn_frame,
                   text="Удалить выбранного донора",
                   command=self.delete_selected_donor).pack(side='left', padx=5)

        ttk.Button(btn_frame,
                   text="Добавить биоматериал для выбранного донора",
                   command=self.add_bio_for_selected).pack(side='left', padx=5)

        ttk.Button(btn_frame,
                   text="Закрыть",
                   command=self.destroy).pack(side='right', padx=5)

        self.tree.bind("<Double-1>", self.on_donor_double_click)

    def on_date_input(self, event):
       """
       Форматирует ввод в поле даты по маске ГГГГ-ММ-ДД.
       """
       widget = event.widget
       current_text = widget.get()

       digits = ''.join(filter(str.isdigit, current_text))
       
       new_text = ""
       if len(digits) > 4:
           new_text = f"{digits[:4]}-"
           if len(digits) > 6:
               new_text += f"{digits[4:6]}-{digits[6:8]}"
           else:
               new_text += f"{digits[4:6]}"
       elif len(digits) > 0:
           new_text = digits[:4]

       new_text = new_text[:10]

       if current_text != new_text:
           widget.delete(0, tk.END)
           widget.insert(0, new_text)

       cursor_pos = widget.index(tk.INSERT)
       if cursor_pos < len(new_text):
           next_char = new_text[cursor_pos] if cursor_pos < len(new_text) else None
           if next_char == '-':
               widget.icursor(cursor_pos + 1)
           elif cursor_pos == 4 and len(new_text) > 5:
               widget.icursor(5)
           elif cursor_pos == 7 and len(new_text) > 8:
               widget.icursor(8)


    def reset_search(self):
        """
        Сбрасывает все критерии поиска к значениям по умолчанию.
        Очищает таблицу результатов и скрывает статусные сообщения.
        """
        for field_var in self.search_vars.values():
             field_var.set("")
 
        self.tree.delete(*self.tree.get_children())
 
        self.search_status_label.grid_remove()


    def perform_search(self):
       """Выполняет поиск доноров в БД по всем заданным критериям."""
       
       has_donor_filters = any(self.search_vars[col].get().strip() for col in self.column_map.keys())
       has_material_filters = any([
           self.search_vars['name_bio'].get().strip(),
           self.search_vars['material_type'].get().strip()
       ])
       
       select_cols = ", ".join([f"d.{col}" for col in self.columns_db])
       from_table = "donors d"
       
       conditions = []
       material_conditions = []
       params = []
       
       if has_donor_filters:
           for db_col in self.columns_db:
               raw_value = self.search_vars[db_col].get().strip()
               if not raw_value:
                   continue

               if db_col in ["children", "stigma"]:
                   value_for_db = raw_value == 'Да'
                   conditions.append(f"d.{db_col} = %s")
                   params.append(value_for_db)
               else:
                   if db_col in ["nationality", "hair_color", "eye_color", "nose_shape", "face_shape", 
                               "forehead_shape", "body_type", "clothing_size", "shoe_size", 
                               "education", "profession"]:
                       conditions.append(f"d.{db_col} ILIKE %s")
                       params.append(f"%{raw_value}%")
                   else:
                       conditions.append(f"d.{db_col} = %s")
                       params.append(raw_value)
       
       name_bio = self.search_vars['name_bio'].get().strip()
       material_type_val = self.search_vars['material_type'].get().strip()
       
       if name_bio:
           material_conditions.append("m.name_bio ILIKE %s")
           params.append(f"%{name_bio}%")
           
       if material_type_val:
           material_conditions.append("m.material_type ILIKE %s")
           params.append(f"%{material_type_val}%")
       
       
       query = f"SELECT DISTINCT {select_cols} FROM {from_table}"
       
       all_conditions = conditions + material_conditions

       if has_material_filters:
           query += " JOIN biological_materials m ON d.id = m.id_donor"
           
           if all_conditions:
               query += f" WHERE {' AND '.join(all_conditions)}"
       
       elif has_donor_filters and conditions:
           query += f" WHERE {' AND '.join(conditions)}"
       
       db = DatabaseConnection(DB_CONFIG)
       
       try:
           result = db.execute_query(query, params)
           
           self.tree.delete(*self.tree.get_children())
           
           for row in result:
               self.tree.insert("", "end", values=row)

           if result:  # Если список не пустой
               first_item = self.tree.get_children()[0]
               self.tree.selection_set(first_item) # Выделяем строку
               self.tree.focus(first_item)         # Устанавливаем фокус

           if not result:
               self.search_status_label.config(text="Доноры по заданным критериям не найдены.", fg="red")
               self.search_status_label.grid()
           else:
               self.search_status_label.grid_remove()
               
       except Exception as e:
           messagebox.showerror("Ошибка поиска", str(e),parent=self)


    def add_bio_for_selected(self):
      """
      Открывает окно добавления биоматериала для донора,
      выбранного в таблице результатов поиска.
      """
      selected_item = self.tree.selection()
      
      if not selected_item:
          messagebox.showwarning("Предупреждение", "Пожалуйста, выберите донора из списка.",parent=self)
          return

      donor_id = self.tree.item(selected_item[0])['values'][0]
      
      AddBioWindow(donor_id)

    def on_donor_double_click(self, event):
       """Открывает окно с деталями донора при двойном щелчке по строке."""
       selected_item = self.tree.selection()
       if not selected_item:
            return # Ничего не выбрано

       # Получаем ID донора из первой колонки (индекс 0)
       donor_id = self.tree.item(selected_item[0])['values'][0]
        
       # Открываем новое окно для редактирования
       DonorDetailsWindow(donor_id)

    def delete_selected_donor(self):
        """
        Удаляет донора, выбранного в таблице результатов поиска,
        вместе со всеми его связанными биоматериалами.
        """
        selected_item = self.tree.selection()
        
        if not selected_item:
            messagebox.showwarning("Предупреждение", "Пожалуйста, выберите донора из списка.", parent=self)
            return

        # Получаем ID донора и его ФИО (или логин) для отображения в диалоге
        donor_values = self.tree.item(selected_item[0])['values']
        donor_id = donor_values[0]
        
        # Попытка получить ФИО или логин для наглядности (если есть в таблице)
        # В вашем текущем коде отображается только ID. Если хотите ФИО, нужно изменить SQL-запрос в perform_search.
        donor_info = f"ID: {donor_id}"

        # Запрос подтверждения перед удалением
        confirm = messagebox.askyesno(
            "Подтверждение удаления",
            f"Вы уверены, что хотите удалить донора {donor_info}?\n"
            "Все связанные с ним биоматериалы также будут безвозвратно удалены.",
            parent=self
        )
        
        if not confirm:
            return # Пользователь отменил операцию

        db = DatabaseConnection(DB_CONFIG)
        
        try:
            # Использование ON DELETE CASCADE в БД — самый надежный способ.
            # Если каскадное удаление настроено на уровне БД, достаточно одной команды.
            # Если нет — нужно удалять из двух таблиц по очереди.
            
            # Вариант 1: Если в БД настроено ON DELETE CASCADE для foreign key:
            success = db.execute_update("DELETE FROM donors WHERE id = %s", (donor_id,))
            
            # Вариант 2: Если каскада нет (менее предпочтительно):
            # db.execute_update("DELETE FROM biological_materials WHERE id_donor = %s", (donor_id,))
            # success = db.execute_update("DELETE FROM donors WHERE id = %s", (donor_id,))

            if success:
                messagebox.showinfo("Успех", f"Донор {donor_info} и его материалы удалены.", parent=self)
                # Обновляем таблицу после удаления
                self.perform_search()
            else:
                messagebox.showerror("Ошибка", "Не удалось удалить данные.", parent=self)

        except Exception as e:
            messagebox.showerror("Ошибка БД", str(e), parent=self)  

class AddBioWindow(tk.Toplevel):
    """Окно для добавления биоматериала к существующему донору."""
    def __init__(self, donor_id):
        super().__init__()
        self.title(f"Добавление биоматериала для донора ID: {donor_id}")
        self.geometry("650x400")  # Увеличена высота для статусного сообщения
        
        self.donor_id = donor_id 

        # --- Словари значений для Combobox ---
        self.bio_types = ("сперма", "ооцит", "эмбрион")
        self.material_types = ("крио", "нативный")
        self.units = ("ед", "мл")

        # --- Инициализация Notebook (Вкладок) ---
        # Создаем блокнот и вкладку сразу, так как донор уже существует
        self.tab_control = ttk.Notebook(self)
        self.bio_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.bio_tab, text='Данные биоматериала')

        # --- Поля биоматериала ---
        # Словарь для хранения переменных полей
        self.bio_entries = {}

        fields_bio = {
            "Наименование биоматериала": ("combobox", self.bio_types),
            "Дата получения (ГГГГ-ММ-ДД)": ("entry", 10),
            "Срок годности (ГГГГ-ММ-ДД)": ("entry", 10),
            "Тип материала": ("combobox", self.material_types),
            "Количество материала": ("entry", 10),
            "Единицы измерения": ("combobox", self.units),
        }

        row_count = 0
        for label_text, (widget_type, params) in fields_bio.items():
            tk.Label(self.bio_tab, text=label_text).grid(row=row_count, column=0, sticky="e", padx=5, pady=2)
            
            if widget_type == "entry":
                entry_var = tk.StringVar()
                entry = tk.Entry(self.bio_tab, textvariable=entry_var, width=params)
                # Привязываем маску для дат
                if "Дата" in label_text or "Срок" in label_text:
                    entry.bind('<KeyRelease>', self.on_date_input)
                entry.grid(row=row_count, column=1, sticky="w", padx=5, pady=2)
                self.bio_entries[label_text] = entry_var
                
            elif widget_type == "combobox":
                combo_var = tk.StringVar()
                combo = ttk.Combobox(self.bio_tab, textvariable=combo_var, values=params, state='readonly')
                combo.grid(row=row_count, column=1, sticky="w", padx=5, pady=2)
                self.bio_entries[label_text] = combo_var
                
            row_count += 1

        # Флаг генетического паспорта
        tk.Label(self.bio_tab, text="Генетический паспорт").grid(row=row_count, column=0, sticky="e", padx=5, pady=10)
        self.bio_genetic_passport_var = tk.BooleanVar()
        ttk.Checkbutton(self.bio_tab, variable=self.bio_genetic_passport_var).grid(row=row_count, column=1, sticky="w")
        
        row_count += 1

        # --- Статусное поле для вывода сообщений ---
        self.save_status_label = tk.Label(self.bio_tab, text="", fg="black", justify='left')
        self.save_status_label.grid(row=row_count, column=0, columnspan=2, pady=(10, 0), sticky="w")
        
        # --- Кнопка сохранения ---
        ttk.Button(self.bio_tab,
                  text="Сохранить биоматериал",
                  command=self.save_and_close).grid(row=row_count + 1, column=0, columnspan=2, pady=(5, 20))
        
        # Размещаем Notebook в окне после добавления всех элементов
        self.tab_control.pack(expand=True, fill='both')

    def on_date_input(self, event):
       """Форматирует ввод в поле даты по маске ГГГГ-ММ-ДД."""
       widget = event.widget
       current_text = widget.get()
       digits = ''.join(filter(str.isdigit, current_text))
       
       new_text = ""
       if len(digits) > 4:
           new_text = f"{digits[:4]}-"
           if len(digits) > 6:
               new_text += f"{digits[4:6]}-{digits[6:8]}"
           else:
               new_text += f"{digits[4:6]}"
       elif len(digits) > 0:
           new_text = digits[:4]

       new_text = new_text[:10]

       if current_text != new_text:
           widget.delete(0, tk.END)
           widget.insert(0, new_text)

       cursor_pos = widget.index(tk.INSERT)
       if cursor_pos < len(new_text):
           next_char = new_text[cursor_pos] if cursor_pos < len(new_text) else None
           if next_char == '-':
               widget.icursor(cursor_pos + 1)
           elif cursor_pos == 4 and len(new_text) > 5:
               widget.icursor(5)
           elif cursor_pos == 7 and len(new_text) > 8:
               widget.icursor(8)
            
    def save_and_close(self):
       """Сохраняет данные биоматериала в БД и закрывает окно."""
       # Очистка статуса перед началом операции
       self.save_status_label.config(text="", fg="black")

       # Сбор данных из виджетов
       data = {field: var.get() for field, var in self.bio_entries.items()}
       data['date_i'] = data.get('Дата получения (ГГГГ-ММ-ДД)', '')
       data['date_end'] = data.get('Срок годности (ГГГГ-ММ-ДД)', '')
       data['quantity'] = data.get('Количество материала', '')
       data['units'] = data.get('Единицы измерения', '')

       # Проверка обязательных полей
       required_fields = {
           'Наименование биоматериала': data.get('Наименование биоматериала'),
           'Дата получения (ГГГГ-ММ-ДД)': data['date_i'],
           'Срок годности (ГГГГ-ММ-ДД)': data['date_end'],
           'Количество материала': data['quantity'],
           'Единицы измерения': data['units']
       }
       
       missing_fields = [field for field, value in required_fields.items() if not value.strip()]
       
       if missing_fields:
           error_text = "⚠ Не заполнены обязательные поля: " + ", ".join(missing_fields)
           self.save_status_label.config(text=error_text, fg="red")
           return

       # Валидация количества материала (должно быть числом)
       try:
           quantity = float(data['quantity'])
           if quantity <= 0:
               raise ValueError("Количество должно быть больше нуля.")
       except ValueError:
           self.save_status_label.config(text="❌ Ошибка: 'Количество материала' должно быть положительным числом.", fg="red")
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
           data['date_i'],
           data['date_end'],
           data['Тип материала'],
           float(data['quantity']),
           data['Единицы измерения'],
           True if self.bio_genetic_passport_var.get() else False
       )
       
       try:
           success = db.execute_update(query_bio, params_bio)
           
           if success:
               self.save_status_label.config(text="✅ Данные успешно сохранены!", fg="green")
               
               # --- Обновляем список в родительском окне ---
               if hasattr(self, 'parent') and hasattr(self.parent, 'load_biological_materials'):
                  self.parent.load_biological_materials()

               # Закрываем окно через 1.5 секунды после успешного сохранения
               self.after(1500, self.destroy)
               
       except Exception as e:
           # Обработка непредвиденных ошибок БД (например, потеря соединения)
           self.save_status_label.config(text=f"❌ Критическая ошибка: {str(e)}", fg="red")

class EditBioWindow(tk.Toplevel):
    """Окно для редактирования существующего биоматериала."""
    def __init__(self, donor_id, bio_id):
        super().__init__()
        self.donor_id = donor_id
        self.bio_id = bio_id
        
        self.title(f"Редактирование биоматериала ID: {bio_id}")
        self.geometry("650x350")
        
        db = DatabaseConnection(DB_CONFIG)
        
        # Загружаем текущие данные материала
        result = db.execute_query(
            """SELECT name_bio, date_i, date_end, material_type,
                  quantity, unit, genetic_passport 
              FROM biological_materials 
              WHERE id = %s""",
            (self.bio_id,)
        )
        
        if not result:
            messagebox.showerror("Ошибка", "Биоматериал не найден.",parent=self)
            self.destroy()
            return
            
        current_data = result[0]

        # --- Инициализация переменных ---
        self.name_bio_var = tk.StringVar()
        self.date_i_var = tk.StringVar()
        self.date_end_var = tk.StringVar()
        self.material_type_var = tk.StringVar()
        self.quantity_var = tk.StringVar()
        self.unit_var = tk.StringVar()
        self.genetic_passport_var = tk.BooleanVar()

        # Списки значений для Combobox
        self.bio_types = ("сперма", "ооцит", "эмбрион")
        self.material_types = ("крио", "нативный")
        self.units = ("ед", "мл")

        # --- Создание интерфейса ---
        # Фрейм для полей ввода (левая часть окна)
        form_frame = tk.Frame(self)
        form_frame.pack(padx=10, pady=10, fill='x')

        row_count = 0

        # Поля формы (используем grid внутри form_frame)
        tk.Label(form_frame, text="Наименование:").grid(row=row_count, column=0, sticky="e", pady=2)
        ttk.Combobox(form_frame, textvariable=self.name_bio_var,
                    values=self.bio_types, state='readonly', width=30).grid(row=row_count, column=1, sticky="w", pady=2)
        row_count += 1

        tk.Label(form_frame, text="Дата получения:").grid(row=row_count, column=0, sticky="e", pady=2)
        tk.Entry(form_frame, textvariable=self.date_i_var, width=32).grid(row=row_count, column=1, sticky="w", pady=2)
        row_count += 1

        tk.Label(form_frame, text="Срок годности:").grid(row=row_count, column=0, sticky="e", pady=2)
        tk.Entry(form_frame, textvariable=self.date_end_var, width=32).grid(row=row_count, column=1, sticky="w", pady=2)
        row_count += 1

        tk.Label(form_frame, text="Тип материала:").grid(row=row_count, column=0, sticky="e", pady=2)
        ttk.Combobox(form_frame, textvariable=self.material_type_var,
                     values=self.material_types, state='readonly', width=30).grid(row=row_count, column=1, sticky="w", pady=2)
        row_count += 1

        tk.Label(form_frame, text="Количество:").grid(row=row_count, column=0, sticky="e", pady=2)
        tk.Entry(form_frame, textvariable=self.quantity_var, width=32).grid(row=row_count, column=1, sticky="w", pady=2)
        row_count += 1

        tk.Label(form_frame, text="Единицы:").grid(row=row_count, column=0, sticky="e", pady=(2, 10))
        ttk.Combobox(form_frame, textvariable=self.unit_var,
                     values=self.units, state='readonly', width=30).grid(row=row_count, column=1, sticky="w", pady=(2, 10))

         # Привязываем маску для дат после создания виджетов
        for child in form_frame.winfo_children():
             if isinstance(child, tk.Entry):
                 child.bind('<KeyRelease>', self.on_date_input)

         # Фрейм для нижней части (чекбокс, кнопка, статус)
        bottom_frame = tk.Frame(self)
        bottom_frame.pack(padx=10, pady=(0, 10), fill='x')

         # 1. Чекбокс (Генетический паспорт)
        self.genetic_passport_check = ttk.Checkbutton(bottom_frame,
                                                      text="Генетический паспорт",
                                                      variable=self.genetic_passport_var)
        self.genetic_passport_check.pack(anchor='w', pady=(0, 5))

         # 2. Кнопка сохранения
        self.save_button = ttk.Button(bottom_frame,
                   text="Сохранить изменения и закрыть",
                   command=self.save_and_close)
        self.save_button.pack(fill='x', pady=(0, 5))

         # 3. Статусная метка (выводится ПОД кнопкой)
        self.save_status_label = tk.Label(bottom_frame, text="", fg="black")
        self.save_status_label.pack(fill='x')
         
         # Заполнение данных из БД
        self._populate_data(current_data)
    
    def _populate_data(self, data):
        """Заполняет поля окна данными из базы данных."""
        self.name_bio_var.set(data[0])
        self.date_i_var.set(data[1])
        self.date_end_var.set(data[2])
        self.material_type_var.set(data[3])
        
        quantity_val = data[4]
        self.quantity_var.set(str(quantity_val) if quantity_val is not None else "")
         
        self.unit_var.set(data[5])
        
        if data[6]:
            self.genetic_passport_var.set(True)
    
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

    def save_and_close(self):
       """Сохраняет измененные данные биоматериала в БД и закрывает окно."""
       
       # Блокируем кнопку во время сохранения
       self.save_button.config(state='disabled')
       
       # Очистка статуса перед началом операции
       self.save_status_label.config(text="", fg="black")

       # Сбор данных напрямую из переменных (связанных с виджетами)
       name_bio = self.name_bio_var.get()
       date_i = self.date_i_var.get()
       date_end = self.date_end_var.get()
       material_type = self.material_type_var.get()
       quantity_str = self.quantity_var.get()
       unit = self.unit_var.get()

       # Валидация: Проверка на пустые обязательные поля
       required_fields = {
           "Наименование биоматериала": name_bio,
           "Дата получения": date_i,
           "Срок годности": date_end,
           "Количество материала": quantity_str,
           "Единицы измерения":unit
       }
       
       missing_fields = [field for field in required_fields if not field.strip()]
       
       if missing_fields:
           error_text = "⚠ Не заполнены обязательные поля: " + ", ".join(missing_fields)
           self.save_status_label.config(text=error_text, fg="red")
           self.save_button.config(state='normal') # Разблокируем кнопку при ошибке валидации
           return

       # Валидация количества материала (должно быть числом)
       try:
           quantity = float(quantity_str)
           if quantity <= 0:
               raise ValueError("Количество должно быть больше нуля.")
       except ValueError:
           self.save_status_label.config(text="❌ Ошибка: 'Количество' должно быть положительным числом.", fg="red")
           self.save_button.config(state='normal')
           return

       db = DatabaseConnection(DB_CONFIG)
       
       query_bio = """
           UPDATE biological_materials SET
               name_bio=%s,
               date_i=%s,
               date_end=%s,
               material_type=%s,
               quantity=%s,
               unit=%s,
               genetic_passport=%s
           WHERE id=%s;
       """
       
       params_bio = (
           name_bio,
           date_i,
           date_end,
           material_type,
           quantity,
           unit,
           True if self.genetic_passport_var.get() else False,
           self.bio_id
       )
       
       success = db.execute_update(query_bio, params_bio)

       if success:
           self.save_status_label.config(text="✅ Данные успешно обновлены!", fg="green")
           
           # Обновляем таблицу в родительском окне и устанавливаем фокус
           if hasattr(self, 'parent') and hasattr(self.parent, 'load_biological_materials'):
              self.parent.load_biological_materials()

           # Небольшая задержка перед закрытием окна для прочтения сообщения
           self.after(1500, self.destroy) 
           
       else:
          self.save_status_label.config(text="❌ Не удалось сохранить данные в базу данных.", fg="red")
          self.save_button.config(state='normal') # Разблокируем кнопку при ошибке БД
class DonorDetailsWindow(tk.Toplevel):
    """Окно для просмотра и редактирования данных донора и его биоматериалов."""
    def __init__(self, donor_id):
        super().__init__()
        self.donor_id = donor_id
        self.title(f"Детали донора ID: {donor_id}")
        self.geometry("800x700")
        
        # Словарь для хранения переменных полей
        self.entries = {}
        
        # --- Загрузка данных донора ---
        db = DatabaseConnection(DB_CONFIG)
        donor_data = db.execute_query(
            "SELECT * FROM donors WHERE id = %s", 
            (self.donor_id,)
        )
        
        if not donor_data:
            messagebox.showerror("Ошибка", "Донор не найден.",parent=self)
            self.destroy()
            return
            
        donor_data = donor_data[0] # Получаем первую строку результата

        # --- Создание интерфейса ---
        tab_control = ttk.Notebook(self)
        
        # Вкладка 1: Данные донора
        donor_tab = ttk.Frame(tab_control)
        
        # Поля донора
        fields_donor = {
            "Пол (М/Ж)": ("combobox", ('М', 'Ж')),
            "Дата рождения (ГГГГ-ММ-ДД)": ("entry", 10),
            "Группа крови": ("combobox", ('O(I)', 'A(II)', 'B(III)', 'AB(IV)')),
            "Резус-фактор": ("combobox", ('+', '-')),
            "Дети (Да/Нет)": ("combobox", ('Да', 'Нет')),
            "Рост (см)": ("entry", 5),
            "Вес (кг)": ("entry", 5),
            "Национальность": ("combobox", ('Русский', 'Украинец','Белорус')),
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
            
             tk.Label(donor_tab, text=label_text).grid(row=row_count, column=0, sticky="e", padx=5, pady=2)
             
             if widget_type == "entry":
                 entry_var = tk.StringVar()
                 entry = tk.Entry(donor_tab, textvariable=entry_var, width=params)
                 
                 # Добавляем маску для даты рождения
                 if label_text == "Дата рождения (ГГГГ-ММ-ДД)":
                     entry.bind('<KeyRelease>', self.on_date_input)
                     
                 entry.grid(row=row_count, column=1, sticky="w", padx=5, pady=2)
                 self.entries[label_text] = entry_var
                 
             elif widget_type == "combobox":
                 combo_var = tk.StringVar()
                 combo = ttk.Combobox(donor_tab, textvariable=combo_var, values=params, state='readonly')
                 combo.grid(row=row_count, column=1, sticky="w", padx=5, pady=2)
                 self.entries[label_text] = combo_var
                 
             row_count += 1

         # Кнопка сохранения данных донора
        self.save_btn = ttk.Button(donor_tab, text="Сохранить изменения донора", command=self.save_donor_changes)
        self.save_btn.grid(row=row_count, column=0, columnspan=2, pady=15)

         # Статусная метка для вывода результата сохранения
        self.save_status_label = tk.Label(donor_tab, text="", fg="black")
        self.save_status_label.grid(row=row_count + 1, column=0, columnspan=2, pady=(5, 15))
         
        tab_control.add(donor_tab, text='Данные донора')
         
         # --- Вкладка 2: Биоматериалы ---
        bio_tab = ttk.Frame(tab_control)
         
         # Таблица биоматериалов
        bio_columns = ["id_bio", "Наименование", "Дата получения", "Срок годности", "Тип"]
        self.bio_tree = ttk.Treeview(bio_tab, columns=bio_columns, show="headings")
         
        for col in bio_columns:
             self.bio_tree.heading(col, text=col)
             if col == "id_bio":
                 self.bio_tree.column(col, width=40, anchor='center')
             else:
                 self.bio_tree.column(col, width=150)
         
        self.bio_tree.pack(fill='both', expand=True, padx=10, pady=5)
         
         # Кнопки управления биоматериалами
        bio_btn_frame = tk.Frame(bio_tab)
        bio_btn_frame.pack(pady=5)
         
        ttk.Button(bio_btn_frame,
                   text="Добавить биоматериал",
                   command=self.add_new_bio).pack(side='left', padx=5)
                   
        ttk.Button(bio_btn_frame,
                   text="Редактировать биоматериал",
                   command=self.edit_selected_bio).pack(side='left', padx=5)
                   
        ttk.Button(bio_btn_frame,
                   text="Удалить биоматериал",
                   command=self.delete_selected_bio).pack(side='left', padx=5)
                   
        tab_control.add(bio_tab, text='Биоматериалы')
        tab_control.pack(expand=True, fill='both')
         
         # Заполнение полей данными
        self.populate_donor_data(donor_data)
        self.load_biological_materials()

    def populate_donor_data(self, data):
        """Заполняет поля окна данными из базы данных."""
        mapping = {
            "Пол (М/Ж)": data[1],
            "Дата рождения (ГГГГ-ММ-ДД)": data[2],
            "Группа крови": data[3],
            "Резус-фактор": data[4],
            "Дети (Да/Нет)": "Да" if data[5] else "Нет",
            "Рост (см)": str(data[6]) if data[6] != 0 else "",
            "Вес (кг)": str(data[7]) if data[7] != 0 else "",
            "Национальность": data[8],
            "Цвет волос": data[9],
            "Волосы (тип)": data[10],
            "Разрез глаз": data[11],
            "Цвет глаз": data[12],
            "Нос (форма)": data[13],
            "Овал лица": data[14],
            "Лоб": data[15],
            "Телосложение": data[16],
            "Размер одежды": data[17],
            "Размер обуви": data[18],
            "Образование": data[19],
            "Профессия": data[20],
             "Наличие стигм (Да/Нет)": "Да" if data[21] else "Нет"
        }
        
        for field_name, value in mapping.items():
             if field_name in self.entries:
                 self.entries[field_name].set(value)

    def on_date_input(self, event):
       """Форматирует ввод в поле даты по маске ГГГГ-ММ-ДД."""
       widget = event.widget
       current_text = widget.get()
       digits = ''.join(filter(str.isdigit, current_text))
       
       new_text = ""
       if len(digits) > 4:
           new_text = f"{digits[:4]}-"
           if len(digits) > 6:
               new_text += f"{digits[4:6]}-{digits[6:8]}"
           else:
               new_text += f"{digits[4:6]}"
       elif len(digits) > 0:
           new_text = digits[:4]

       new_text = new_text[:10]

       if current_text != new_text:
           widget.delete(0, tk.END)
           widget.insert(0, new_text)

       cursor_pos = widget.index(tk.INSERT)
       if cursor_pos < len(new_text):
           next_char = new_text[cursor_pos] if cursor_pos < len(new_text) else None
           if next_char == '-':
               widget.icursor(cursor_pos + 1)
           elif cursor_pos == 4 and len(new_text) > 5:
               widget.icursor(5)
           elif cursor_pos == 7 and len(new_text) > 8:
               widget.icursor(8)

    def save_donor_changes(self):
       """Сохраняет измененные данные донора в БД."""
       db = DatabaseConnection(DB_CONFIG)
       
       # Собираем данные из полей
       data = {field: var.get() for field, var in self.entries.items()}
       
       # Очистка статуса перед началом операции
       self.save_status_label.config(text="", fg="black")

       # Валидация: Проверка на пустые обязательные поля Роста и Веса
       height_str = data['Рост (см)'].strip()
       weight_str = data['Вес (кг)'].strip()
       
       if not height_str or not weight_str:
           self.save_status_label.config(text="⚠ Поля 'Рост' и 'Вес' обязательны для заполнения.", fg="red")
           return

       try:
           height = int(height_str)
           weight = int(weight_str)
       except ValueError:
           self.save_status_label.config(text="⚠ Поля 'Рост' и 'Вес' должны содержать только цифры.", fg="red")
           return

       children = data['Дети (Да/Нет)'] == 'Да'
       stigma = data['Наличие стигм (Да/Нет)'] == 'Да'

       query = """
           UPDATE donors SET 
               sex=%s, birth_date=%s, blood_group=%s, rh_factor=%s,
               children=%s, height=%s, weight=%s,
               nationality=%s, hair_color=%s, hair_type=%s,
               eye_shape=%s, eye_color=%s, nose_shape=%s,
               face_shape=%s, forehead_shape=%s,
               body_type=%s, clothing_size=%s, shoe_size=%s,
               education=%s, profession=%s,
               stigma=%s
           WHERE id=%s;
       """
       
       params = (
           data['Пол (М/Ж)'], data['Дата рождения (ГГГГ-ММ-ДД)'], data['Группа крови'], data['Резус-фактор'],
           children, height, weight,
           data['Национальность'], data['Цвет волос'], data['Волосы (тип)'],
           data['Разрез глаз'], data['Цвет глаз'], data['Нос (форма)'],
           data['Овал лица'], data['Лоб'],
           data['Телосложение'], data['Размер одежды'], data['Размер обуви'],
           data['Образование'], data['Профессия'],
           stigma,
           self.donor_id
       )
       
       success = db.execute_update(query, params)
       
       if success:
           self.save_status_label.config(text="✅ Данные донора успешно обновлены!", fg="green")
           self.load_biological_materials() # Обновляем список материалов после сохранения
       else:
          self.save_status_label.config(text="❌ Не удалось сохранить данные в базу данных.", fg="red")

    def load_biological_materials(self):
       """Загружает список биоматериалов для текущего донора в таблицу."""
       self.bio_tree.delete(*self.bio_tree.get_children())
       
       db = DatabaseConnection(DB_CONFIG)
       
       result = db.execute_query(
           """SELECT id AS id_bio, name_bio AS "Наименование", date_i AS "Дата получения", 
                  date_end AS "Срок годности", material_type AS "Тип"
              FROM biological_materials 
              WHERE id_donor = %s""",
           (self.donor_id,)
       )
       
       if result:
           for row in result:
               self.bio_tree.insert("", "end", values=row)

           # Устанавливаем фокус на первую запись
           first_item = self.bio_tree.get_children()[0]
           self.bio_tree.selection_set(first_item)
           self.bio_tree.focus(first_item)

    def add_new_bio(self):
        """Открывает окно добавления нового биоматериала для этого донора."""
        add_window = AddBioWindow(self.donor_id)
        add_window.parent = self  # Передаем ссылку на текущее окно как родителя
        #AddBioWindow(self.donor_id)
        #self.load_biological_materials() # Обновляем список после добавления

    def edit_selected_bio(self):
        """Открывает окно редактирования выбранного биоматериала."""
        selected_item = self.bio_tree.selection()
        
        if not selected_item:
             messagebox.showwarning("Предупреждение", "Пожалуйста, выберите биоматериал из списка.",parent=self)
             return

        bio_id = self.bio_tree.item(selected_item[0])['values'][0]
        
        #EditBioWindow(self.donor_id, bio_id)

        # Передаём self как parent
        edit_window = EditBioWindow(self.donor_id, bio_id)
        edit_window.parent = self  # Сохраняем ссылку на родителя

        self.load_biological_materials() # Обновляем список после редактирования

    def delete_selected_bio(self):
        """Удаляет выбранный биоматериал."""
        selected_item = self.bio_tree.selection()
        
        if not selected_item:
             messagebox.showwarning("Предупреждение", "Пожалуйста, выберите биоматериал из списка.",parent=self)
             return

        bio_id = self.bio_tree.item(selected_item[0])['values'][0]
        
        confirm = messagebox.askyesno("Подтверждение удаления", 
                                     f"Вы уверены, что хотите удалить биоматериал ID: {bio_id}?",parent=self)
        
        if confirm:
             db = DatabaseConnection(DB_CONFIG)
             success = db.execute_update("DELETE FROM biological_materials WHERE id = %s", (bio_id,))
             
             if success:
                 messagebox.showinfo("Успех", "Биоматериал удален.",parent=self)
                 self.load_biological_materials()

if __name__ == "__main__":
    app = AuthWindow()
    app.mainloop()