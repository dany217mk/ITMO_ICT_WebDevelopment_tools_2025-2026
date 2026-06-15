import multiprocessing
import requests
from bs4 import BeautifulSoup
import time
from db_utils import init_db, save_parsed_data, add_skill_if_not_exists, clear_tables, get_stats

URLS = [
    ("https://github.com/trending", "github"),
    ("https://habr.com/ru/articles/", "habr"),
    ("https://news.ycombinator.com/", "hackernews"),
]

def parse_github(soup, url):
    """Парсинг GitHub Trending"""
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
                    add_skill_if_not_exists(lang, "Programming Language")
                
                save_parsed_data(url, title, f"Репозиторий, язык: {lang}")
                print(f"  GitHub: {title[:50]}")
                count += 1
        except Exception as e:
            continue
    
    return count

def parse_habr(soup, url):
    """Парсинг Habr (обновленный)"""
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
                    add_skill_if_not_exists(hub_name, "Technology/Hub")
            
            author_elem = article.select_one('.tm-user-info__username')
            if not author_elem:
                author_elem = article.select_one('.user-info__nickname')
            author = author_elem.text.strip() if author_elem else "Unknown"
            
            time_elem = article.select_one('.tm-article-reading-time__label')
            read_time = time_elem.text.strip() if time_elem else "?"
            
            summary = f"Автор: {author} | Хабы: {', '.join(hub_names[:3])} | Время чтения: {read_time}"
            
            save_parsed_data(url, title, summary)
            print(f"  Habr: {title[:50]}...")
            count += 1
            
        except Exception:
            continue
    
    if count == 0:
        print(f"  Habr: статей не найдено")
    
    return count

def parse_hackernews(soup, url):
    """Парсинг Hacker News"""
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
                            add_skill_if_not_exists(domain, "Website/Source")
                
                save_parsed_data(url, title, f"Hacker News story")
                print(f"  Hacker News: {title[:50]}")
                count += 1
        except Exception:
            continue
    
    return count

def parse_and_save(url_type):
    """Парсит страницу и сохраняет данные"""
    url, source_type = url_type
    print(f"\n[MULTIPROCESSING] Начинаю парсинг: {url} (PID: {multiprocessing.current_process().pid})")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
        }
        
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        if source_type == "github":
            count = parse_github(soup, url)
            print(f"  GitHub: спарсено {count} репозиториев")
        
        elif source_type == "habr":
            count = parse_habr(soup, url)
            print(f"  Habr: спарсено {count} статей")
        
        elif source_type == "hackernews":
            count = parse_hackernews(soup, url)
            print(f"  Hacker News: спарсено {count} новостей")
    
    except requests.exceptions.Timeout:
        print(f"  Таймаут при запросе {url}")
    except Exception as e:
        print(f"  Ошибка {url}: {e}")

def main():
    print("=" * 70)
    print("Запуск парсинга с использованием MULTIPROCESSING")
    print("=" * 70)
    
    init_db()
    clear_tables()
    
    start_time = time.time()
    
    with multiprocessing.Pool(processes=3) as pool:
        pool.map(parse_and_save, URLS)
    
    elapsed = time.time() - start_time
    
    print("\n" + "=" * 70)
    print(f"MULTIPROCESSING завершен за {elapsed:.2f} секунд")
    get_stats()
    print("=" * 70)

if __name__ == "__main__":
    main()