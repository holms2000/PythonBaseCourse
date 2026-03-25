import socket
import tkinter as tk
from tkinter import messagebox
import random
import os
from dotenv import load_dotenv
import sys

# --- Загрузка конфигурации ---
env_path = os.path.join(sys.path[0], '.env.example')
if not load_dotenv(env_path):
    load_dotenv()

HOST = os.getenv("HOST_SERVER")
PORT = int(os.getenv("PORT_SERVER"))


class GuessGameClient:
    def __init__(self, root):
        """
        Initializes the main application window and starts the mode selection screen.

        @requires: A valid Tkinter root window object.
        @modifies: The root window (sets title), initializes the socket attribute.
        @effects: Displays the initial mode selection screen.
        @raises: None
        @returns: None
        """
        self.root = root
        self.root.title("Угадай число")
        self.sock = None  # Сокет для сетевой игры
        self.show_mode_selection()

    def clear_window(self):
        """Удаляет все виджеты из текущего окна."""
        """
        Clears all widgets from the main application window.

        @requires: The root window to have child widgets.
        @modifies: The root window (destroys all child widgets).
        @effects: Empties the GUI screen for new content.
        @raises: None
        @returns: None
        """
        for widget in self.root.winfo_children():
            widget.destroy()

    # ------------------- ГЛАВНОЕ МЕНЮ -------------------
    def show_mode_selection(self):
        """Первый экран: выбор режима игры."""
        """
        Displays the main menu screen for selecting the game mode.

        @requires: The root window to be cleared of previous content.
        @modifies: The root window (adds new widgets).
        @effects: Shows buttons for "Local Play" and "Server Play".
        @raises: None
        @returns: None
        """
        self.clear_window()
        
        tk.Label(self.root, text="Выберите режим игры:", font=('Arial', 14)).pack(pady=20)
        
        tk.Button(self.root, text="Играть локально", 
                  command=self.show_local_setup, 
                  width=25, height=2).pack(pady=10)
        
        tk.Button(self.root, text="Играть на сервере", 
                  command=self.show_server_setup, 
                  width=25, height=2).pack(pady=10)

    # ------------------- ЛОКАЛЬНАЯ ИГРА -------------------
    def show_local_setup(self):
        """Показывает окно для ввода настроек локальной игры."""
        """
        Displays the configuration screen for local game mode.

        @requires: The root window to be cleared of previous content.
        @modifies: The root window (adds input fields and a start button).
        @effects: Shows input fields for number range and max attempts.
        @raises: None
        @returns: None
        """
        self.clear_window()
        
        frame = tk.Frame(self.root)
        frame.pack(padx=20, pady=20)

        tk.Label(frame, text="Настройки локальной игры", font=('Arial', 14)).grid(row=0, column=0, columnspan=2, pady=10)
        
        tk.Label(frame, text="Интервал (например: 1 100):").grid(row=1, column=0, sticky='e')
        self.range_entry_local = tk.Entry(frame)
        self.range_entry_local.grid(row=1, column=1)

        tk.Label(frame, text="Число попыток:").grid(row=2, column=0, sticky='e')
        self.attempts_entry_local = tk.Entry(frame)
        self.attempts_entry_local.grid(row=2, column=1)

        tk.Button(frame, text="Начать игру", command=self.start_local_session).grid(row=3, column=0, columnspan=2, pady=10)

    def start_local_session(self):
        """Запускает локальную игру после валидации настроек."""
        """
        Validates local game settings and starts a local game session.

        @requires: User input in the local setup fields.
        @modifies: The game state (initializes local variables), the GUI (switches to game screen).
        @effects: Generates a random number; creates the game interface; displays a start message.
                 Shows an error messagebox if validation fails.
        @raises: ValueError if input data is invalid (handled internally).
        @returns: None
        """
        range_text = self.range_entry_local.get()
        attempts_text = self.attempts_entry_local.get()
        
        if not range_text or not attempts_text:
            messagebox.showerror("Ошибка", "Заполните все поля!")
            return

        try:
            min_num, max_num = map(int, range_text.split())
            max_attempts = int(attempts_text)
            if min_num >= max_num or max_attempts <= 0:
                raise ValueError("Неверный диапазон или число попыток.")
            
            # Уничтожаем фрейм настроек и начинаем игру
            self.range_entry_local.master.destroy()
            
            # Создаем виджеты игры (общие для обоих режимов)
            self.create_game_widgets(min_num, max_num, max_attempts)
            
            # Инициализация переменных для локальной игры
            self.local_number = random.randint(min_num, max_num)
            self.local_attempts = 0
            self.max_attempts = max_attempts

            # Показываем стартовое сообщение
            start_msg = f"Игра началась! Угадайте число от {min_num} до {max_num}. У вас {max_attempts} попыток.\n"
            self.result_text.insert(tk.END, start_msg)
            
        except ValueError as e:
            messagebox.showerror("Ошибка", f"Неверный формат: {e}")

    # ------------------- СЕТЕВАЯ ИГРА -------------------
    def show_server_setup(self):
        """Показывает окно для ввода настроек подключения к серверу."""
        """
        Displays the configuration screen for connecting to a server.

        @requires: The root window to be cleared of previous content.
        @modifies: The root window (adds input fields and a start button).
        @effects: Shows input fields for number range and max attempts for server play.
        @raises: None
        @returns: None
        """
        self.clear_window()
        
        frame = tk.Frame(self.root)
        frame.pack(padx=20, pady=20)

        tk.Label(frame, text="Подключение к серверу", font=('Arial', 14)).grid(row=0, column=0, columnspan=2, pady=10)
        
        tk.Label(frame, text="Интервал (например: 1 100):").grid(row=1, column=0, sticky='e')
        self.range_entry_server = tk.Entry(frame)
        self.range_entry_server.grid(row=1, column=1)

        tk.Label(frame, text="Число попыток:").grid(row=2, column=0, sticky='e')
        self.attempts_entry_server = tk.Entry(frame)
        self.attempts_entry_server.grid(row=2, column=1)

        tk.Button(frame, text="Начать игру", command=self.start_game).grid(row=3, column=0, columnspan=2, pady=10)

    def start_game(self):
        """Логика подключения к серверу."""
        """
        Attempts to connect to the server and starts a network game session.

        @requires: User input in the server setup fields; HOST and PORT environment variables set.
        @modifies: The socket connection state (`self.sock`), the GUI (switches to game screen).
        @effects: Creates a socket; connects to the server; sends initial game parameters;
             receives welcome message; creates the game interface.
             Shows an error messagebox on connection failure or invalid input.
        @raises: socket.error on connection failure (handled internally).
             ValueError if input data is invalid (handled internally).
        @returns: None
        """
        range_text = self.range_entry_server.get()
        attempts_text = self.attempts_entry_server.get()
        
        if not range_text or not attempts_text:
            messagebox.showerror("Ошибка", "Заполните все поля!")
            return

        try:
            min_num, max_num = map(int, range_text.split())
            max_attempts = int(attempts_text)
            if min_num >= max_num or max_attempts <= 0:
                raise ValueError("Неверный диапазон или число попыток.")
            
            # Уничтожаем фрейм настроек и подключаемся к серверу
            self.range_entry_server.master.destroy()
            
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.connect((HOST, PORT))
                self.sock.sendall(f"{min_num},{max_num},{max_attempts}".encode())
                
                # Создаем виджеты игры (общие для обоих режимов)
                self.create_game_widgets(min_num, max_num, max_attempts)
                
                # Получаем первое сообщение от сервера (подтверждение начала)
                self.receive_message()
                
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось подключиться к серверу: {e}")
                self.show_mode_selection() # Возвращаем выбор режима при ошибке

        except ValueError as e:
            messagebox.showerror("Ошибка", f"Неверный формат: {e}")

    # ------------------- ИНТЕРФЕЙС ИГРЫ -------------------
    def create_game_widgets(self, min_num, max_num, max_attempts):
        """Создает интерфейс для самой игры. Используется и для сети, и для локалки."""
        """
        Creates and packs all widgets for the active game session UI.
 
        @param min_num: Minimum number in the guessing range.
        @param max_num: Maximum number in the guessing range.
        @param max_attempts: Maximum number of allowed guesses.
        @modifies: self.game_frame, self.info_label, self.guess_entry, etc. are set as attributes.
        @returns: None
        """
        self.game_frame = tk.Frame(self.root)
        self.game_frame.pack(padx=20, pady=20)
        
        self.info_label = tk.Label(self.game_frame, text="", wraplength=350)
        self.info_label.pack(pady=5)
        
        tk.Label(self.game_frame, text=f"Интервал: {min_num}-{max_num} | Попыток: {max_attempts}").pack(pady=5)
        
        self.guess_label = tk.Label(self.game_frame, text="Ваше предположение:")
        self.guess_label.pack(pady=5)
        
        self.guess_entry = tk.Entry(self.game_frame)
        self.guess_entry.pack(pady=5)
        
        # Кнопка вызывает универсальный метод обработки хода
        self.send_button = tk.Button(self.game_frame, text="Отправить", command=self.process_guess)
        self.send_button.pack(pady=5)
        
        self.result_text = tk.Text(self.game_frame, height=8, width=45)
        self.result_text.pack(pady=5)
        
    def process_guess(self):
        """Обрабатывает ход игрока. Работает и для сети, и для локальной игры."""
        """
        Handles a player's guess submission. Logic branches based on local or network mode.
 
        @requires: User input in self.guess_entry; game state initialized (either local or network).
        @modifies: Game state (local_attempts), GUI (updates result_text), or network socket state (sends data).
        @effects: For local mode: Compares guess to self.local_number and updates UI with result or win/loss message.
              For network mode: Sends guess to server via socket and calls receive_message().
              Disables input controls on game end. Shows error messagebox on invalid integer input.
        @raises: ValueError if guess cannot be converted to int (handled internally).
        @returns: None
        """
        guess = self.guess_entry.get().strip()
        
        if not guess:
            return

        try:
            guess_int = int(guess)
            
            # --- ЛОКАЛЬНАЯ ЛОГИКА ---
            if hasattr(self, 'local_number'): 
                self.local_attempts += 1
                remaining = self.max_attempts - self.local_attempts

                if guess_int < self.local_number:
                    response = f"Введено число {guess_int}. Больше! Осталось попыток: {remaining}\n"
                elif guess_int > self.local_number:
                    response = f"Введено число {guess_int}. Меньше! Осталось попыток: {remaining}\n"
                else:
                    response = f"🎉 Поздравляю! Вы угадали число {self.local_number} за {self.local_attempts} попыток.\n"
                    self.send_button.config(state='disabled')
                
                if remaining == 0 and guess_int != self.local_number:
                    response += f"❌ Попытки закончились. Загаданное число было: {self.local_number}\n"
                    self.send_button.config(state='disabled')
                
                self.result_text.insert(tk.END, response)
                return # Завершаем функцию для локального режима

            # --- СЕТЕВАЯ ЛОГИКА ---
            if not hasattr(self, 'sock') or not self.sock.fileno(): 
                return

            self.sock.sendall(guess.encode())
            
            # Очищаем поле ввода только для сети (в локалке это делает блок выше или по нажатию Enter в поле Text)
            self.guess_entry.delete(0, tk.END)
            
            # Получаем ответ от сервера
            self.receive_message()
            
        except ValueError:
             messagebox.showerror("Ошибка", "Пожалуйста, введите целое число.")
             return

    def receive_message(self):
        """Получает и отображает сообщения ТОЛЬКО для сетевой игры."""
        """
        Receives messages from the server during a network game session and updates the UI accordingly.
 
        @requires: An active network connection via self.sock; a running Tkinter mainloop to update widgets safely.
        @modifies: GUI widgets (self.result_text), socket state (closes socket), button states (disables guess_entry/send_button).
        @effects: Reads data from socket and inserts it into self.result_text. Checks for end-game keywords to disable controls,
              display "Main Menu" button, and close the socket connection. Handles unexpected disconnections by showing an error dialog and returning to mode selection screen. Automatically scrolls text widget to the end after insertion. Catches general exceptions to prevent app crash on network errors and closes the main window on critical failure.
        @raises: socket.error on receive failure or connection reset (handled internally with error dialogs).
              Exception on other unexpected errors during receive/UI update (handled by closing app).
        @returns: None
        """
        try:
            data = self.sock.recv(2048).decode()
            
            if data:
                self.result_text.insert(tk.END, data + "\n")
                
                # Проверка на конец игры по ключевым словам из ответа сервера
                if "🎉" in data or "❌" in data or "Попытки закончились" in data or "Поздравляю" in data:
                    self.guess_entry.config(state='disabled')
                    self.send_button.config(state='disabled')
                    
                    back_btn = tk.Button(self.game_frame, text="Главное меню", command=self.show_mode_selection)
                    back_btn.pack(pady=10)
                    
                    exit_btn = tk.Button(self.game_frame, text="Выход", command=self.root.destroy)
                    exit_btn.pack(pady=5)
                    
                    # Закрываем сокет после окончания игры
                    if hasattr(self, 'sock'):
                        try:
                            self.sock.close()
                        except Exception as e:
                            print(f"Ошибка закрытия сокета: {e}")
                            pass

                self.result_text.see(tk.END) # Прокрутка вниз

                # Обработка внезапного отключения сервера (если данные пустые или сокет закрылся с ошибкой)
                if not data or not hasattr(self.sock, '_closed') or self.sock._closed:
                    messagebox.showerror("Ошибка", "Сервер был отключен.")
                    self.show_mode_selection()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Проблема с соединением: {e}")
            self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = GuessGameClient(root)
    root.mainloop()