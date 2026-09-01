import os
import json
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta

# 模拟真实 Chrome 浏览器，防止被官网拦截
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "ja-JP,ja;q=0.9,zh-CN;q=0.8,zh;q=0.7,en-US;q=0.6,en;q=0.5",
    "Cache-Control": "max-age=0",
    "Upgrade-Insecure-Requests": "1"
}

def get_url(url):
    try:
        session = requests.Session()
        resp = session.get(url, headers=HEADERS, timeout=15)
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
    cards = soup.select('.p-news-list__item, .p-card, article, .news-list li, .p-news-list div')
    for card in cards:
        title_el = card.select_one('.p-card__title, .title, h3, h2, a')
        img_el = card.select_one('img')
        link_el = card.select_one('a')
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
    cards = soup.select('.news-list li, .article-list article, .newsBox, li')
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
    cards = soup.select('main .p-news-list__item, main .c-card-news, main article, .p-news-list__item')
    for card in cards:
        title_el = card.select_one('.c-card-news__title, .title, h3, a')
        img_el = card.select_one('img')
        link_el = card.select_one('a')
        if title_el:
            title = title_el.get_text(strip=True)
            if "プライバシー" in title or "サステナビリティ" in title or "利用規約" in title:
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

# ==================== 生成卡片 HTML ====================
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

    # 保底提示：若全部被云端反爬拦截，显示明确提示
    if total_count == 0:
        print("\n[警告] 未能获取到新数据，触发保底提示。")
        all_cards_html = '<div style="text-align: center; padding: 40px; color: #64748b; font-size: 1rem;">官网巡逻中，暂未检测到新发布商品，请稍后刷新。</div>'

    now_jst = datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M")

    # 保存 JSON
    with open("history.json", "w", encoding="utf-8") as f:
        json.dump({"update_time": now_jst, "brands": result_data}, f, ensure_ascii=False, indent=2)

    # 替换 index.html 中的文本与 HTML
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            html_content = f.read()

        # 1. 替换更新时间（同时兼容 {{ UPDATE_TIME }} 和已被替换的时间格式）
        html_content = re.sub(r'🟢 更新时间:.*?(?=</div>)', f'🟢 更新时间: {now_jst}', html_content)
        
        # 2. 替换 CONTENT 区域
        if "<!-- CONTENT_START -->" in html_content and "<!-- CONTENT_END -->" in html_content:
            pattern = r"<!-- CONTENT_START -->[\s\S]*?<!-- CONTENT_END -->"
            replacement = f"<!-- CONTENT_START -->\n{all_cards_html}\n<!-- CONTENT_END -->"
            html_content = re.sub(pattern, replacement, html_content)

        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html_content)

    print(f"\n=== 执行完成！更新时间：{now_jst} ===")

if __name__ == "__main__":
    main()
