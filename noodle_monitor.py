import os
import json
import re
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
import cloudscraper

# 创建智能爬虫实例，模拟真实 Chrome 浏览器
scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'desktop': True
    }
)

def get_url(url):
    try:
        resp = scraper.get(url, timeout=15)
        print(f"[请求] {url} -> HTTP {resp.status_code}")
        if resp.status_code == 200:
            resp.encoding = resp.apparent_encoding or 'utf-8'
            return resp.text
    except Exception as e:
        print(f"[错误] 请求失败 {url}: {e}")
    return None

def make_abs_url(base, src):
    if not src:
        return ""
    if src.startswith("//"):
        return "https:" + src
    if src.startswith("http"):
        return src
    if src.startswith("/"):
        domain = re.match(r'(https?://[^/]+)', base)
        return (domain.group(1) if domain else "") + src
    return base.rsplit('/', 1)[0] + '/' + src

# ==================== 1. 日清食品 (Nissin) ====================
def fetch_nissin():
    url = "https://www.nissin.com/jp/products/news/"
    html = get_url(url)
    items = []
    if not html:
        return items
    soup = BeautifulSoup(html, 'html.parser')
    cards = soup.select('.p-news-list__item, .p-card, article, .news-list li, a.p-card')
    for card in cards:
        title_el = card.select_one('.p-card__title, .title, h3, h2, span')
        img_el = card.select_one('img')
        link_el = card if card.name == 'a' else card.select_one('a')
        
        if title_el:
            title = title_el.get_text(strip=True)
            if not title or "新商品情報" in title or title == "ニュース":
                continue
            img = make_abs_url(url, img_el.get('src') if img_el else '')
            link = make_abs_url(url, link_el.get('href') if link_el else '')
            if not any(i['title'] == title for i in items):
                items.append({'title': title, 'img': img, 'link': link})
        if len(items) >= 6:
            break
    return items

# ==================== 2. 东洋水产 (Maruchan) ====================
def fetch_maruchan():
    url = "https://www.maruchan.co.jp/news_topics/"
    html = get_url(url)
    items = []
    if not html:
        return items
    soup = BeautifulSoup(html, 'html.parser')
    cards = soup.select('.news-list li, .article-list article, .newsBox, li.item')
    for card in cards:
        title_el = card.select_one('.title, dt, h3, a')
        img_el = card.select_one('img')
        link_el = card.select_one('a')
        if title_el:
            title = title_el.get_text(strip=True)
            if len(title) < 4:
                continue
            img = make_abs_url(url, img_el.get('src') if img_el else '')
            link = make_abs_url(url, link_el.get('href') if link_el else '')
            if title and not any(i['title'] == title for i in items):
                items.append({'title': title, 'img': img, 'link': link})
        if len(items) >= 6:
            break
    return items

# ==================== 3. 明星食品 (Myojo) ====================
def fetch_myojo():
    url = "https://www.myojofoods.co.jp/news/"
    html = get_url(url)
    items = []
    if not html:
        return items
    soup = BeautifulSoup(html, 'html.parser')
    cards = soup.select('main .p-news-list__item, main .c-card-news, article')
    for card in cards:
        title_el = card.select_one('.c-card-news__title, .title, h3, a')
        img_el = card.select_one('img')
        link_el = card.select_one('a')
        if title_el:
            title = title_el.get_text(strip=True)
            if "プライバシー" in title or "サステナビリティ" in title:
                continue
            img = make_abs_url(url, img_el.get('src') if img_el else '')
            link = make_abs_url(url, link_el.get('href') if link_el else '')
            if title and not any(i['title'] == title for i in items):
                items.append({'title': title, 'img': img, 'link': link})
        if len(items) >= 6:
            break
    return items

# ==================== 4. Acecook (エースコック) ====================
def fetch_acecook():
    url = "https://www.acecook.co.jp/news/"
    html = get_url(url)
    items = []
    if not html:
        return items
    soup = BeautifulSoup(html, 'html.parser')
    cards = soup.select('.news-list__item, .p-news-item, .mod-newsList-item, article')
    for card in cards:
        title_el = card.select_one('.title, .p-news-item__title, h3, a')
        img_el = card.select_one('img')
        link_el = card.select_one('a')
        if title_el:
            title = title_el.get_text(strip=True)
            img = make_abs_url(url, img_el.get('src') if img_el else '')
            link = make_abs_url(url, link_el.get('href') if link_el else '')
            if title and not any(i['title'] == title for i in items):
                items.append({'title': title, 'img': img, 'link': link})
        if len(items) >= 6:
            break
    return items

# ==================== 生成 HTML ====================
def generate_html_cards(brand_name, items):
    if not items:
        return ""
    
    html = f'<section class="brand-section">'
    html += f'<div class="brand-header"><div class="brand-title">{brand_name}</div></div>'
    html += '<div class="cards-grid">'
    
    for item in items:
        img_src = item['img'] if item['img'] else 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="200" height="140"><rect width="200" height="140" fill="%23f1f5f9"/><text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" fill="%2394a3b8">暂无图片</text></svg>'
        link_url = item['link'] if item['link'] else '#'
        
        html += f'''
        <a href="{link_url}" target="_blank" class="card" rel="noopener noreferrer">
            <div class="img-box">
                <img src="{img_src}" alt="{item['title']}" referrerpolicy="no-referrer" onerror="this.src='data:image/svg+xml;utf8,<svg xmlns=&quot;http://www.w3.org/2000/svg&quot; width=&quot;200&quot; height=&quot;140&quot;><rect width=&quot;200&quot; height=&quot;140&quot; fill=&quot;%23f1f5f9&quot;/><text x=&quot;50%&quot; y=&quot;50%&quot; dominant-baseline=&quot;middle&quot; text-anchor=&quot;middle&quot; fill=&quot;%2394a3b8&quot;>图片载入失败</text></svg>';">
            </div>
            <div class="card-info">{item['title']}</div>
        </a>
        '''
    html += '</div></section>'
    return html

def main():
    print("=== 开始抓取方便面情报 ===")
    
    brands = [
        {"name": "日清食品 (Nissin)", "fetcher": fetch_nissin},
        {"name": "东洋水产 (Maruchan)", "fetcher": fetch_maruchan},
        {"name": "明星食品 (Myojo)", "fetcher": fetch_myojo},
        {"name": "エースコック (Acecook)", "fetcher": fetch_acecook},
    ]

    all_cards_html = ""
    result_data = {}
    total_count = 0

    for brand in brands:
        name = brand["name"]
        print(f"\n正在抓取: {name}...")
        try:
            items = brand["fetcher"]()
            result_data[name] = items
            count = len(items)
            total_count += count
            print(f" -> 成功获取 {count} 条数据")
            all_cards_html += generate_html_cards(name, items)
        except Exception as e:
            print(f" -> 抓取失败 {name}: {e}")

    now_jst = datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M")

    # 防空白保底机制：如果本次全被拦截，尝试使用 history.json 中的上一次有效数据
    if total_count == 0 and os.path.exists("history.json"):
        try:
            with open("history.json", "r", encoding="utf-8") as f:
                old_data = json.load(f).get("brands", {})
            for name, items in old_data.items():
                if items:
                    all_cards_html += generate_html_cards(name, items)
                    total_count += len(items)
            print("[提示] 触发备用数据机制，成功载入历史快照内容。")
        except Exception as e:
            print(f"[错误] 读取历史数据失败: {e}")

    # 如果仍然完全没有内容，显示友好提示
    if total_count == 0:
        all_cards_html = '<div style="text-align: center; padding: 50px 20px; color: #64748b;">官网巡逻中，暂未检测到新发布商品，请稍后刷新页面。</div>'

    # 写入 history.json（仅在有新数据时覆盖）
    if total_count > 0 and result_data:
        with open("history.json", "w", encoding="utf-8") as f:
            json.dump({"update_time": now_jst, "brands": result_data}, f, ensure_ascii=False, indent=2)

    # 替换 index.html 中的内容
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            html_content = f.read()

        html_content = re.sub(r'🟢 更新时间:.*?(?=</div>)', f'🟢 更新时间: {now_jst}', html_content)
        
        if "<!-- CONTENT_START -->" in html_content and "<!-- CONTENT_END -->" in html_content:
            pattern = r"<!-- CONTENT_START -->[\s\S]*?<!-- CONTENT_END -->"
            replacement = f"<!-- CONTENT_START -->\n{all_cards_html}\n<!-- CONTENT_END -->"
            html_content = re.sub(pattern, replacement, html_content)

        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html_content)

    print(f"\n=== 执行完成！更新时间：{now_jst} ===")

if __name__ == "__main__":
    main()
