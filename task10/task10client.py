import socket
import tkinter as tk
from tkinter import messagebox
import os
from dotenv import load_dotenv
from pathlib import Path
import sys

#сначала берем параметры базы из файла .env.example 
env_path = os.path.join(sys.path[0], '.env.example')

if load_dotenv(env_path)==False:
   load_dotenv()

# --- Конфигурация сервера ---
HOST = os.getenv("HOST_SERVER")
PORT = int(os.getenv("PORT_SERVER"))

class GuessGameClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Угадай число")
        self.sock = None
        self.create_setup_widgets()

    def create_setup_widgets(self):
        # Этап 1: Настройка игры
        self.frame_setup = tk.Frame(self.root)
        self.frame_setup.pack(padx=20, pady=20)

        tk.Label(self.frame_setup, text="Интервал (например: 1 100):").grid(row=0, column=0, sticky='e')
        self.range_entry = tk.Entry(self.frame_setup)
        self.range_entry.grid(row=0, column=1)

        tk.Label(self.frame_setup, text="Число попыток:").grid(row=1, column=0, sticky='e')
        self.attempts_entry = tk.Entry(self.frame_setup)
        self.attempts_entry.grid(row=1, column=1)

        self.start_button = tk.Button(self.frame_setup, text="Начать игру", command=self.start_game)
        self.start_button.grid(row=2, column=0, columnspan=2, pady=10)

    def start_game(self):
        # Получаем данные от пользователя
        range_text = self.range_entry.get()
        attempts_text = self.attempts_entry.get()
        
        if not range_text or not attempts_text:
            messagebox.showerror("Ошибка", "Заполните все поля!")
            return

        try:
            min_num, max_num = map(int, range_text.split())
            max_attempts = int(attempts_text)
            if min_num >= max_num or max_attempts <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат интервала или числа попыток!")
            return

        # Подключаемся к серверу и отправляем настройки
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((HOST, PORT))
            self.sock.sendall(f"{min_num},{max_num},{max_attempts}".encode())
            
            # Убираем виджеты настройки
            self.frame_setup.destroy()
            
            # Создаём виджеты для игры
            self.create_game_widgets(min_num, max_num, max_attempts)
            
            # Получаем первое сообщение от сервера (подтверждение начала)
            self.receive_message()
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось подключиться к серверу: {e}")
            self.root.destroy()

    def create_game_widgets(self, min_num, max_num, max_attempts):
        # Этап 2: Сама игра
        self.game_frame = tk.Frame(self.root)
        self.game_frame.pack(padx=20, pady=20)
        
        self.info_label = tk.Label(self.game_frame, text="", wraplength=300)
        self.info_label.pack(pady=5)
        
        tk.Label(self.game_frame, text=f"Интервал: {min_num}-{max_num} | Попыток: {max_attempts}").pack(pady=5)
        
        self.guess_label = tk.Label(self.game_frame, text="Ваше предположение:")
        self.guess_label.pack(pady=5)
        
        self.guess_entry = tk.Entry(self.game_frame)
        self.guess_entry.pack(pady=5)
        
        self.send_button = tk.Button(self.game_frame, text="Отправить", command=self.send_guess)
        self.send_button.pack(pady=5)
        
        self.result_text = tk.Text(self.game_frame, height=8, width=40)
        self.result_text.pack(pady=5)
        
    def send_guess(self):
        guess = self.guess_entry.get()
        if not guess:
            return
        try:
            int(guess) # Проверка на число (можно убрать для отправки строки серверу)
            self.sock.sendall(guess.encode())
            self.guess_entry.delete(0, tk.END)
            self.receive_message()
        except ValueError:
            messagebox.showerror("Ошибка", "Пожалуйста, введите целое число.")

    def receive_message(self):
        try:
            data = self.sock.recv(2048).decode() # Увеличим буфер для длинных сообщений
            if data:
                self.result_text.insert(tk.END, data)
                # Проверяем условия окончания игры
                if "🎉" in data or "❌" in data or "Попробуйте еще раз" in data:
                    self.guess_entry.config(state='disabled')
                    self.send_button.config(state='disabled')
                    self.info_label.config(text="Игра окончена.")
                else:
                    self.info_label.config(text="Введите число и нажмите Отправить.")
                
                # Прокручиваем текст в конец
                self.result_text.see(tk.END)
                
                # Закрываем сокет после окончания игры
                if "🎉" in data or "❌" in data:
                    self.sock.close()
                    
        except Exception as e:
            messagebox.showerror("Ошибка", f"Проблема с соединением: {e}")
            self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = GuessGameClient(root)
    root.mainloop()