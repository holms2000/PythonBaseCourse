import socket
import random
import os
from dotenv import load_dotenv
import sys
import threading

# Загрузка переменных окружения
env_path = os.path.join(sys.path[0], '.env.example')
if not load_dotenv(env_path):
    load_dotenv()

HOST = os.getenv("HOST_SERVER")
PORT = int(os.getenv("PORT_SERVER"))

def handle_client(conn, addr):
    """Обработка игровой сессии для одного клиента."""
    """
    Handles a game session for a single connected client.

    @requires: An open socket connection `conn` and client address `addr`.
    @modifies: The state of the connection (sends and receives data).
    @effects: Prints game progress messages to the server console; sends game status and feedback messages to the client.
    @raises: Exceptions on network errors or invalid client input.
    @returns: None
    """
    with conn:
        print(f"Игрок {addr} подключился.")
        try:
            data = conn.recv(1024).decode()
            if not data:
                print(f"{addr} отключился до начала игры.")
                return

            min_num, max_num, max_attempts = map(int, data.split(','))
            number = random.randint(min_num, max_num)
            attempts = 0

            welcome_msg = f"Игра началась! Угадайте число от {min_num} до {max_num}. У вас {max_attempts} попыток.\n"
            conn.sendall(welcome_msg.encode())

            while attempts < max_attempts:
                data = conn.recv(1024).decode()
                if not data:
                    print(f"{addr} отключился во время игры.")
                    break

                try:
                    guess = int(data)
                    attempts += 1
                    remaining = max_attempts - attempts

                    if guess < number:
                        response = f"Введено число {guess}. Больше! Осталось попыток: {remaining}\n"
                    elif guess > number:
                        response = f"Введено число {guess}. Меньше! Осталось попыток: {remaining}\n"
                    else:
                        response = f"🎉 Поздравляю! Вы угадали число {number} за {attempts} попыток.\n"
                        conn.sendall(response.encode())
                        break

                    conn.sendall(response.encode())
                except ValueError:
                    conn.sendall(f"Пожалуйста, введите целое число.\n")
            else:
                conn.sendall(f"❌ Попытки закончились. Загаданное число было: {number}\n".encode())
        except Exception as e:
            print(f"Ошибка с клиентом {addr}: {e}")
    print(f"Сессия с {addr} завершена.")

def start_server():
    """
    Initializes and starts the TCP server to listen for incoming client connections.

    @requires: HOST and PORT environment variables to be set.
    @modifies: Network state (opens a listening socket).
    @effects: Prints server status messages to the console; spawns new threads for each client connection.
    @raises: Exceptions on socket binding or listening errors.
    @returns: None
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print(f"Сервер запущен на {HOST}:{PORT}. Ожидание игроков...")

        while True:
            print("Ожидаем нового подключения...")
            conn, addr = s.accept()
            # Запускаем обработку клиента в отдельном потоке
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()

if __name__ == "__main__":
    """
    Entry point of the application.

    @requires: The script is executed directly (not imported as a module).
    @modifies: Program execution flow.
    @effects: Starts the server by calling start_server().
    @raises: Propagates exceptions from start_server().
    @returns: None
    """
    start_server()