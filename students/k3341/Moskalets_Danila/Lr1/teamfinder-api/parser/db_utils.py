import psycopg2
from psycopg2.extras import execute_values

DB_CONFIG = {
    'dbname': 'parser_data',  # В Docker будет другая БД
    'user': 'postgres',
    'password': 'postgres',
    'host': 'parser_postgres',  # В Docker имя сервиса
    'port': '5432'
}

def init_db():
    """Создает таблицы для парсинга, если их нет"""
    conn = None
    cur = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS parsed_content (
                id SERIAL PRIMARY KEY,
                source_url TEXT UNIQUE,
                title TEXT,
                content_summary TEXT,
                parsed_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS skills (
                id BIGSERIAL PRIMARY KEY,
                name VARCHAR(128) UNIQUE,
                category VARCHAR(64)
            )
        """)
        
        conn.commit()
        print("База данных инициализирована")
    except Exception as e:
        print(f"Ошибка инициализации БД: {e}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def save_parsed_data(source_url, title, content_summary):
    """Сохраняет спарсенные данные в БД"""
    conn = None
    cur = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO parsed_content (source_url, title, content_summary)
            VALUES (%s, %s, %s)
            ON CONFLICT (source_url) DO UPDATE
            SET title = EXCLUDED.title, 
                content_summary = EXCLUDED.content_summary,
                parsed_at = NOW()
        """, (source_url, title[:200], content_summary[:500]))
        
        conn.commit()
    except Exception as e:
        print(f"Ошибка сохранения данных: {e}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def add_skill_if_not_exists(skill_name, category):
    """Добавляет навык в таблицу skills"""
    if not skill_name or skill_name == "Unknown" or len(skill_name) < 2:
        return
    
    conn = None
    cur = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO skills (name, category)
            VALUES (%s, %s)
            ON CONFLICT (name) DO NOTHING
        """, (skill_name[:120], category))
        conn.commit()
    except Exception as e:
        print(f"Ошибка добавления навыка {skill_name}: {e}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def clear_tables():
    """Очищает таблицы перед новым запуском"""
    conn = None
    cur = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        cur.execute("DELETE FROM parsed_content")
        cur.execute("DELETE FROM skills")
        
        conn.commit()
        print("Таблицы очищены")
    except Exception as e:
        print(f"Ошибка очистки таблиц: {e}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def get_stats():
    """Получает статистику по таблицам"""
    conn = None
    cur = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(*) FROM parsed_content")
        parsed_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM skills")
        skills_count = cur.fetchone()[0]
        
        print(f"Статистика: {parsed_count} записей в parsed_content, {skills_count} навыков в skills")
        return parsed_count, skills_count
    except Exception as e:
        print(f"Ошибка получения статистики: {e}")
        return 0, 0
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()