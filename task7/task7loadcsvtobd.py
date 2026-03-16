import csv
import psycopg2
from datetime import datetime
import re

# Настройки подключения к PostgreSQL
DB_NAME = 'farmers_db'
DB_USER = 'sasha'  # Используем пользователя с правами создания БД.
DB_PASSWORD = '1973'  # Пароль пользователя
DB_HOST = 'localhost'
DB_PORT = '5433'

# Регулярное выражение для извлечения времени
TIME_PATTERN = r'\d+:\d+\s*(?:AM|PM)?'

# Функция для преобразования времени
def parse_time(time_string):
    '''
    Extract and format time from a string representation.
    @requires: time_string ϵ string
    @modifies: None
    @effects: Parses the time from a string like "HH:mm AM/PM" and converts it to "HH:MM:SS".
    @raises: None
    @returns: Formatted time string or None if no valid time was found.
    '''
    match = re.search(TIME_PATTERN, time_string)
    if match:
        raw_time = match.group().strip()
        # Преобразуем время в формат HH:MI:SS
        parsed_time = datetime.strptime(raw_time, "%I:%M %p").strftime("%H:%M:%S")
        return parsed_time
    return None

# Подключаемся сначала к postgres, чтобы проверить наличие нужной базы данных
admin_conn = psycopg2.connect(
    dbname="postgres",
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT
)
admin_conn.autocommit = True
admin_cur = admin_conn.cursor()

# Проверяем существование базы данных
check_db_query = f"""
SELECT datname FROM pg_database WHERE datname = '{DB_NAME}';
"""
admin_cur.execute(check_db_query)
db_exists = bool(admin_cur.fetchall())

if not db_exists:
    print(f"База данных {DB_NAME} не найдена. Создаем новую...")
    create_db_query = f"CREATE DATABASE {DB_NAME};"
    admin_cur.execute(create_db_query)
else:
    print(f"База данных {DB_NAME} уже существует.")

# Теперь подключаемся непосредственно к нашей базе данных
conn = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT
)
cur = conn.cursor()

# Прежде чем создавать таблицы, удалим старые версии таблиц, если они существуют
drop_tables_sql = '''
DROP TABLE IF EXISTS reviews CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS markets CASCADE;
DROP TABLE IF EXISTS addresses CASCADE;
DROP TABLE IF EXISTS coordinates CASCADE;
DROP TABLE IF EXISTS operating_schedule CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS social_links CASCADE;
DROP TABLE IF EXISTS payment_options CASCADE;
'''
cur.execute(drop_tables_sql)
conn.commit()

# Создание необходимых таблиц, если они не существуют
create_tables_sql = '''
-- Таблица для пользователей
CREATE TABLE IF NOT EXISTS users (
    username VARCHAR(255) PRIMARY KEY,
    password_hash TEXT,
    firstname TEXT,
    lastname TEXT
);

-- Таблица для адресов
CREATE TABLE IF NOT EXISTS addresses (
    id SERIAL PRIMARY KEY,
    street TEXT,
    city TEXT,
    county TEXT,
    state TEXT,
    zip TEXT
);

-- Таблица для географических координат
CREATE TABLE IF NOT EXISTS coordinates (
    id SERIAL PRIMARY KEY,
    latitude FLOAT,
    longitude FLOAT
);

-- Таблица для рынков (должна быть уникальной по полю FMID)
CREATE TABLE IF NOT EXISTS markets (
    id SERIAL PRIMARY KEY,
    FMID BIGINT UNIQUE, -- Тип поля FMID остался BIGINT
    MarketName TEXT,
    website TEXT,
    address_id INT REFERENCES addresses(id),
    coordinate_id INT REFERENCES coordinates(id),
    update_time TIMESTAMP   -- Теперь берем значение из файла
);

-- Таблица для графиков работы рынков
CREATE TABLE IF NOT EXISTS operating_schedule (
    id SERIAL PRIMARY KEY,
    market_id INT REFERENCES markets(id),
    season_number INT,
    season_date TEXT,          -- Здесь сохранятся оригинальные строки SeasonXDate
    season_time TEXT           -- Здесь сохранятся оригинальные строки SeasonXTimes
    --start_date DATE,
    --start_time TIME,
    --end_date DATE,
    --end_time TIME
);

-- Таблица для продуктов, продаваемых на рынках
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    market_id INT REFERENCES markets(id),
    organic BOOLEAN,
    baked_goods BOOLEAN,
    cheese BOOLEAN,
    crafts BOOLEAN,
    flowers BOOLEAN,
    eggs BOOLEAN,
    seafood BOOLEAN,
    herbs BOOLEAN,
    vegetables BOOLEAN,
    honey BOOLEAN,
    jams BOOLEAN,
    maple BOOLEAN,
    meat BOOLEAN,
    nursery BOOLEAN,
    nuts BOOLEAN,
    plants BOOLEAN,
    poultry BOOLEAN,
    prepared BOOLEAN,
    soap BOOLEAN,
    trees BOOLEAN,
    wine BOOLEAN,
    coffee BOOLEAN,
    beans BOOLEAN,
    fruits BOOLEAN,
    grains BOOLEAN,
    juices BOOLEAN,
    mushrooms BOOLEAN,
    pet_food BOOLEAN,
    tofu BOOLEAN,
    wild_harvested BOOLEAN
);

-- Таблица для отзывов
CREATE TABLE IF NOT EXISTS reviews (
    id SERIAL PRIMARY KEY,
    fmid BIGINT REFERENCES markets(FMID), -- Внешний ключ теперь BIGINT
    rating INTEGER CHECK(rating >= 1 AND rating <= 5),
    comment TEXT,
    author VARCHAR(255) REFERENCES users(username)
);

-- Таблица для ссылок на соцсети
CREATE TABLE IF NOT EXISTS social_links (
    id SERIAL PRIMARY KEY,
    market_id INT REFERENCES markets(id),
    facebook_url TEXT,
    twitter_url TEXT,
    youtube_url TEXT,
    other_media_url TEXT
);

-- Таблица для платежных опций
CREATE TABLE IF NOT EXISTS payment_options (
    id SERIAL PRIMARY KEY,
    market_id INT REFERENCES markets(id),
    credit BOOLEAN,
    wic BOOLEAN,
    wic_cash BOOLEAN,
    sfmnp BOOLEAN,
    snap BOOLEAN
);
'''

# Выполняем команды создания таблиц
cur.execute(create_tables_sql)
conn.commit()

# Вспомогательные функции для вставки данных
def insert_address(data):
    '''
    Insert a new address record into the addresses table.
    @requires: data ϵ dict
    @modifies: Database tables are modified.
    @effects: Inserts a new address into the addresses table.
    @raises: None
    @returns: ID of newly inserted address.
    '''
    """Вставка адреса в таблицу addresses."""
    columns = ', '.join(data.keys())
    placeholders = ', '.join(['%s'] * len(data))
    values = tuple(data.values())
    query = f"INSERT INTO addresses ({columns}) VALUES ({placeholders}) RETURNING id;"
    cur.execute(query, values)
    conn.commit()
    return cur.fetchone()[0]

def insert_coordinates(data):
    '''
    Insert a new coordinate record into the coordinates table.
    @requires: data ϵ dict
    @modifies: Database tables are modified.
    @effects: Inserts a new pair of coordinates into the coordinates table.
    @raises: None
    @returns: ID of newly inserted coordinates.
    '''
    """Вставка координат в таблицу coordinates."""
    columns = ', '.join(data.keys())
    placeholders = ', '.join(['%s'] * len(data))
    values = tuple(data.values())
    query = f"INSERT INTO coordinates ({columns}) VALUES ({placeholders}) RETURNING id;"
    cur.execute(query, values)
    conn.commit()
    return cur.fetchone()[0]

def insert_operating_schedule(data):
    '''
    Insert a new operating schedule record into the operating_schedule table.
    @requires: data ϵ dict
    @modifies: Database tables are modified.
    @effects: Inserts a new schedule entry into the operating_schedule table.
    @raises: None
    @returns: None
    '''
    """Вставка графика работы в таблицу operating_schedule."""
    columns = ', '.join(data.keys())
    placeholders = ', '.join(['%s'] * len(data))
    values = tuple(data.values())
    query = f"INSERT INTO operating_schedule ({columns}) VALUES ({placeholders});"
    cur.execute(query, values)
    conn.commit()

def insert_payment_options(data):
    '''
    Insert payment options for a market into the payment_options table.
    @requires: data ϵ dict
    @modifies: Database tables are modified.
    @effects: Inserts payment methods used at a market into the payment_options table.
    @raises: None
    @returns: None
    '''
    """Вставка платёжных опций в таблицу payment_options."""
    columns = ', '.join(data.keys())
    placeholders = ', '.join(['%s'] * len(data))
    values = tuple(data.values())
    query = f"INSERT INTO payment_options ({columns}) VALUES ({placeholders});"
    cur.execute(query, values)
    conn.commit()

def insert_products(data):
    '''
    Insert product availability for a market into the products table.
    @requires: data ϵ dict
    @modifies: Database tables are modified.
    @effects: Inserts the types of products sold at a market into the products table.
    @raises: None
    @returns: None
    '''
    """Вставка продуктов в таблицу products."""
    columns = ', '.join(data.keys())
    placeholders = ', '.join(['%s'] * len(data))
    values = tuple(data.values())
    query = f"INSERT INTO products ({columns}) VALUES ({placeholders});"
    cur.execute(query, values)
    conn.commit()

def insert_market(data):
    '''
    Insert a new market record into the markets table.
    @requires: data ϵ dict
    @modifies: Database tables are modified.
    @effects: Inserts a new market into the markets table.
    @raises: None
    @returns: ID of newly inserted market.
    '''
    """Вставка информации о рынке в таблицу markets."""
    columns = ', '.join(data.keys())
    placeholders = ', '.join(['%s'] * len(data))
    values = tuple(data.values())
    query = f"INSERT INTO markets ({columns}) VALUES ({placeholders}) RETURNING id;"
    cur.execute(query, values)
    conn.commit()
    return cur.fetchone()[0]

def insert_social_links(data):
    '''
    Insert social media links for a market into the social_links table.
    @requires: data ϵ dict
    @modifies: Database tables are modified.
    @effects: Inserts social media URLs for a market into the social_links table.
    @raises: None
    @returns: None
    '''
    """Вставка ссылок на соцсети в таблицу social_links."""
    columns = ', '.join(data.keys())
    placeholders = ', '.join(['%s'] * len(data))
    values = tuple(data.values())
    query = f"INSERT INTO social_links ({columns}) VALUES ({placeholders});"
    cur.execute(query, values)
    conn.commit()

# Функция для вставки пользователей
def insert_user(data):
    '''
    Insert a new user record into the users table.
    @requires: data ϵ dict
    @modifies: Database tables are modified.
    @effects: Inserts a new user into the users table.
    @raises: None
    @returns: None
    '''
    """Вставка пользователя в таблицу users."""
    columns = ', '.join(data.keys())
    placeholders = ', '.join(['%s'] * len(data))
    values = tuple(data.values())
    query = f"INSERT INTO users ({columns}) VALUES ({placeholders}) ON CONFLICT DO NOTHING;"
    cur.execute(query, values)
    conn.commit()

# Функция для вставки отзывов
def insert_review(data):
    '''
    Insert a new review record into the reviews table.
    @requires: data ϵ dict
    @modifies: Database tables are modified.
    @effects: Inserts a new review into the reviews table only if the referenced market exists.
    @raises: None
    @returns: None
    '''
    """Вставка отзыва в таблицу reviews."""
    fmid = int(data['fmid'])
    check_query = f"SELECT COUNT(*) FROM markets WHERE FMID=%s;"
    cur.execute(check_query, (fmid,))
    count = cur.fetchone()[0]
    
    if count > 0:
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        values = tuple(data.values())
        query = f"INSERT INTO reviews ({columns}) VALUES ({placeholders});"
        cur.execute(query, values)
        conn.commit()
    else:
        print(f"Пропущен отзыв для несуществующего FMID={fmid}.")

# Функция для поиска максимального FMID
def find_max_fmid():
    '''
    Find the maximum FMID value currently present in the markets table.
    @requires: None
    @modifies: None
    @effects: Performs a database query to retrieve the largest FMID value.
    @raises: None
    @returns: Maximum FMID value or zero if the table is empty.
    '''
    select_max_fmid_query = """
    SELECT MAX(FMID) FROM markets;
    """
    cur.execute(select_max_fmid_query)
    result = cur.fetchone()
    max_fmid = result[0] or 0  # Возвращается либо максимальный FMID, либо 0, если таблица пуста
    return max_fmid

# Логика обработки файла Export.csv
def process_export_csv(filename):
    '''
    Process the export CSV file, extracting and inserting market-related data into the database.
    @requires: filename ϵ string
    @modifies: Database tables are populated with market data.
    @effects: Reads the CSV file, processes each line, extracts and normalizes data before insertion.
    @raises: None
    @returns: None
    '''
    markets_with_fmid = []  # Рынки с установленным FMID
    markets_without_fmid = []  # Рынки без установленного FMID

    with open(filename, mode='r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
    
        for row in reader:
            cleaned_row = {k: v.strip() if isinstance(v, str) else v for k, v in row.items()}
            
            # Разделяем рынки по наличию FMID
            if cleaned_row.get('FMID'):
                markets_with_fmid.append(cleaned_row)
            else:
                markets_without_fmid.append(cleaned_row)

    # Первым делом вносим рынки с уже известными FMID
    for market_data in markets_with_fmid:
        handle_market(market_data)

    # Далее определяем новое значение FMID для остальных рынков
    current_max_fmid = find_max_fmid()

    # Пройдем по оставшимся рынкам и назначим каждому уникальный FMID
    for idx, market_data in enumerate(markets_without_fmid):
        new_fmid = current_max_fmid + idx + 1
        market_data['FMID'] = new_fmid
        handle_market(market_data)

# Основной обработчик рынка
def handle_market(row):
    '''
    Handle processing of a single market record, preparing and inserting data into appropriate tables.
    @requires: row ϵ dict
    @modifies: Database tables are populated with processed market data.
    @effects: Processes and inserts address, coordinates, schedules, products, payments, and social links for a market.
    @raises: None
    @returns: None
    '''
    # Начнём с адреса
    address_id = insert_address({
        'street': row.pop('street'),
        'city': row.pop('city'),
        'county': row.pop('County'),
        'state': row.pop('State'),
        'zip': row.pop('zip')
    })
    
    # Координаты
    x_value = row.get('x', '')
    y_value = row.get('y', '')
    if x_value and y_value:
        coordinate_id = insert_coordinates({
            'latitude': float(x_value),
            'longitude': float(y_value)
        })
    else:
        coordinate_id = None
    
    # Графики работы
    schedules = []
    for i in range(1, 5):  # До четырёх сезонов
        date_field = f'Season{i}Date'
        time_field = f'Season{i}Time'
        
        if date_field in row and time_field in row:
          
            season_date = row.pop(date_field)
            season_time = row.pop(time_field)
            if season_date!="":   
              # Сохраняем оригинальные строки в соответствующих полях
              schedules.append({
              'market_id': None,  # Присвоим позже
              'season_number': i,
              'season_date': season_date,
              'season_time': season_time
              })
            '''
            try:
                parts = full_season_date.split('-')
                start_date_str = parts[0].strip()
                end_date_str = parts[-1].strip()
                
                # Приведение дат к нужному формату (%Y-%m-%d)
                start_date_obj = datetime.strptime(start_date_str, '%d/%m/%Y').strftime('%Y-%m-%d')
                end_date_obj = datetime.strptime(end_date_str, '%d/%m/%Y').strftime('%Y-%m-%d')
                
                # Преобразование времени в формат HH:MI:SS
                start_time = parse_time(full_season_time)
                end_time = parse_time(full_season_time)
                
                schedules.append({
                    'market_id': None,  # Будем указывать позже
                    'season_number': i,
                    'start_date': start_date_obj,
                    'start_time': start_time,
                    'end_date': end_date_obj,
                    'end_time': end_time
                })
            except ValueError:
                if full_season_date!="":
                  print(f'{i} {full_season_date} {full_season_time}')
                continue  # Игнорируем некорректные данные
            '''
    # Дата обновления
    update_time_raw = row.pop('updateTime', None)
    if update_time_raw is not None:
        try:
            dt_object = datetime.strptime(update_time_raw, "%m/%d/%Y %I:%M:%S %p")
            update_time_formatted = dt_object.strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            print(f"Ошибка при обработке updateTime: {e}")
            update_time_formatted = None
    else:
        update_time_formatted = None
    
    # Подготовили основную информацию о рынке
    market_data = {
        'FMID': int(row.pop('FMID')) if row.get('FMID') else None,  # Проверяем наличие FMID
        'MarketName': row.pop('MarketName'),
        'website': row.pop('Website'),
        'address_id': address_id,
        'coordinate_id': coordinate_id,
        'update_time': update_time_formatted
    }
    
    # Вносим основной объект рынка
    market_id = insert_market(market_data)
    
    # Устанавливаем привязку ко вновь созданному рынку
    for schedule in schedules:
        schedule['market_id'] = market_id
        insert_operating_schedule(schedule)
    
    # Продукты
    product_columns = [
        'Organic','Baked_goods', 'Cheese', 'Crafts', 'Flowers', 'Eggs',
        'Seafood', 'Herbs', 'Vegetables', 'Honey', 'Jams',
        'Maple', 'Meat', 'Nursery', 'Nuts', 'Plants', 'Poultry',
        'Prepared', 'Soap', 'Trees', 'Wine', 'Coffee', 'Beans',
        'Fruits', 'Grains', 'Juices', 'Mushrooms', 'Pet_food',
        'Tofu', 'Wild_harvested'
    ]

    product_values = {}
    for col in product_columns:
        if col in row:  
            product_values[col] = True if row.pop(col) == 'Y' else False
        else:
            product_values[col] = False  # По умолчанию False, если поле отсутствует
    
    product_values['market_id'] = market_id
    insert_products(product_values)
    
    # Платежные опции
    payment_data = {
        'market_id': market_id,
        'credit': True if row.pop('Credit') == 'Y' else False,
        'wic': True if row.pop('WIC') == 'Y' else False,
        'wic_cash': True if row.pop('WICcash') == 'Y' else False,
        'sfmnp': True if row.pop('SFMNP') == 'Y' else False,
        'snap': True if row.pop('SNAP') == 'Y' else False
    }
    insert_payment_options(payment_data)
    
    # Социальные сети
    social_data = {
        'market_id': market_id,
        'facebook_url': row.pop('Facebook'),
        'twitter_url': row.pop('Twitter'),
        'youtube_url': row.pop('Youtube'),
        'other_media_url': row.pop('OtherMedia')
    }
    insert_social_links(social_data)

# Логика обработки всех файлов
def process_csv_file(filename):
    '''
    Process different types of CSV files and populate the database accordingly.
    @requires: filename ϵ string
    @modifies: Database tables are populated with data from CSV files.
    @effects: Handles different types of CSV files (export, users, reviews) and calls respective handlers.
    @raises: None
    @returns: None
    '''
    if filename.endswith('Export.csv'):       # Сначала обрабатываем рынки
        process_export_csv(filename)
    elif filename.endswith('users.csv'):      # Потом добавляем пользователей
        with open(filename, mode='r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)
            for row in reader:
                cleaned_row = {k: v.strip() if isinstance(v, str) else v for k, v in row.items()}
                data = {
                    'username': cleaned_row.pop('username'),
                    'password_hash': cleaned_row.pop('password_hash'),
                    'firstname': cleaned_row.pop('firstname'),
                    'lastname': cleaned_row.pop('lastname')
                }
                insert_user(data)
    elif filename.endswith('reviews.csv'):    # И только потом идут отзывы
        with open(filename, mode='r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)
            for row in reader:
                cleaned_row = {k: v.strip() if isinstance(v, str) else v for k, v in row.items()}
                
                # Проверяем, заполнено ли поле fmid
                if not cleaned_row.get('fmid'):
                    continue  # Пропускаем строку, если fmid пустой
                
                data = {
                    'fmid': int(cleaned_row.pop('fmid')),
                    'rating': int(cleaned_row.pop('rating')),
                    'comment': cleaned_row.pop('comment'),
                    'author': cleaned_row.pop('author')
                }
                
                # Вставляем отзыв только если соответствующий FMID существует в таблице markets
                insert_review(data)

# Перебор всех файлов
filenames = ['Export.csv', 'users.csv', 'reviews.csv']
for filename in filenames:
    process_csv_file(filename)

print("Все данные успешно загружены в базу данных.")

# Закрываем соединение с базой данных
cur.close()
conn.close()
admin_cur.close()
admin_conn.close()