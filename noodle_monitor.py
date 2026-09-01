import os
import json
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ja,zh-CN;q=0.9,zh;q=0.8,en;q=0.7",
}

def get_url(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=12)
        if resp.status_code == 200:
            resp.encoding = resp.apparent_encoding or 'utf-8'
            return resp.text
    except Exception as e:
        print(f"[Error] 请求失败 {url}: {e}")
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

# ==================== 各品牌抓取 ====================

def fetch_nissin():
    url = "https://www.nissin.com/jp/products/news/"
    html = get_url(url)
    items = []
    if not html:
        return items
    soup = BeautifulSoup(html, 'html.parser')
    cards = soup.select('.p-news-list__item, .p-card, article')
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

def fetch_maruchan():
    url = "https://www.maruchan.co.jp/news_topics/"
    html = get_url(url)
    items = []
    if not html:
        return items
    soup = BeautifulSoup(html, 'html.parser')
    cards = soup.select('.news-list li, .article-list article, .newsBox')
    for card in cards:
        title_el = card.select_one('.title, dt, h3, a')
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

def fetch_myojo():
    url = "https://www.myojofoods.co.jp/news/"
    html = get_url(url)
    items = []
    if not html:
        return items
    soup = BeautifulSoup(html, 'html.parser')
    cards = soup.select('main .p-news-list__item, main .c-card-news, main article')
    for card in cards:
        title_el = card.select_one('.c-card-news__title, .title, h3')
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

def fetch_acecook():
    url = "https://www.acecook.co.jp/news/"
    html = get_url(url)
    items = []
    if not html:
        return items
    soup = BeautifulSoup(html, 'html.parser')
    cards = soup.select('.news-list__item, .p-news-item, .mod-newsList-item')
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

# ==================== 生成 HTML 内容 ====================

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
    print("开始抓取泡面情报...")
    
    brands = [
        {"name": "日清食品 (Nissin)", "fetcher": fetch_nissin},
        {"name": "东洋水产 (Maruchan)", "fetcher": fetch_maruchan},
        {"name": "明星食品 (Myojo)", "fetcher": fetch_myojo},
        {"name": "エースコック (Acecook)", "fetcher": fetch_acecook},
    ]

    all_cards_html = ""
    result_data = {}

    for brand in brands:
        name = brand["name"]
        print(f"正在抓取: {name}")
        try:
            items = brand["fetcher"]()
            result_data[name] = items
            all_cards_html += generate_html_cards(name, items)
        except Exception as e:
            print(f"  抓取失败 {name}: {e}")

    now_jst = datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M")

    # 1. 保存 history.json 备份
    with open("history.json", "w", encoding="utf-8") as f:
        json.dump({"update_time": now_jst, "brands": result_data}, f, ensure_ascii=False, indent=2)

    # 2. 直接将渲染好的 HTML 卡片插入 index.html 模版
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            html_content = f.read()

        # 替换更新时间和内容区
        html_content = re.sub(r'\{\{\s*UPDATE_TIME\s*\}\}', now_jst, html_content)
        
        # 替换卡片内容区域
        if "<!-- CONTENT_START -->" in html_content and "<!-- CONTENT_END -->" in html_content:
            pattern = r"<!-- CONTENT_START -->[\s\S]*?<!-- CONTENT_END -->"
            replacement = f"<!-- CONTENT_START -->\n{all_cards_html}\n<!-- CONTENT_END -->"
            html_content = re.sub(pattern, replacement, html_content)

        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html_content)

    print(f"完成！更新时间：{now_jst}")

if __name__ == "__main__":
    main()
