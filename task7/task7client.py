import tkinter as tk
from tkinter import ttk, messagebox
import socket
import json
import os
from dotenv import load_dotenv
from pathlib import Path
import sys

#сначала берем параметры базы из файла .env.example 
env_path = os.path.join(sys.path[0], '.env.example1')

if load_dotenv(env_path)==False:
   load_dotenv()

# --- Конфигурация сервера ---
HOST = os.getenv("HOST_SERVER")
PORT = int(os.getenv("PORT_SERVER"))

# --- Вспомогательные классы ---

class Tooltip:
    def __init__(self, widget, text, delay=500):
        self.widget, self.text, self.delay = widget, text, delay
        self._after_id = None
        self._tip = None
        widget.bind("<Enter>", self._schedule)
        widget.bind("<Leave>", self._hide)
        widget.bind("<ButtonPress>", self._hide)
        widget.bind("<Motion>", self._move)

    def _schedule(self, _=None):
        self._cancel()
        self._after_id = self.widget.after(self.delay, self._show)

    def _show(self):
        if self._tip:
            return
        self._tip = tk.Toplevel(self.widget)
        self._tip.wm_overrideredirect(True)
        self._tip.wm_attributes("-topmost", True)
        tk.Label(self._tip, text=self.text, bg="#ffffe0",
                 relief="solid", bd=1, justify="left").pack(ipadx=4, ipady=2)
        self._move()

    def _move(self, event=None):
        if not self._tip:
            return
        x = (event.x_root + 12) if event else self.widget.winfo_rootx() + 12
        y = (event.y_root + 8) if event else self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        self._tip.geometry(f"+{x}+{y}")

    def _hide(self, _=None):
        self._cancel()
        if self._tip:
            self._tip.destroy()
            self._tip = None

    def _cancel(self):
        if self._after_id:
            self.widget.after_cancel(self._after_id)
            self._after_id = None

# --- Основной класс приложения ---

class FarmersMarketsApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Приложение фермерских рынков")
        self.geometry("800x650")
        
        # Состояние пользователя
        self.logged_in_user = None
        self.logged_in_fullname = ""
        
        # Окно деталей (чтобы не открывалось несколько раз)
        self.details_window = None 
        
        # Запуск окна входа
        self.login_window()

    # --- Методы взаимодействия с сервером ---
    def send_to_server(self, action, params):
        """Отправляет запрос на сервер и возвращает ответ."""
        request = {"action": action, "params": params}
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5)  # Таймаут 5 секунд
                try:
                    s.connect((HOST, PORT))
                except (socket.error, ConnectionRefusedError) as e:
                      # Не удалось даже установить соединение
                      return {"status": "error", "message": f"Не удалось подключиться к серверу.\n{str(e)}"}
            
                try:
                    s.sendall(json.dumps(request).encode('utf-8'))
                except Exception as e:
                      return {"status": "error", "message": f"Ошибка при отправке данных: {str(e)}"}

                # --- НАЧАЛО БЛОКА ПРИЕМА ДАННЫХ (ИСПРАВЛЕННОГО) ---
                data = ""
                while True:
                     try:
                         chunk = s.recv(4096).decode('utf-8')
                         if not chunk: 
                         # Сервер закрыл соединение
                            break
                         data += chunk
                    
                         # Пытаемся распарсить то, что получили
                         return json.loads(data)
                        
                     except json.JSONDecodeError:
                            # Данные еще не полные, продолжаем читать
                            continue
                     except socket.timeout:
                           return {"status": "error", "message": "Превышено время ожидания ответа от сервера."}
            
                # Если мы вышли из цикла while (сервер закрыл соединение),
                # но у нас накопились какие-то данные, пробуем распарсить их в последний раз.
                if data:
                   try:
                        return json.loads(data)
                   except json.JSONDecodeError:
                        return {"status": "error", "message": "Получен некорректный ответ от сервера (не JSON)."}
                else:
                     return {"status": "error", "message": "Сервер закрыл соединение без отправки данных."}
                # --- КОНЕЦ БЛОКА ПРИЕМА ДАННЫХ ---

        except Exception as e:
              # Это поймает ошибки создания сокета и другие непредвиденные проблемы
              return {"status": "error", "message": f"Внутренняя ошибка клиента: {str(e)}"}
        
    # --- Окно входа и регистрации ---
    def login_window(self):
        login_frame = tk.Frame(self)
        login_frame.pack(fill="both", expand=True)

        label_username = ttk.Label(login_frame, text="Имя пользователя:", font=("Arial", 14))
        label_username.pack(padx=10, pady=10)
        entry_username = ttk.Entry(login_frame, width=30)
        entry_username.pack(padx=10, pady=5)
        entry_username.focus_set()
        
        entry_username.bind("<Return>", lambda event: entry_password.focus_set())

        label_password = ttk.Label(login_frame, text="Пароль:", font=("Arial", 14))
        label_password.pack(padx=10, pady=10)
        entry_password = ttk.Entry(login_frame, show="*", width=30)
        entry_password.pack(padx=10, pady=5)
        
        entry_password.bind("<Return>", lambda event: self.authenticate(entry_username.get(), entry_password.get()))

        button_login = ttk.Button(login_frame, text="Войти", command=lambda: self.authenticate(entry_username.get(), entry_password.get()))
        button_login.pack(padx=10, pady=10)
        
        button_register = ttk.Button(login_frame, text="Зарегистрироваться", command=self.register_window)
        button_register.pack(padx=10, pady=10)
        
    def authenticate(self, username, password):
       auth_result = self.send_to_server('verify_login', {'username': username, 'password': password})
       
       if auth_result.get('status') == 'ok':
           if auth_result.get('authenticated'):
               self.logged_in_user = username
               self.logged_in_fullname = auth_result.get('fullname', username)
               self.clear_login_screen()
           else:
               messagebox.showerror("Ошибка", auth_result.get('message', "Неверные данные для входа."))
       else:
           messagebox.showerror("Ошибка сервера", auth_result.get('message'))

    def register_window(self):
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

       button_register = ttk.Button(register_frame, text="Зарегистрироваться", command=lambda: self.register_user(
           entry_firstname.get(), entry_lastname.get(), entry_username.get(), entry_password.get()))
       button_register.pack(padx=10, pady=10)
    
    def register_user(self, firstname, lastname, username, password):
       if not firstname or not lastname or not username or not password:
           messagebox.showerror("Ошибка", "Все поля должны быть заполнены.")
           return

       exists_result = self.send_to_server('check_user_exists', {'username': username})
       
       if exists_result.get('status') == 'ok' and exists_result.get('exists'):
           messagebox.showerror("Ошибка", "Такой пользователь уже существует.")
           return

       create_result = self.send_to_server('create_user', {
           'username': username,
           'password': password,
           'firstname': firstname,
           'lastname': lastname
       })
       
       if create_result.get('status') == 'ok':
           messagebox.showinfo("Успех", "Вы успешно зарегистрированы.")
           #self.login_window() # Можно вернуть окно логина или оставить как есть
       else:
           messagebox.showerror("Ошибка сервера", create_result.get('message'))
    
    def clear_login_screen(self):
       for widget in self.winfo_children():
           widget.destroy()
       self.main_app()
    
    def logout(self):
      """Сброс состояния пользователя и возврат к окну входа."""
      result = messagebox.askyesno("Выход", "Вы уверены?")
      if result:
          for widget in self.winfo_children():
              widget.destroy()
          self.logged_in_user = None
          self.logged_in_fullname = ""
          self.login_window()
    
    # --- Основное приложение ---
    def main_app(self):
       welcome_label = ttk.Label(self, text=f"Добро пожаловать, {self.logged_in_fullname}!", font=("Arial", 16))
       welcome_label.pack(pady=(20, 10))
       
       logout_btn = ttk.Button(self, text="Выйти", command=self.logout)
       logout_btn.pack(pady=(0, 20))
       
       # Закладочная панель (Notebook)
       self.tab_control = ttk.Notebook(self)
       
       self.tab_view_all = ttk.Frame(self.tab_control)
       self.tab_search = ttk.Frame(self.tab_control)
       
       self.tab_control.add(self.tab_view_all, text="Просмотр рынков")
       self.tab_control.add(self.tab_search, text="Поиск рынков")
       
       self.tab_control.pack(expand=True, fill="both")
       
       # Вкладка "Просмотр всех рынков"
       button_view_all = ttk.Button(self.tab_view_all, text="Показать все рынки", command=self.load_all_markets)
       button_view_all.pack(pady=10)
       
       columns_view_all = ("FMID", "Название", "Адрес")
       self.tree_view_all = ttk.Treeview(self.tab_view_all, columns=columns_view_all, show="headings")
       
       # <Double-1> — это событие двойного щелчка левой кнопкой мыши.
       self.tree_view_all.bind("<Double-1>", self.on_row_double_click)


       for col in columns_view_all:
           self.tree_view_all.heading(col, text=col)
           if col == "FMID":
               self.tree_view_all.column(col,width=50,minwidth=40)
           elif col == "Название":
               self.tree_view_all.column(col,width=250,minwidth=40)
           else:
               self.tree_view_all.column(col,width=350,minwidth=40)
               
       scrollbar_y_all = ttk.Scrollbar(self.tab_view_all, orient="vertical", command=self.tree_view_all.yview)
       
       self.tree_view_all.configure(yscrollcommand=scrollbar_y_all.set)
       
       scrollbar_y_all.pack(side="right", fill="y")
       self.tree_view_all.pack(side="left", fill="both", expand=True)
       
       Tooltip(self.tree_view_all, "Двойной клик для просмотра подробностей.", delay=700)
       
       # Вкладка "Поиск рынков"
       
       search_frame_top = tk.Frame(self.tab_search)
       search_frame_top.pack(fill='x', padx=20, pady=(20, 5))
       
       label_search_city = ttk.Label(search_frame_top, text="Город:", font=("Arial", 12))
       label_search_city.grid(row=0, column=0, sticky='e')
       
       entry_search_city = ttk.Entry(search_frame_top, width=25)
       entry_search_city.grid(row=0, column=1,padx=(5), sticky='w')
       
       label_search_state = ttk.Label(search_frame_top, text="Штат:", font=("Arial", 12))
       label_search_state.grid(row=0, column=2,sticky='e')
       
       entry_search_state = ttk.Entry(search_frame_top, width=25)
       entry_search_state.grid(row=0, column=3,padx=(5), sticky='w')
         
       button_advanced_search = ttk.Button(search_frame_top,
                                             text="Расширенный поиск",
                                             command=self.open_search_dialog)
       button_advanced_search.grid(row=0, column=4,padx=(20), sticky='e')
         
       button_search_simple = ttk.Button(search_frame_top,
                                           text="Искать",
                                           command=lambda: self.search_markets(
                                               city=entry_search_city.get(),
                                               state=entry_search_state.get()))
       button_search_simple.grid(row=0, column=5,padx=(5), sticky='w')
         
       Tooltip(button_advanced_search,
                 "Поиск по индексу или координатам.", delay=700)
         
       Tooltip(button_search_simple,
                 "Поиск по городу и штату.", delay=700)
         
       columns_search = ("FMID", "Название", "Адрес")
       self.tree_search = ttk.Treeview(self.tab_search,
                                         columns=columns_search,
                                         show="headings")
       # <Double-1> — это событие двойного щелчка левой кнопкой мыши.
       self.tree_search.bind("<Double-1>", self.on_row_double_click)

       for col in columns_search:
             self.tree_search.heading(col,text=col)
             if col == "FMID":
                 self.tree_search.column(col,width=60,minwidth=40)
             elif col == "Название":
                 self.tree_search.column(col,width=280,minwidth=40)
             else:
                 self.tree_search.column(col,width=360,minwidth=40)
                 
       scrollbar_y_search = ttk.Scrollbar(self.tab_search,
                                            orient="vertical",
                                            command=self.tree_search.yview)
         
       self.tree_search.configure(yscrollcommand=scrollbar_y_search.set)
         
       scrollbar_y_search.pack(side="right", fill="y")
       self.tree_search.pack(side="left", fill="both", expand=True,padx=(20),pady=(5))
         
       Tooltip(self.tree_search,
                 "Двойной клик для просмотра подробностей.", delay=700)
    
    # --- Логика работы с данными ---
    
    def on_row_double_click(self, event):
       """Обработчик двойного клика по строке в таблице."""
       tree = event.widget
       selected_items = tree.selection()
       if not selected_items:
         print("Ошибка: Строка не выбрана.")
         return

       # Берем первую выбранную строку (если выбрано несколько)
       selected_item_id = selected_items[0]
    
       # Получаем значения всех колонок этой строки
       item_values = tree.item(selected_item_id)['values']
    
       # Проверяем, что значения вообще есть и первое из них не пустое
       if not item_values or item_values[0] is None or str(item_values[0]).strip() == '':
         messagebox.showerror("Ошибка", "В этой строке нет данных об идентификаторе рынка.")
         print(f"Ошибка: Пустые значения в строке {selected_item_id}. Значения: {item_values}")
         return

       fmid_str_val = str(item_values[0])
       print(f"Выбрана строка. Извлеченный FMID (строка): '{fmid_str_val}'") # Отладочная печать

       try:
           fmid_int_val = int(fmid_str_val)
           print(f"Успешное преобразование в число: {fmid_int_val}") # Отладочная печать
           self.open_details_window(fmid_int_val)
        
       except ValueError:
              messagebox.showerror("Ошибка", "Неверный идентификатор рынка. Невозможно преобразовать в число.")
              print(f"Ошибка ValueError при попытке преобразовать '{fmid_str_val}' в int.")
    
    def load_all_markets(self):
        markets_data = self.send_to_server('find_markets', {})
        
        if markets_data.get('status') != 'ok':
            messagebox.showwarning("Предупреждение", markets_data.get('message', "Ошибка получения данных."))
            return

        markets = markets_data.get('data', [])
        
        # Очистка таблицы перед вставкой новых данных
        for child in self.tree_view_all.get_children():
            self.tree_view_all.delete(child)
            
        for market in markets:
            # Распаковка данных, пришедших от сервера
            fmid, name, city, state, zip_code, *rest = market
            
            # Формирование строки адреса
            address_parts = [part for part in [city, state, zip_code] if part]
            address_str = ", ".join(address_parts) if address_parts else ""
            
            # Вставка строки в таблицу
            self.tree_view_all.insert("", "end", values=(str(fmid), name or "", address_str or ""))
            
        if not markets:
            messagebox.showwarning("Предупреждение", "Нет доступных рынков.")
    
    def search_markets(self, city=None, state=None):
        """Простой поиск по городу и штату."""
        params = {}
        if city: params['city'] = city.strip()
        if state: params['state'] = state.strip()
        
        markets_data = self.send_to_server('find_markets', params)
        
        if markets_data.get('status') != 'ok':
            messagebox.showwarning("Предупреждение", markets_data.get('message', "Ошибка получения данных."))
            return

        markets = markets_data.get('data', [])
        
        # Очистка таблицы перед вставкой новых данных
        for child in self.tree_search.get_children():
            self.tree_search.delete(child)
            
        for market in markets:
            fmid, name, city, state, zip_code, *rest = market
            address_parts = [part for part in [city, state, zip_code] if part]
            address_str = ", ".join(address_parts) if address_parts else ""
            
            self.tree_search.insert("", "end", values=(str(fmid), name or "", address_str or ""))
            
        if not markets:
            messagebox.showwarning("Предупреждение", "Рынков не найдено.")
    
    def open_search_dialog(self):
       """Диалог для расширенного поиска."""
       dialog = tk.Toplevel(self)
       dialog.title("Расширенный поиск")
       dialog.geometry("450x380")
       dialog.resizable(False, False)
       
       frame_main = tk.Frame(dialog,padx=20,pady=(20))
       frame_main.pack(fill='both')
       
       # Поля ввода
       label_city_dlg = ttk.Label(frame_main,text="Город:")
       label_city_dlg.grid(row=0,sticky='e')
       entry_city_dlg = ttk.Entry(frame_main,width=35)
       entry_city_dlg.grid(row=0,rowspan=2,padx=(5),sticky='w')
       
       label_state_dlg = ttk.Label(frame_main,text="Штат:")
       label_state_dlg.grid(row=2,sticky='e')
       entry_state_dlg = ttk.Entry(frame_main,width=35)
       entry_state_dlg.grid(row=2,rowspan=2,padx=(5),sticky='w')
       
       label_zip_dlg = ttk.Label(frame_main,text="Индекс (ZIP):")
       label_zip_dlg.grid(row=4,sticky='e')
       entry_zip_dlg = ttk.Entry(frame_main,width=35)
       entry_zip_dlg.grid(row=4,rowspan=2,padx=(5),sticky='w')
       
       label_lat_dlg = ttk.Label(frame_main,text="Широта:")
       label_lat_dlg.grid(row=6,sticky='e')
       entry_lat_dlg = ttk.Entry(frame_main,width=35)
       entry_lat_dlg.grid(row=6,rowspan=2,padx=(5),sticky='w')
       
       label_lon_dlg = ttk.Label(frame_main,text="Долгота:")
       label_lon_dlg.grid(row=8,sticky='e')
       entry_lon_dlg = ttk.Entry(frame_main,width=35)
       entry_lon_dlg.grid(row=8,rowspan=2,padx=(5),sticky='w')
       
       label_dist_dlg = ttk.Label(frame_main,text="Макс. расстояние (мили):")
       label_dist_dlg.grid(row=10,sticky='e')
       entry_dist_dlg = ttk.Entry(frame_main,width=35)
       entry_dist_dlg.grid(row=10,rowspan=2,padx=(5),sticky='w')
       
       # Сортировка
       frame_sort = tk.Frame(frame_main)
       frame_sort.grid(row=12, columnspan=2, pady=(20, 0))

       var_apply_sort = tk.BooleanVar(value=False)
       chk_apply_sort = ttk.Checkbutton(frame_sort, text="Сортировать по рейтингу", variable=var_apply_sort)
       chk_apply_sort.pack(side="left")

       var_sort_order = tk.StringVar(value="desc")
       chk_sort_asc = ttk.Checkbutton(frame_sort, text="По возрастанию", variable=var_sort_order, onvalue="asc", offvalue="desc")
       chk_sort_asc.pack(side="left")

       # Кнопки
       frame_btns = tk.Frame(dialog)
       frame_btns.pack(fill='x', padx=20, pady=(20, 20))

       btn_search = ttk.Button(frame_btns, text="Искать", command=lambda: self.perform_search(
           entry_city_dlg.get(),
           entry_state_dlg.get(),
           entry_zip_dlg.get(),
           entry_lat_dlg.get(),
           entry_lon_dlg.get(),
           entry_dist_dlg.get(),
           var_apply_sort.get(),
           var_sort_order.get(),
           dialog,
           self.tree_search # Передаем таблицу для заполнения
       ))
       btn_search.pack(side="left", padx=(0, 10))

       btn_cancel = ttk.Button(frame_btns, text="Отмена", command=dialog.destroy)
       btn_cancel.pack(side="right")
    
    def perform_search(self, city, state, zip_code, latitude, longitude, max_distance,
                       apply_sort, sort_order, dialog, tree_to_fill):
        """Выполнение расширенного поиска."""
        params = {}
        if city.strip(): params['city'] = city.strip()
        if state.strip(): params['state'] = state.strip()
        if zip_code.strip(): params['zip_code'] = zip_code.strip()

        # Валидация числовых параметров
        try:
            if latitude.strip() and longitude.strip() and max_distance.strip():
                params['latitude'] = float(latitude)
                params['longitude'] = float(longitude)
                params['max_distance'] = float(max_distance)
                params['sort_by_rating'] = apply_sort
                params['sort_order'] = sort_order
        except ValueError:
            messagebox.showwarning("Предупреждение", "Координаты и расстояние должны быть числами.")
            return

        markets_data = self.send_to_server('find_markets', params)
        
        # Очистка таблицы перед вставкой новых данных
        for child in tree_to_fill.get_children():
            tree_to_fill.delete(child)

        if markets_data.get('status') != 'ok':
            messagebox.showwarning("Ошибка", markets_data.get('message', "Ошибка получения данных."))
            dialog.destroy()
            return

        markets = markets_data.get('data', [])
        
        for market in markets:
            fmid, name, city_db, state_db, zip_code_db, *rest = market 
            address_parts = [part for part in [city_db, state_db, zip_code_db] if part]
            address_str = ", ".join(address_parts) if address_parts else ""
            
            tree_to_fill.insert("", "end", values=(str(fmid), name or "", address_str or ""))
            
        if not markets:
            messagebox.showwarning("Предупреждение", "Рынков не найдено.")
            
        dialog.destroy()
    
    def open_details_window(self, fmid):
        """Открывает модальное окно с подробной информацией о рынке."""
        # Предотвращаем открытие нескольких окон
        if self.details_window is not None and self.details_window.winfo_exists():
            self.details_window.lift()
            return

        # Создаем новое окно
        self.details_window = tk.Toplevel(self)
        self.details_window.title("Подробности о рынке")
        self.details_window.geometry("800x600")
        
        # Блокируем главное окно и делаем новое окно модальным
        self.details_window.transient(self)
        
        # --- Получение данных с сервера ---
        details_data = self.send_to_server('get_market_details', {'fmid': fmid})
        
        if details_data.get('status') != 'ok':
            messagebox.showerror("Ошибка", details_data.get('message'))
            self.details_window.destroy()
            return

        data = details_data['data']
        
        # --- Сборка текстового описания ---
        details_text = ""
        
        # 1. Основная информация
        market_info = data.get('market', [])
        address_info = data.get('address', [])
        
        if market_info and address_info:
            details_text += f"Название: {market_info[2]}\n"
            
            street = address_info[1] or ""
            city_state_zip = f"{address_info[2]}, {address_info[3]} {address_info[4]}" if address_info[2] and address_info[3] else ""
            details_text += f"Адрес: {street} {city_state_zip}\n"
            
            coords_info = data.get('coords', [])
            if coords_info:
                details_text += f"Координаты: {coords_info[1]}, {coords_info[2]}\n"
        
        # 2. Социальные сети
        social_links = data.get('social', {})
        if social_links:
            details_text += "\n--- СОЦИАЛЬНЫЕ СЕТИ ---\n"
            for platform, link in social_links.items():
                if link:
                    details_text += f"{platform}: {link}\n"
        
        # 3. Способы оплаты
        payment_options = data.get('payment', {})
        if payment_options:
            details_text += "\n--- СПОСОБЫ ОПЛАТЫ ---\n"
            for option, available in payment_options.items():
                details_text += f"{option}: {'Да' if available else 'Нет'}\n"
        
        # 4. Продукты
        products_list = data.get('products', [])
        if products_list:
            details_text += "\n--- ПРОДУКТЫ НА РЫНКЕ ---\n"
            details_text += ", ".join(products_list) + "\n"
        
        # 5. График работы
        schedule_list = data.get('schedule', [])
        if schedule_list:
            details_text += "\n--- ГРАФИК РАБОТЫ ---\n"
            for sched in schedule_list:
                details_text += f"Сезон {sched['Season Number']}: {sched['Season Date']}, Время: {sched['Season Time']}\n"
        
        # 6. Отзывы
        reviews_data = self.send_to_server('get_reviews_by_fmid', {'fmid': fmid})
        details_text += "\n--- ОТЗЫВЫ ---\n"
        
        if reviews_data.get('status') == 'ok':
            reviews_list = reviews_data.get('data', [])
            if reviews_list:
                for rev in reviews_list:
                    author_name = rev.get('fullname', rev.get('author', 'Аноним'))
                    details_text += f"Автор: {author_name}, Рейтинг: {rev['rating']}\n"
                    details_text += f"Комментарий: {rev['comment']}\n\n"
            else:
                details_text += "Отзывов нет.\n"

        # --- Вывод текста в окно ---
        text_area = tk.Text(self.details_window, wrap=tk.WORD)
        text_area.insert(tk.END, details_text)
        
        scrollbar_y = ttk.Scrollbar(self.details_window, orient="vertical", command=text_area.yview)
        text_area.configure(yscrollcommand=scrollbar_y.set, state=tk.DISABLED) # Блокируем редактирование текста
        
        text_area.pack(side="left", fill="both", expand=True)
        scrollbar_y.pack(side="right", fill="y")
        
        # Сохраняем ссылку на text_area для обновления из других методов
        self.details_window.text_area = text_area 

        # --- Блок для формы отзыва (только для авторизованных пользователей) ---
        if self.logged_in_user:
            frame_review_forms_container = tk.Frame(self.details_window)
            frame_review_forms_container.pack(fill="x", padx=10, pady=10)

            # Проверяем, оставлял ли пользователь отзыв ранее
            user_reviewed_data = self.send_to_server('user_has_reviewed', {'fmid': fmid, 'author': self.logged_in_user})
            
            if user_reviewed_data.get('status') == 'ok' and user_reviewed_data.get('has_reviewed'):
                # --- Форма для РЕДАКТИРОВАНИЯ отзыва ---
                frame_edit_review = tk.Frame(frame_review_forms_container)
                frame_edit_review.pack(fill="x")

                ttk.Label(frame_edit_review, text="Редактирование вашего отзыва:").pack(pady=(0, 5))
                
                frame_edit_fields = tk.Frame(frame_edit_review)
                frame_edit_fields.pack(fill="x")
                
                ttk.Label(frame_edit_fields, text="Новый рейтинг (1-5):", width=20, anchor="e").grid(row=0, column=0, sticky='e', padx=(0, 5))
                entry_new_rating_edit = ttk.Entry(frame_edit_fields, width=10)
                entry_new_rating_edit.grid(row=0, column=1, sticky='w')
                
                ttk.Label(frame_edit_fields, text="Новый комментарий:", width=20, anchor="e").grid(row=1, column=0, sticky='e', pady=(5, 0), padx=(0, 5))
                entry_new_comment_edit = ttk.Entry(frame_edit_fields, width=30)
                entry_new_comment_edit.grid(row=1, column=1, sticky='w', pady=(5, 0))
                
                # Заполняем поля текущими данными отзыва
                existing_review = reviews_list[0]
                entry_new_rating_edit.insert(0, str(existing_review['rating']))
                entry_new_comment_edit.insert(0, existing_review['comment'])

                frame_buttons = tk.Frame(frame_edit_review)
                frame_buttons.pack(fill="x", pady=(10, 0))

                ttk.Button(frame_buttons, text="Сохранить изменения",
                           command=lambda: self.save_review_changes(
                               fmid,
                               entry_new_rating_edit.get(),
                               entry_new_comment_edit.get())).pack(side="left", padx=(0, 10))

                ttk.Button(frame_buttons, text="Удалить отзыв",
                           command=lambda: self.delete_review(fmid)).pack(side="left")

            else:
                # --- Форма для СОЗДАНИЯ нового отзыва ---
                frame_create_review = tk.Frame(frame_review_forms_container)
                frame_create_review.pack(fill="x")

                ttk.Label(frame_create_review, text="Создать новый отзыв:").pack(pady=(0, 5))
                
                frame_create_fields = tk.Frame(frame_create_review)
                frame_create_fields.pack(fill="x")
                
                ttk.Label(frame_create_fields, text="Рейтинг (1-5):", width=20, anchor="e").grid(row=0, column=0, sticky='e', padx=(0, 5))
                entry_new_rating_create = ttk.Entry(frame_create_fields, width=10)
                entry_new_rating_create.grid(row=0, column=1, sticky='w')
                
                ttk.Label(frame_create_fields, text="Комментарий:", width=20, anchor="e").grid(row=1, column=0, sticky='e', pady=(5, 0), padx=(0, 5))
                entry_new_comment_create = ttk.Entry(frame_create_fields, width=30)
                entry_new_comment_create.grid(row=1, column=1, sticky='w', pady=(5, 0))

                frame_buttons = tk.Frame(frame_create_review)
                frame_buttons.pack(fill="x", pady=(10, 0))

                ttk.Button(frame_buttons, text="Отправить новый отзыв",
                           command=lambda: self.send_new_review(
                               fmid,
                               entry_new_rating_create.get(),
                               entry_new_comment_create.get())).pack(side="left")

        # --- Финальные настройки окна ---
        self.details_window.resizable(False, False)
        self.details_window.update_idletasks()  # Обновляем геометрию перед захватом фокуса
        self.details_window.grab_set()
        
        # Обработчик закрытия окна
        self.details_window.protocol("WM_DELETE_WINDOW", self.on_close_details_window)
    
    def on_close_details_window(self):
        """Освобождает фокус и закрывает окно деталей."""
        if hasattr(self.details_window, 'grab_release'):
            self.details_window.grab_release()
        self.details_window.destroy()
        self.details_window = None # Сбрасываем ссылку

    def send_new_review(self,fmid,rating_str,comment_str):
       """Отправка нового отзыва на сервер."""
       try:
           rating_value = int(rating_str)
           if 1 <= rating_value <= 5:
               result = self.send_to_server('add_review', {
                   'fmid': fmid,
                   'rating': rating_value,
                   'comment': comment_str,
                   'author': self.logged_in_user
               })
               
               if result.get('status') == 'ok':
                   messagebox.showinfo("Успех", "Ваш отзыв успешно отправлен.")
                   self.refresh_details_window(fmid)
               else:
                   messagebox.showerror("Ошибка", result.get('message'))
           else:
               messagebox.showwarning("Предупреждение", "Рейтинг должен быть от 1 до 5.")
       except ValueError:
           messagebox.showwarning("Предупреждение", "Недопустимый формат рейтинга.")
    
    def save_review_changes(self,fmid,new_rating_str,new_comment_str):
       """Сохранение изменений в существующем отзыве."""
       try:
           rating_value = int(new_rating_str)
           if 1 <= rating_value <= 5:
               result = self.send_to_server('edit_review', {
                   'fmid': fmid,
                   'new_rating': rating_value,
                   'new_comment': new_comment_str,
                   'author': self.logged_in_user
               })
               
               if result.get('status') == 'ok':
                   messagebox.showinfo("Успех", "Ваш отзыв успешно обновлён.")
                   self.refresh_details_window(fmid)
               else:
                   messagebox.showerror("Ошибка", result.get('message'))
           else:
               messagebox.showwarning("Предупреждение", "Рейтинг должен быть от 1 до 5.")
       except ValueError:
           messagebox.showwarning("Предупреждение", "Недопустимый формат рейтинга.")
    
    def delete_review(self,fmid):
       """Удаление отзыва пользователя."""
       answer = messagebox.askyesno("Подтверждение", "Вы действительно хотите удалить этот отзыв?")
       if answer:
           result = self.send_to_server('remove_review', {
               'fmid': fmid,
               'author': self.logged_in_user
           })
           
           if result.get('status') == 'ok':
               messagebox.showinfo("Успех", "Ваш отзыв удален.")
               self.refresh_details_window(fmid)
           else:
               messagebox.showerror("Ошибка", result.get('message'))
               
    def refresh_details_window(self,fmid):
       """Обновление содержимого окна деталей."""
       if self.details_window is not None and hasattr(self.details_window,'text_area'):
           # Удаляем старые виджеты
           old_text_area = self.details_window.text_area
           old_scrollbar = old_text_area.master.children['!scrollbar']
           
           old_text_area.destroy()
           old_scrollbar.destroy()
           
           # Открываем окно заново с тем же FMID
           self.open_details_window(fmid)

# Точка входа в приложение
if __name__ == "__main__":
    app = FarmersMarketsApp()
    app.mainloop()