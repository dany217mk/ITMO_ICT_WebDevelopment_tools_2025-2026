import asyncio
import aiohttp
from bs4 import BeautifulSoup
import time
import asyncpg
from parser.db_utils import DB_CONFIG

URLS = [
    ("https://github.com/trending", "github"),
    ("https://habr.com/ru/articles/", "habr"),
    ("https://news.ycombinator.com/", "hackernews"),
]

async def init_db_async():
    """Создает таблицы асинхронно"""
    try:
        conn = await asyncpg.connect(
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['dbname'],
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port']
        )
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS parsed_content (
                id SERIAL PRIMARY KEY,
                source_url TEXT UNIQUE,
                title TEXT,
                content_summary TEXT,
                parsed_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS skills (
                id BIGSERIAL PRIMARY KEY,
                name VARCHAR(128) UNIQUE,
                category VARCHAR(64)
            )
        """)
        
        await conn.close()
        print("База данных инициализирована (async)")
    except Exception as e:
        print(f"Ошибка инициализации БД: {e}")

async def clear_tables_async(pool):
    """Очищает таблицы"""
    try:
        async with pool.acquire() as conn:
            await conn.execute("DELETE FROM parsed_content")
            await conn.execute("DELETE FROM skills")
        print("Таблицы очищены (async)")
    except Exception as e:
        print(f"Ошибка очистки таблиц: {e}")

async def add_skill_async(pool, skill_name, category):
    """Асинхронное добавление навыка"""
    if not skill_name or skill_name == "Unknown" or len(skill_name) < 2:
        return
    
    try:
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO skills (name, category)
                VALUES ($1, $2)
                ON CONFLICT (name) DO NOTHING
            """, skill_name[:120], category)
    except Exception as e:
        pass

async def save_parsed_async(pool, source_url, title, content_summary):
    """Асинхронное сохранение результата"""
    try:
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO parsed_content (source_url, title, content_summary)
                VALUES ($1, $2, $3)
                ON CONFLICT (source_url) DO UPDATE
                SET title = EXCLUDED.title, 
                    content_summary = EXCLUDED.content_summary,
                    parsed_at = NOW()
            """, source_url, title[:200], content_summary[:500])
    except Exception as e:
        print(f"Ошибка сохранения: {e}")

async def parse_github_async(soup, url, pool):
    """Парсинг GitHub Trending асинхронно"""
    count = 0
    repos = soup.select('article.Box-row')
    
    if not repos:
        repos = soup.select('.Box-row')
    
    for repo in repos[:5]:
        try:
            title_elem = repo.select_one('h2 a')
            if not title_elem:
                title_elem = repo.select_one('h3 a')
            
            if title_elem:
                title = title_elem.text.strip().replace('\n', '').replace(' ', '')
                lang_elem = repo.select_one('span[itemprop="programmingLanguage"]')
                if not lang_elem:
                    lang_elem = repo.select_one('[itemprop="programmingLanguage"]')
                
                lang = lang_elem.text.strip() if lang_elem else "Unknown"
                
                if lang and lang != "Unknown":
                    await add_skill_async(pool, lang, "Programming Language")
                
                await save_parsed_async(pool, url, title, f"Репозиторий, язык: {lang}")
                print(f"  GitHub: {title[:50]}")
                count += 1
        except Exception:
            continue
    
    return count

async def parse_habr_async(soup, url, pool):
    """Парсинг Habr асинхронно"""
    count = 0
    
    articles = soup.select('article.tm-articles-list__item')
    if not articles:
        articles = soup.select('.tm-article-snippet')
    if not articles:
        articles = soup.select('.post-preview')
    
    for article in articles[:5]:
        try:
            title_elem = article.select_one('h2.tm-title__link a')
            if not title_elem:
                title_elem = article.select_one('.tm-title__link')
            if not title_elem:
                title_elem = article.select_one('a.post__title_link')
            
            if not title_elem:
                continue
            
            title = title_elem.text.strip()
            
            hubs = article.select('.tm-publication-hub__link')
            if not hubs:
                hubs = article.select('.post__hubs a')
            
            hub_names = []
            for hub in hubs[:3]:
                hub_name = hub.text.strip().replace('*', '').strip()
                if hub_name and len(hub_name) > 1:
                    hub_names.append(hub_name)
                    await add_skill_async(pool, hub_name, "Technology/Hub")
            
            author_elem = article.select_one('.tm-user-info__username')
            if not author_elem:
                author_elem = article.select_one('.user-info__nickname')
            author = author_elem.text.strip() if author_elem else "Unknown"
            
            time_elem = article.select_one('.tm-article-reading-time__label')
            read_time = time_elem.text.strip() if time_elem else "?"
            
            summary = f"Автор: {author} | Хабы: {', '.join(hub_names[:3])} | Время чтения: {read_time}"
            
            await save_parsed_async(pool, url, title, summary)
            print(f"  Habr: {title[:50]}...")
            count += 1
            
        except Exception:
            continue
    
    if count == 0:
        print(f"  Habr: статей не найдено")
    
    return count

async def parse_hackernews_async(soup, url, pool):
    """Парсинг Hacker News асинхронно"""
    count = 0
    items = soup.select('.athing')
    
    for item in items[:5]:
        try:
            title_elem = item.select_one('.titleline a')
            if title_elem:
                title = title_elem.text.strip()
                
                second_line = item.find_next_sibling('tr')
                if second_line:
                    sitebit = second_line.select_one('.sitebit a')
                    if sitebit:
                        domain = sitebit.text.strip('()')
                        if domain:
                            await add_skill_async(pool, domain, "Website/Source")
                
                await save_parsed_async(pool, url, title, "Hacker News story")
                print(f"  Hacker News: {title[:50]}")
                count += 1
        except Exception:
            continue
    
    return count

async def parse_and_save_async(session, pool, url, source_type):
    """Асинхронный парсинг страницы"""
    print(f"\n[ASYNC] Начинаю парсинг: {url}")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
        }
        
        async with session.get(url, headers=headers, timeout=20) as response:
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            
            if source_type == "github":
                count = await parse_github_async(soup, url, pool)
                print(f"  GitHub: спарсено {count} репозиториев")
            
            elif source_type == "habr":
                count = await parse_habr_async(soup, url, pool)
                print(f"  Habr: спарсено {count} статей")
            
            elif source_type == "hackernews":
                count = await parse_hackernews_async(soup, url, pool)
                print(f"  Hacker News: спарсено {count} новостей")
    
    except asyncio.TimeoutError:
        print(f"  Таймаут при запросе {url}")
    except Exception as e:
        print(f"  Ошибка {url}: {e}")

async def get_stats_async(pool):
    """Получает статистику асинхронно"""
    try:
        async with pool.acquire() as conn:
            parsed_count = await conn.fetchval("SELECT COUNT(*) FROM parsed_content")
            skills_count = await conn.fetchval("SELECT COUNT(*) FROM skills")
            print(f"Статистика: {parsed_count} записей в parsed_content, {skills_count} навыков в skills")
    except Exception as e:
        print(f"Ошибка получения статистики: {e}")

async def main_async():
    print("=" * 70)
    print("Запуск парсинга с использованием ASYNC")
    print("=" * 70)
    
    await init_db_async()
    
    pool = await asyncpg.create_pool(
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        database=DB_CONFIG['dbname'],
        host=DB_CONFIG['host'],
        port=DB_CONFIG['port'],
        min_size=3,
        max_size=10
    )
    
    await clear_tables_async(pool)
    
    start_time = time.time()
    
    async with aiohttp.ClientSession() as session:
        tasks = [parse_and_save_async(session, pool, url, stype) for url, stype in URLS]
        await asyncio.gather(*tasks)
    
    elapsed = time.time() - start_time
    
    await get_stats_async(pool)
    await pool.close()
    
    print("\n" + "=" * 70)
    print(f"ASYNC завершен за {elapsed:.2f} секунд")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main_async())