"""
Сервис для вызова парсера (обертка над парсером из лабы 2)
"""
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Tuple, Optional
import asyncpg
from app.core.config import settings

# Конфиг для БД парсера
PARSER_DB_CONFIG = {
    'user': 'postgres',
    'password': 'password',
    'database': 'teamfinder',
    'host': 'postgres',
    'port': 5432
}

URLS = [
    ("https://github.com/trending", "github"),
    ("https://habr.com/ru/articles/", "habr"),
    ("https://news.ycombinator.com/", "hackernews"),
]


async def get_db_pool():
    """Создает пул соединений с БД"""
    return await asyncpg.create_pool(
        user=PARSER_DB_CONFIG['user'],
        password=PARSER_DB_CONFIG['password'],
        database=PARSER_DB_CONFIG['database'],
        host=PARSER_DB_CONFIG['host'],
        port=PARSER_DB_CONFIG['port'],
        min_size=2,
        max_size=10
    )


async def add_skill(pool, skill_name: str, category: str):
    """Добавляет навык в БД"""
    if not skill_name or skill_name == "Unknown" or len(skill_name) < 2:
        return
    
    try:
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO skills (name, category)
                VALUES ($1, $2)
                ON CONFLICT (name) DO NOTHING
            """, skill_name[:120], category)
    except Exception:
        pass


async def save_parsed(pool, source_url: str, title: str, content_summary: str):
    """Сохраняет результат парсинга"""
    try:
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO parsed_content (source_url, title, content_summary, parsed_at)
                VALUES ($1, $2, $3, NOW())
                ON CONFLICT (source_url) DO UPDATE
                SET title = EXCLUDED.title,
                    content_summary = EXCLUDED.content_summary,
                    parsed_at = NOW()
            """, source_url, title[:200], content_summary[:500])
    except Exception as e:
        print(f"Ошибка сохранения: {e}")


async def parse_github(soup, url, pool) -> int:
    """Парсинг GitHub Trending"""
    count = 0
    repos = soup.select('article.Box-row') or soup.select('.Box-row')
    
    for repo in repos[:5]:
        try:
            title_elem = repo.select_one('h2 a') or repo.select_one('h3 a')
            if title_elem:
                title = title_elem.text.strip().replace('\n', '').replace(' ', '')
                lang_elem = repo.select_one('span[itemprop="programmingLanguage"]')
                lang = lang_elem.text.strip() if lang_elem else "Unknown"
                
                if lang and lang != "Unknown":
                    await add_skill(pool, lang, "Programming Language")
                
                await save_parsed(pool, url, title, f"Репозиторий, язык: {lang}")
                count += 1
        except Exception:
            continue
    return count


async def parse_habr(soup, url, pool) -> int:
    """Парсинг Habr"""
    count = 0
    articles = soup.select('article.tm-articles-list__item') or \
               soup.select('.tm-article-snippet') or \
               soup.select('.post-preview')
    
    for article in articles[:5]:
        try:
            title_elem = article.select_one('h2.tm-title__link a') or \
                         article.select_one('.tm-title__link') or \
                         article.select_one('a.post__title_link')
            
            if not title_elem:
                continue
            
            title = title_elem.text.strip()
            
            hubs = article.select('.tm-publication-hub__link') or \
                   article.select('.post__hubs a')
            
            hub_names = []
            for hub in hubs[:3]:
                hub_name = hub.text.strip().replace('*', '').strip()
                if hub_name and len(hub_name) > 1:
                    hub_names.append(hub_name)
                    await add_skill(pool, hub_name, "Technology/Hub")
            
            author_elem = article.select_one('.tm-user-info__username') or \
                          article.select_one('.user-info__nickname')
            author = author_elem.text.strip() if author_elem else "Unknown"
            
            summary = f"Автор: {author} | Хабы: {', '.join(hub_names[:3])}"
            await save_parsed(pool, url, title, summary)
            count += 1
        except Exception:
            continue
    return count


async def parse_hackernews(soup, url, pool) -> int:
    """Парсинг Hacker News"""
    count = 0
    items = soup.select('.athing')
    
    for item in items[:5]:
        try:
            title_elem = item.select_one('.titleline a')
            if title_elem:
                title = title_elem.text.strip()
                await save_parsed(pool, url, title, "Hacker News story")
                count += 1
        except Exception:
            continue
    return count


async def parse_single_source(session, pool, url: str, source_type: str) -> Dict[str, Any]:
    """Парсинг одного источника"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        async with session.get(url, headers=headers, timeout=20) as response:
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            
            if source_type == "github":
                count = await parse_github(soup, url, pool)
            elif source_type == "habr":
                count = await parse_habr(soup, url, pool)
            elif source_type == "hackernews":
                count = await parse_hackernews(soup, url, pool)
            else:
                count = 0
            
            return {
                "url": url,
                "source_type": source_type,
                "items_parsed": count,
                "status": "success"
            }
    except Exception as e:
        return {
            "url": url,
            "source_type": source_type,
            "items_parsed": 0,
            "status": "error",
            "error": str(e)
        }


async def run_parser_async(url: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Асинхронный запуск парсера
    
    Args:
        url: конкретный URL для парсинга (если None - парсит все)
    
    Returns:
        Список результатов парсинга
    """
    results = []
    
    # Определяем какие URL парсить
    if url:
        source_type = None
        for u, t in URLS:
            if u == url:
                source_type = t
                break
        if not source_type:
            source_type = "unknown"
        urls_to_parse = [(url, source_type)]
    else:
        urls_to_parse = URLS
    
    pool = await get_db_pool()
    
    async with aiohttp.ClientSession() as session:
        tasks = [parse_single_source(session, pool, u, t) for u, t in urls_to_parse]
        results = await asyncio.gather(*tasks)
    
    await pool.close()
    return results


# Оставляем синхронную обертку для совместимости с Celery
def run_parser_sync(url: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Синхронная обертка для вызова парсера (для Celery)
    """
    try:
        # Пытаемся получить текущий event loop
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # Нет запущенного event loop - можно использовать asyncio.run()
        return asyncio.run(run_parser_async(url))
    else:
        # Уже есть запущенный event loop - создаем новый в отдельном потоке
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, run_parser_async(url))
            return future.result()