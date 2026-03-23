import socket
import json
import psycopg2
from contextlib import closing
from hashlib import sha256
import os
from dotenv import load_dotenv
import sys

# --- Загрузка конфигурации ---
env_path = os.path.join(sys.path[0], '.env.example1')
if not load_dotenv(env_path):
    load_dotenv()

# --- Конфигурация базы данных ---
DB_CONFIG = {
    'dbname': os.getenv("DBNAME"),
    'user': os.getenv("LOGIN"),
    'password': os.getenv("PASSWORD"),
    'host': os.getenv("HOST"),
    'port': os.getenv("PORT")
}

EARTH_RADIUS_MILES = 3958.8

def handle_client(conn):
    """
    Обрабатывает входящее соединение.
    Читает JSON-запрос, выполняет действие и отправляет JSON-ответ.
    
    Handles an incoming client connection.

    @requires: A valid socket connection `conn`.
    @modifies: The database state (if the action requires writing), the socket connection.
    @effects: Sends a JSON response to the client. Closes the connection.
    @raises: Exceptions on JSON parsing errors or database connection failures.
    @returns: None
    """
    # Ответ по умолчанию на случай непредвиденных ошибок
    response = {'status': 'error', 'message': 'Неизвестная ошибка на сервере.'}
    
    try:
        # 1. ЧТЕНИЕ ЗАПРОСА ОТ КЛИЕНТА
        request_data = conn.recv(4096).decode('utf-8')
        if not request_data:
            return

        # 2. ПАРСИНГ JSON-ЗАПРОСА
        try:
            request = json.loads(request_data)
        except json.JSONDecodeError:
            response = {'status': 'error', 'message': 'Некорректный формат JSON.'}
            raise # Переходим в finally для отправки ошибки

        action = request.get('action')
        params = request.get('params', {})
        response = {'status': 'error', 'message': f'Действие "{action}" не поддерживается.'}

        # 3. ВЫПОЛНЕНИЕ ЗАПРОСА К БАЗЕ ДАННЫХ
        with closing(psycopg2.connect(**DB_CONFIG)) as db_conn:
            with db_conn.cursor() as cursor:
                if action == 'find_markets':
                    response = handle_find_markets(cursor, params)
                elif action == 'find_market_by_name':
                    response = handle_find_market_by_name(cursor, params)
                elif action == 'find_market_by_fmid':
                    response = handle_find_market_by_fmid(cursor, params)
                elif action == 'get_market_details':
                    response = handle_get_market_details(cursor, params)
                elif action == 'add_review':
                    response = handle_add_review(cursor, params, db_conn)
                elif action == 'get_reviews_by_fmid':
                    response = handle_get_reviews_by_fmid(cursor, params)
                elif action == 'edit_review':
                    response = handle_edit_review(cursor, params, db_conn)
                elif action == 'remove_review':
                    response = handle_remove_review(cursor, params, db_conn)
                elif action == 'user_has_reviewed':
                    response = handle_user_has_reviewed(cursor, params)
                elif action == 'check_user_exists':
                    response = handle_check_user_exists(cursor, params)
                elif action == 'create_user':
                    response = handle_create_user(cursor, params, db_conn)
                elif action == 'verify_login':
                    response = handle_verify_login(cursor, params)

    except psycopg2.OperationalError as e:
        response = {'status': 'error', 'message': f'Ошибка подключения к базе данных: {str(e)}'}
    except Exception as e:
        # Логируем другие ошибки
        print(f"Ошибка при обработке: {e}")
    finally:
        # 4. ОТПРАВКА ОТВЕТА И ЗАКРЫТИЕ СОЕДИНЕНИЯ
        try:
            conn.sendall(json.dumps(response).encode('utf-8'))
            # print(f"Ответ отправлен: {response.get('status')}") # Раскомментируйте для отладки
        except Exception as e:
            print(f"Не удалось отправить ответ клиенту: {e}")
        
        conn.close()

# --- ОБРАБОТЧИКИ ДЕЙСТВИЙ ---

def handle_find_markets(cursor, params):
    """Поиск рынков по различным критериям."""
    """
    Searches for markets based on various criteria.

    @requires: A valid database cursor and a dictionary of filter parameters.
    @modifies: None (read-only operation).
    @effects: Executes an SQL query against the database.
    @raises: Exceptions on SQL execution errors.
    @returns: A dictionary with status and a list of found markets.
    """
    conditions = []
    args = []

    if params.get('city'):
        conditions.append("addresses.city ILIKE %s")
        args.append(f"%{params['city']}%")
    if params.get('state'):
        conditions.append("addresses.state ILIKE %s")
        args.append(f"%{params['state']}%")
    if params.get('zip_code'):
        conditions.append("addresses.zip = %s")
        args.append(params['zip_code'])

    if (params.get('latitude') and params.get('longitude') and params.get('max_distance')):
        lat, lon, dist = params['latitude'], params['longitude'], params['max_distance']
        dist_condition = f"""
            ACOS(SIN(RADIANS({lat}))*SIN(RADIANS(coordinates.latitude)) +
                 COS(RADIANS({lat}))*COS(RADIANS(coordinates.latitude)) *
                 COS(RADIANS(coordinates.longitude-{lon}))) * {EARTH_RADIUS_MILES} <= %s
        """
        conditions.append(dist_condition)
        args.append(dist)

    order_by = ""
    if params.get('sort_by_rating'):
        order_by = "ORDER BY avg_rating DESC" if params.get('sort_order', 'desc') == 'desc' else "ORDER BY avg_rating ASC"

    query = f"""
        SELECT markets.FMID, markets.MarketName,
               addresses.street, addresses.city, addresses.state, addresses.zip,
               (SELECT COALESCE(AVG(rating), 0) FROM reviews WHERE reviews.fmid = markets.FMID) as avg_rating
          FROM markets
          JOIN addresses ON markets.address_id=addresses.id
          JOIN coordinates ON markets.coordinate_id=coordinates.id
    """
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
        
    query += f" {order_by};"
    
    cursor.execute(query, args)
    rows = cursor.fetchall()
    
    # Убираем столбец avg_rating из результата перед отправкой клиенту
    markets = [row[:-1] for row in rows]
    
    return {'status': 'ok', 'data': markets}

# --- Поиск по части имени ---
def handle_find_market_by_name(cursor, params):
    """
    Специализированный поиск рынков по части названия.
    Не трогает основную функцию handle_find_markets.
    """
    """
    Searches for markets by a partial name match.

    @requires: A valid database cursor and a parameter `market_name_part`.
    @modifies: None (read-only operation).
    @effects: Executes an SQL query against the database.
    @raises: Exceptions on SQL execution errors.
    @returns: A dictionary with status and a list of found markets.
    """
    # Используем тот же универсальный механизм поиска, но с конкретным параметром
    conditions = []
    args = []

    # Только одно условие: поиск по названию
    if params.get('market_name_part'):
        conditions.append("markets.MarketName ILIKE %s")
        args.append(f"%{params['market_name_part']}%")

    # Если условий нет (например, параметр пустой), вернем пустой список
    if not conditions:
        return {'status': 'ok', 'data': []}

    # Запрос строится аналогично основному, но без лишних JOIN и условий
    query = """
        SELECT markets.FMID, markets.MarketName,
               addresses.street, addresses.city, addresses.state, addresses.zip,
               (SELECT COALESCE(AVG(rating), 0) FROM reviews WHERE reviews.fmid = markets.FMID) as avg_rating
          FROM markets
          JOIN addresses ON markets.address_id=addresses.id
          JOIN coordinates ON markets.coordinate_id=coordinates.id
         WHERE """ + " AND ".join(conditions) + ";"
    
    cursor.execute(query, args)
    rows = cursor.fetchall()
    
    markets = [row[:-1] for row in rows] # Убираем avg_rating из ответа

    return {'status': 'ok', 'data': markets}

# --- Поиск по FMID ---
def handle_find_market_by_fmid(cursor, params):
    """
    Выполняет поиск рынка по точному совпадению FMID.
    Эта функция не зависит от handle_find_markets.
    """
    """
    Finds a market by its unique FMID identifier.

    @requires: A valid database cursor and a parameter `fmid`.
    @modifies: None (read-only operation).
    @effects: Executes an SQL query against the database.
    @raises: Exceptions on SQL execution errors.
    @returns: A dictionary with status and market data or an empty list.
    """
    fmid = params.get('fmid')
    
    # Если параметр не передан, возвращаем ошибку
    if fmid is None:
        return {'status': 'error', 'message': 'Параметр FMID обязателен.'}

    # --- ИСПРАВЛЕНИЕ ТИПОВ ДАННЫХ ---
    # Используем явное приведение типа, чтобы сравнивать строку со строкой.
    # Это решает проблему, когда число сравнивается с текстовым полем.
    query = """
        SELECT markets.FMID, markets.MarketName,
               addresses.street, addresses.city, addresses.state, addresses.zip,
               (SELECT COALESCE(AVG(rating), 0) FROM reviews WHERE reviews.fmid = markets.FMID) as avg_rating
          FROM markets
          JOIN addresses ON markets.address_id=addresses.id
         WHERE markets.FMID = (%s);
    """
    
    try:
        cursor.execute(query, (fmid,))
        row = cursor.fetchone()
        
        if row:
            # Убираем столбец avg_rating из результата перед отправкой клиенту
            market_data = row[:-1]
            return {'status': 'ok', 'data': [market_data]} # Оборачиваем в список для совместимости
        else:
            return {'status': 'ok', 'data': []} # Рынок не найден
            
    except Exception as e:
        return {'status': 'error', 'message': f'Ошибка при поиске по FMID: {str(e)}'}
    
def handle_get_market_details(cursor, params):
    """Получение подробной информации о рынке."""
    """
     Retrieves comprehensive details for a specific market.

     @requires: A valid database cursor and a parameter `fmid`.
     @modifies: None (read-only operation).
     @effects: Executes a series of SQL queries to gather data from multiple tables.
               Converts data types (e.g., datetime) for JSON serialization.
     @raises: Exceptions on SQL execution or data type conversion errors.
     @returns: A dictionary with status and structured market data.
     """
    fmid = params.get('fmid')
    result = {}

    # --- ИСПРАВЛЕНИЕ ДЛЯ DATETIME ---
    # Импортируем datetime локально для проверки типа
    import datetime

    # 1. Основная информация о рынке (с обработкой даты)
    cursor.execute("SELECT * FROM markets WHERE FMID=%s;", (fmid,))
    market_row = cursor.fetchone()
    
    if market_row:
        # Преобразуем кортеж в список, чтобы можно было изменять значения
        market_list = list(market_row)
        
        # Проверяем поля, которые могут содержать дату (обычно последние поля).
        # В вашем случае проблема была в поле с датой/временем.
        # Мы проверим несколько последних элементов на всякий случай.
        for i in range(len(market_list)-1, len(market_list)-3, -1):
            if isinstance(market_list[i], (datetime.datetime, datetime.date)):
                market_list[i] = market_list[i].isoformat()
        
        result['market'] = market_list
    else:
        return {'status': 'error', 'message': f'Рынок с FMID {fmid} не найден.'}

    # 2. Адрес
    cursor.execute("SELECT * FROM addresses WHERE id=(SELECT address_id FROM markets WHERE FMID=%s);", (fmid,))
    address_row = cursor.fetchone()
    if address_row:
        result['address'] = list(address_row)

    # 3. Координаты
    cursor.execute("SELECT * FROM coordinates WHERE id=(SELECT coordinate_id FROM markets WHERE FMID=%s);", (fmid,))
    coords_row = cursor.fetchone()
    if coords_row:
        result['coords'] = list(coords_row)

    # 4. Социальные сети
    cursor.execute("SELECT * FROM social_links WHERE market_id=(SELECT id FROM markets WHERE FMID=%s);", (fmid,))
    social_row = cursor.fetchone()
    if social_row:
        result['social'] = {
            "Facebook": social_row[2] or "",
            "Twitter": social_row[3] or "",
            "YouTube": social_row[4] or "",
            "Other Media": social_row[5] or ""
        }

    # 5. Способы оплаты
    cursor.execute("SELECT * FROM payment_options WHERE market_id=(SELECT id FROM markets WHERE FMID=%s);", (fmid,))
    payment_row = cursor.fetchone()
    if payment_row:
        result['payment'] = {
            "Кредитные карты": payment_row[2],
            "Программа WIC": payment_row[3],
            "Денежные средства по программе WIC": payment_row[4],
            "Программа SFMNP": payment_row[5],
            "Программа SNAP": payment_row[6]
        }

    # 6. Продукты
    cursor.execute("SELECT * FROM products WHERE market_id=(SELECT id FROM markets WHERE FMID=%s);", (fmid,))
    products_row = cursor.fetchone()
    if products_row:
        columns = ['organic', 'baked_goods', 'cheese', 'crafts', 'flowers', 'eggs', 
                   'seafood', 'herbs', 'vegetables', 'honey', 'jams', 'maple', 
                   'meat', 'nursery', 'nuts', 'plants', 'poultry', 'prepared', 
                   'soap', 'trees', 'wine', 'coffee', 'beans', 'fruits', 
                   'grains', 'juices', 'mushrooms', 'pet_food', 'tofu', 
                   'wild_harvested']
        products_list = [col.replace("_", " ").capitalize() for col, val in zip(columns, products_row) if val]
        result['products'] = products_list

    # 7. Расписание (поля TEXT, проблем быть не должно)
    cursor.execute("""
        SELECT season_number, season_date, season_time 
          FROM operating_schedule 
         WHERE market_id=(SELECT id FROM markets WHERE FMID=%s) 
      ORDER BY season_number ASC;
    """, (fmid,))
    
    schedule_rows = cursor.fetchall()
    
    # Дополнительная защита: приводим все элементы строк к строкам (на случай NULL)
    safe_schedule = []
    for row in schedule_rows:
         safe_schedule.append({
             "Season Number": str(row[0]),
             "Season Date": str(row[1]),
             "Season Time": str(row[2])
         })
    
    if schedule_rows:
         result['schedule'] = safe_schedule

    return {'status': 'ok', 'data': result}


def handle_add_review(cursor, params, db_conn):
     """
     Adds a new review for a specific market to the database.

     @requires: A valid database cursor, a connection `db_conn`, and parameters `fmid`, `rating`, `comment`, `author`.
     @modifies: The `reviews` table in the database (inserts a record).
     @effects: Commits the transaction to the database.
     @raises: Exceptions on insertion or commit errors.
     @returns: A dictionary with status and a success message.
     """
     fmid = params.get('fmid')
     rating = params.get('rating')
     comment = params.get('comment')
     author = params.get('author')
     
     query = """
         INSERT INTO reviews (fmid, rating, comment, author) 
         VALUES (%s, %s, %s, %s);
     """
     cursor.execute(query, (fmid, rating, comment, author))
     db_conn.commit()
     
     return {'status': 'ok', 'message': 'Отзыв добавлен.'}


def handle_get_reviews_by_fmid(cursor, params):
     """
     Retrieves all reviews for a specific market.

     @requires: A valid database cursor and a parameter `fmid`.
     @modifies: None (read-only operation).
     @effects: Executes SQL queries to fetch reviews and author data from the `users` table.
     @raises: Exceptions on SQL execution errors.
     @returns: A dictionary with status and a list of reviews with author names.
     """
     fmid = params.get('fmid')
     
     query_reviews = """
         SELECT id, fmid, rating, comment, author 
           FROM reviews 
          WHERE fmid=%s;
     """
     cursor.execute(query_reviews, (fmid,))
     reviews_rows = cursor.fetchall()
     
     if not reviews_rows:
         return {'status': 'ok', 'data': []}
         
     authors = {row[4] for row in reviews_rows} # authors are at index 4
     
     query_users = """
         SELECT username, firstname, lastname 
           FROM users 
          WHERE username IN %s;
     """
     cursor.execute(query_users, (tuple(authors),))
     users_rows = cursor.fetchall()
     
     users_map = {row[0]: f"{row[1]} {row[2]}" for row in users_rows}
     
     reviews_data = []
     for row in reviews_rows:
         reviews_data.append({
             "id": row[0],
             "fmid": row[1],
             "rating": row[2],
             "comment": row[3],
             "fullname": users_map.get(row[4], "")
         })
         
     return {'status': 'ok', 'data': reviews_data}


def handle_edit_review(cursor, params, db_conn):
     """
      Edits an existing review's rating and comment text.

      @requires: A valid database cursor, a connection `db_conn`, and parameters to identify the review (`fmid`, `author`) and new data (`new_rating`, `new_comment`).
      @modifies: The `reviews` table in the database (updates a record).
      @effects: Commits the transaction to the database. Checks `cursor.rowcount` to validate permissions.
      @raises: Exceptions on update or commit errors.
      @returns: A dictionary with status and a success or access-denied message.
      """
     fmid = params.get('fmid')
     new_rating = params.get('new_rating')
     new_comment = params.get('new_comment')
     author = params.get('author')
     
     query = """
         UPDATE reviews 
            SET rating=%s,
                comment=%s 
          WHERE fmid=%s AND author=%s;
     """
     cursor.execute(query, (new_rating, new_comment, fmid, author))
     
     if cursor.rowcount == 0:
         return {'status': 'error', 'message': 'Отзыв не найден или нет прав на редактирование.'}
         
     db_conn.commit()
     
     return {'status': 'ok', 'message': 'Отзыв обновлён.'}


def handle_remove_review(cursor, params, db_conn):
     """
      Removes a review from the database.

      @requires: A valid database cursor, a connection `db_conn`, and parameters to identify the review (`fmid`, `author`).
      @modifies: The `reviews` table in the database (deletes a record).
      @effects: Commits the transaction to the database. Checks `cursor.rowcount` to validate permissions.
      @raises: Exceptions on deletion or commit errors.
      @returns: A dictionary with status and a success or access-denied message.
      """
     fmid = params.get('fmid')
     author = params.get('author')
     
     query = "DELETE FROM reviews WHERE fmid=%s AND author=%s;"
     cursor.execute(query, (fmid, author))
     
     if cursor.rowcount == 0:
          return {'status': 'error', 'message': 'Отзыв не найден или нет прав на удаление.'}
          
     db_conn.commit()
     
     return {'status': 'ok', 'message': 'Отзыв удалён.'}


def handle_user_has_reviewed(cursor, params):
     """
     Checks if a user has already reviewed a specific market.

     @requires: A valid database cursor and parameters `fmid`, `author`.
     @modifies: None (read-only operation).
     @effects: Executes an SQL query to count records in the `reviews` table.
     @raises: Exceptions on SQL execution errors.
     @returns: A dictionary with status and a boolean indicating if a review exists.
     """ 
     fmid = params.get('fmid')
     author = params.get('author')
     
     query = "SELECT COUNT(*) FROM reviews WHERE fmid=%s AND author=%s;"
     cursor.execute(query, (fmid, author))
     count = cursor.fetchone()[0]
     
     return {'status': 'ok', 'has_reviewed': count > 0}


def handle_check_user_exists(cursor, params):
     """
     Checks if a user exists in the database.

     @requires: A valid database cursor and a parameter `username`.
     @modifies: None (read-only operation).
     @effects: Executes an SQL query to count records in the `users` table.
     @raises: Exceptions on SQL execution errors.
     @returns: A dictionary with status and a boolean indicating if the user exists.
     """
     username = params.get('username')
     
     query = "SELECT COUNT(*) FROM users WHERE username=%s;"
     cursor.execute(query, (username,))
     count = cursor.fetchone()[0]
     
     return {'status': 'ok', 'exists': count > 0}


def handle_create_user(cursor, params, db_conn):
     """
     Creates a new user account in the database.

     @requires: A valid database cursor, a connection `db_conn`, and registration parameters (`username`, `password`, `firstname`, `lastname`).
               The password is hashed inside the function.
     @modifies: The `users` table in the database (inserts a record).
     @effects: Commits the transaction to the database. Handles unique username violations (`UniqueViolation`).
     @raises: Exceptions on insertion or commit errors (except for duplicate username).
     @returns: A dictionary with status and a success or duplicate-user error message.
     """
     username = params.get('username')
     password_hash = sha256(params['password'].encode()).hexdigest()
     firstname = params.get('firstname')
     lastname = params.get('lastname')
     
     query = """
         INSERT INTO users (username, password_hash, firstname, lastname) 
         VALUES (%s, %s, %s, %s);
     """
     try:
         cursor.execute(query, (username, password_hash, firstname, lastname))
         db_conn.commit()
         return {'status': 'ok', 'message': 'Пользователь создан.'}
     except psycopg2.errors.UniqueViolation:
         return {'status': 'error', 'message': 'Пользователь с таким именем уже существует.'}


def handle_verify_login(cursor, params):
     """
      Verifies user login credentials.

      @requires: A valid database cursor and login parameters (`username`, `password`).
                The password is hashed inside the function for comparison with the stored hash.
      @modifies: None (read-only operation).
      @effects: Executes an SQL query to fetch the user's password hash from the `users` table.
      @raises: Exceptions on SQL execution errors.
      @returns: A dictionary with authentication status (`authenticated`), full name, or an error message.
     """
     username = params.get('username')
     password_hash_provided = sha256(params['password'].encode()).hexdigest()
     
     query = """
         SELECT password_hash, firstname, lastname 
           FROM users 
          WHERE username=%s;
     """
     cursor.execute(query, (username,))
     row = cursor.fetchone()
     
     if not row:
         return {'status': 'error', 'message': 'Пользователь не найден.'}
         
     stored_hash, firstname, lastname = row
     
     if stored_hash == password_hash_provided:
         return {'status': 'ok', 
                 "authenticated": True,
                 "fullname": f"{firstname} {lastname}"}
     else:
         return {'status': 'ok', 
                 "authenticated": False,
                 "message": "Неверный пароль."}
                 
# --- Запуск сервера ---
def start_server(host, port):
   """
   Starts the TCP server to listen for incoming connections.

   @requires: Host (`host`) and port (`port`) parameters for socket binding.
   @modifies: Creates a socket, binds it to an address, and puts it into listening mode. Accepts incoming connections.
   @effects: Prints status messages to the console. Calls the client handler function for each connection.
   @raises: Exceptions on socket creation or binding errors.
   @returns: None. The function runs indefinitely until interrupted externally.
   """
   print(f"Попытка запуска сервера на {host}:{port}...")
   try:
       with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
           s.bind((host, port))
           s.listen()
           print(f"Сервер успешно запущен на {host}:{port}")
           while True:
               conn, addr = s.accept()
               print(f"Новое подключение от {addr}")
               handle_client(conn)
   except Exception as e:
       print(f"Не удалось запустить сервер: {str(e)}")
       print("Проверьте настройки HOST_SERVER и PORT_SERVER в .env файле.")

if __name__ == "__main__":
   start_server(os.getenv("HOST_SERVER"), int(os.getenv("PORT_SERVER")))