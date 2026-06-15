import subprocess
import time
import sys

def run_parser(script_name):
    """Запускает один парсер и возвращает время выполнения"""
    print(f"\n{'='*70}")
    print(f"Запуск {script_name}")
    print('='*70)
    
    start = time.time()
    
    try:
        result = subprocess.run(
            [sys.executable, script_name], 
            capture_output=True, 
            text=True,
            timeout=60  # 60 секунд таймаут
        )
        
        print(result.stdout)
        
        if result.stderr:
            print(" Предупреждения/Ошибки:")
            print(result.stderr[:500])  # Показываем только первые 500 символов
            
    except subprocess.TimeoutExpired:
        print(f" {script_name} превысил лимит времени (60 сек)")
        return None
    except Exception as e:
        print(f" Ошибка запуска {script_name}: {e}")
        return None
    
    end = time.time()
    elapsed = end - start
    
    print(f"\n Время выполнения {script_name}: {elapsed:.2f} сек")
    return elapsed

def main():
    print("\n" + "="*70)
    print("ЗАПУСК ВСЕХ ТРЕХ ПАРСЕРОВ")
    print("="*70)
    print("\nУбедитесь, что:")
    print("   1. Docker контейнер с PostgreSQL запущен")
    print("   2. Установлены все зависимости: pip install requests beautifulsoup4 psycopg2-binary aiohttp asyncpg lxml")
    print("   3. База данных доступна на localhost:5439")
    
    input("\nНажмите Enter для начала...")
    
    scripts = [
        ("threading_parser.py", "THREADING"),
        ("multiprocessing_parser.py", "MULTIPROCESSING"),
        ("async_parser.py", "ASYNC")
    ]
    
    results = {}
    
    for script_name, display_name in scripts:
        print(f"\n{'#'*70}")
        print(f"# {display_name} ПАРСЕР")
        print(f"{'#'*70}")
        
        input(f"\nНажмите Enter для запуска {display_name}...")
        
        elapsed = run_parser(script_name)
        if elapsed is not None:
            results[display_name] = elapsed
        
        # Пауза между запусками
        if script_name != scripts[-1][0]:
            print("\n Пауза 3 секунды перед следующим запуском...")
            time.sleep(3)
    
    # Вывод итогов
    print("\n" + "="*70)
    print("ИТОГОВОЕ СРАВНЕНИЕ")
    print("="*70)
    
    if results:
        for name, duration in results.items():
            print(f"{name:20} : {duration:.2f} секунд")
        
        fastest = min(results, key=results.get)
        slowest = max(results, key=results.get)
        
        print(f"\n Самый быстрый: {fastest} ({results[fastest]:.2f} сек)")
        print(f" Самый медленный: {slowest} ({results[slowest]:.2f} сек)")
        
        # Сравнение с async как базовым
        if "ASYNC" in results:
            async_time = results["ASYNC"]
            print(f"\n Анализ:")
            if "THREADING" in results:
                ratio = results["THREADING"] / async_time
                print(f"   Threading медленнее Async в {ratio:.2f} раза")
            if "MULTIPROCESSING" in results:
                ratio = results["MULTIPROCESSING"] / async_time
                print(f"   Multiprocessing медленнее Async в {ratio:.2f} раза")
    else:
        print(" Ни один парсер не завершился успешно")
    
    print("\n" + "="*70)
    print("Для просмотра результатов выполните:")
    print("python test_db.py")
    print("="*70)

if __name__ == "__main__":
    main()