import threading
import time

def calculate_sum(start, end, result, index):
    """Вычисляет сумму чисел от start до end (включительно)"""
    total = 0
    for i in range(start, end + 1):
        total += i
    result[index] = total

def main():
    N = 100_000_000 
    
    num_threads = 4
    chunk_size = N // num_threads
    
    threads = []
    results = [0] * num_threads
    
    start_time = time.time()
    
    for i in range(num_threads):
        start = i * chunk_size + 1
        end = (i + 1) * chunk_size if i != num_threads - 1 else N
        t = threading.Thread(target=calculate_sum, args=(start, end, results, i))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    total_sum = sum(results)
    elapsed = time.time() - start_time
    
    print(f"Threading результат: {total_sum}")
    print(f"Threading время: {elapsed:.2f} секунд")

if __name__ == "__main__":
    main()