import asyncio
import concurrent.futures
import time

def calculate_sum_sync(start, end):
    """Синхронная функция для вычислений"""
    total = 0
    for i in range(start, end + 1):
        total += i
    return total

async def calculate_sum_async(start, end, executor):
    """Асинхронная обертка"""
    loop = asyncio.get_event_loop()
    # Запускаем CPU-задачу в отдельном процессе (чтобы не блокировать)
    result = await loop.run_in_executor(executor, calculate_sum_sync, start, end)
    return result

async def main_async():
    N = 100_000_000
    num_tasks = 4
    chunk_size = N // num_tasks
    
    # Создаем пул процессов для реальных вычислений
    with concurrent.futures.ProcessPoolExecutor(max_workers=num_tasks) as executor:
        tasks = []
        for i in range(num_tasks):
            start = i * chunk_size + 1
            end = (i + 1) * chunk_size if i != num_tasks - 1 else N
            tasks.append(calculate_sum_async(start, end, executor))
        
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start_time
        
        total_sum = sum(results)
        print(f"Async результат: {total_sum}")
        print(f"Async время: {elapsed:.2f} секунд")

if __name__ == "__main__":
    asyncio.run(main_async())