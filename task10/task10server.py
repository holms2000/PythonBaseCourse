import socket
import random
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

def start_server():
    # Используем with, чтобы сокет корректно закрывался при остановке программы
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # Позволяет перезапускать сервер сразу после закрытия
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        s.bind((HOST, PORT))
        s.listen()
        print(f"Сервер запущен на {HOST}:{PORT}. Ожидание игроков...")

        # БЕСКОНЕЧНЫЙ ЦИКЛ: сервер будет работать, пока его не убьют вручную (Ctrl+C)
        while True:
            print("Ожидаем нового подключения...")
            conn, addr = s.accept() # Ждем нового клиента
            
            with conn:
                print(f"Игрок {addr} подключился.")
                
                try:
                    # Получаем настройки игры от клиента
                    data = conn.recv(1024).decode()
                    if not data:
                        print(f"{addr} отключился до начала игры.")
                        continue # Переходим к ожиданию следующего клиента

                    min_num, max_num, max_attempts = map(int, data.split(','))
                    number = random.randint(min_num, max_num)
                    attempts = 0

                    welcome_msg = f"Игра началась! Угадайте число от {min_num} до {max_num}. У вас {max_attempts} попыток.\n"
                    conn.sendall(welcome_msg.encode())

                    # Цикл одной игровой сессии
                    while attempts < max_attempts:
                        data = conn.recv(1024).decode()
                        if not data: # Клиент просто закрыл окно
                            print(f"{addr} отключился во время игры.")
                            break

                        try:
                            guess = int(data)
                            attempts += 1
                            remaining = max_attempts - attempts

                            if guess < number:
                                response = f"Больше! Осталось попыток: {remaining}\n"
                            elif guess > number:
                                response = f"Меньше! Осталось попыток: {remaining}\n"
                            else:
                                response = f"🎉 Поздравляю! Вы угадали число {number} за {attempts} попыток.\n"
                                conn.sendall(response.encode())
                                break

                            conn.sendall(response.encode())

                        except ValueError:
                            conn.sendall(f"Пожалуйста, введите целое число.\n")

                    else:
                        # Сюда попадаем, если попытки закончились (break не сработал)
                        conn.sendall(f"❌ Попытки закончились. Загаданное число было: {number}\n".encode())

                except Exception as e:
                    # Если клиент прислал ерунду или оборвал связь неожиданно
                    print(f"Ошибка с клиентом {addr}: {e}")

            # Блок 'with conn' закрывает соединение с текущим клиентом.
            # Цикл возвращается наверх к s.accept() и ждет следующего игрока.
            print(f"Сессия с {addr} завершена. Сервер готов к новому игроку.")

if __name__ == "__main__":
    start_server()