import psycopg2
from db_utils import DB_CONFIG

def test_connection():
    """Тест подключения к БД"""
    print("=" * 50)
    print("Тест подключения к базе данных")
    print("=" * 50)
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Проверяем версию PostgreSQL
        cur.execute("SELECT version();")
        version = cur.fetchone()
        print(f"PostgreSQL версия: {version[0][:50]}...")
        
        # Проверяем список таблиц
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cur.fetchall()
        
        print(f"\n Таблицы в базе данных ({len(tables)}):")
        for table in tables[:10]:
            print(f"   - {table[0]}")
        
        cur.close()
        conn.close()
        
        print("\n Подключение к БД успешно!")
        return True
        
    except Exception as e:
        print(f" Ошибка подключения: {e}")
        print("\n Проверьте:")
        print("   1. Запущен ли Docker контейнер: docker ps")
        print("   2. Правильный ли порт: 5439")
        print("   3. Правильные ли учетные данные: postgres/password")
        return False

def test_parsed_content_table():
    """Тест таблицы parsed_content"""
    print("\n" + "=" * 50)
    print("Тест таблицы parsed_content")
    print("=" * 50)
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Проверяем структуру таблицы
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'parsed_content'
            ORDER BY ordinal_position;
        """)
        columns = cur.fetchall()
        
        print("Структура таблицы:")
        for col in columns:
            print(f"   - {col[0]}: {col[1]}")
        
        # Считаем записи
        cur.execute("SELECT COUNT(*) FROM parsed_content")
        count = cur.fetchone()[0]
        print(f"\nКоличество записей: {count}")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Ошибка: {e}")

def test_skills_table():
    """Тест таблицы skills"""
    print("\n" + "=" * 50)
    print("Тест таблицы skills")
    print("=" * 50)
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Проверяем структуру таблицы
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'skills'
            ORDER BY ordinal_position;
        """)
        columns = cur.fetchall()
        
        print("Структура таблицы:")
        for col in columns:
            print(f"   - {col[0]}: {col[1]}")
        
        # Считаем записи
        cur.execute("SELECT COUNT(*) FROM skills")
        count = cur.fetchone()[0]
        print(f"\nКоличество записей: {count}")
        
        # Показываем несколько навыков
        if count > 0:
            cur.execute("SELECT name, category FROM skills LIMIT 5")
            skills = cur.fetchall()
            print("\nПримеры навыков:")
            for skill in skills:
                print(f"   - {skill[0]} ({skill[1]})")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    if test_connection():
        test_parsed_content_table()
        test_skills_table()
    else:
        print("\nНевозможно продолжить тесты из-за ошибки подключения")