import psycopg2
from psycopg2 import sql
import os
from dotenv import load_dotenv
import sys

#сначала берем параметры базы из файла .env.example 
env_path = os.path.join(sys.path[0], '.env.example')

if load_dotenv(env_path)==False:
   load_dotenv()
   
# Настройки подключения к базе данных

DB_NAME = os.getenv("DBNAME")
DB_USER = os.getenv("LOGIN")
DB_PASSWORD = os.getenv("PASSWORD")
DB_HOST = os.getenv("HOST")
DB_PORT = os.getenv("PORT")

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
    
try:
    # Подключение к PostgreSQL
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    cursor = conn.cursor()
    print("✅ Подключение к базе данных установлено.")

    # Создание таблицы пользователей
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            login VARCHAR(50) UNIQUE NOT NULL,
            passwordhash VARCHAR(255) NOT NULL
        );
    """)

    # Создание таблицы доноров
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS donors (
            id SERIAL PRIMARY KEY,
            sex CHAR(1) CHECK (sex IN ('М', 'Ж')),
            birth_date DATE,
            blood_group VARCHAR(3) CHECK (blood_group IN ('O(I)', 'A(II)', 'B(III)', 'AB(IV)')),
            rh_factor CHAR(1) CHECK (rh_factor IN ('+', '-')),
            children BOOLEAN,
            height INT,
            weight INT,
            nationality VARCHAR(50),
            hair_color VARCHAR(30),
            hair_type VARCHAR(30),
            eye_shape VARCHAR(30),
            eye_color VARCHAR(30),
            nose_shape VARCHAR(30),
            face_shape VARCHAR(30),
            forehead_shape VARCHAR(30),
            body_type VARCHAR(30),
            clothing_size VARCHAR(10),
            shoe_size VARCHAR(10),
            education VARCHAR(100),
            profession VARCHAR(100),
            stigma BOOLEAN          
        );
    """)

    # Создание таблицы биологических материалов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS biological_materials (
            id SERIAL PRIMARY KEY,
            id_donor INT REFERENCES donors(id) ON DELETE CASCADE,
            name_bio VARCHAR(100),
            date_i DATE,
            date_end DATE,
            material_type VARCHAR(50),
            quantity NUMERIC(10,2),
            unit VARCHAR(20),
            genetic_passport BOOLEAN
        );
    """)

    # Применение изменений
    conn.commit()
    print("✅ Таблицы успешно созданы.")

except Exception as e:
    print(f"❌ Ошибка: {e}")
finally:
    if conn:
        cursor.close()
        conn.close()
        print("🔌 Соединение с базой данных закрыто.")