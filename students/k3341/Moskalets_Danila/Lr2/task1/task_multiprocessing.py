import multiprocessing
import time

def calculate_sum(start, end):
    """Вычисляет сумму чисел от start до end (включительно)"""
    total = 0
    for i in range(start, end + 1):
        total += i
    return total

def main():
    N = 100_000_000
    num_processes = multiprocessing.cpu_count()  # используем все ядра
    
    chunk_size = N // num_processes
    pool = multiprocessing.Pool(processes=num_processes)
    
    tasks = []
    for i in range(num_processes):
        start = i * chunk_size + 1
        end = (i + 1) * chunk_size if i != num_processes - 1 else N
        tasks.append((start, end))
    
    start_time = time.time()
    results = pool.starmap(calculate_sum, tasks)
    pool.close()
    pool.join()
    
    total_sum = sum(results)
    elapsed = time.time() - start_time
    
    print(f"Multiprocessing результат: {total_sum}")
    print(f"Multiprocessing время: {elapsed:.2f} секунд")
    print(f"Использовано ядер: {num_processes}")

if __name__ == "__main__":
    # Важно: multiprocessing требует защиты входа
    main()