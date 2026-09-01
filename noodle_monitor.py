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
    """日清食品 - 过滤通用栏目名，抓取具体商品"""
    url = "https://www.nissin.com/jp/products/news/"
    html = get_url(url)
    items = []
    if not html:
        return items
    soup = BeautifulSoup(html, 'html.parser')
    
    # 查找所有商品卡片
    cards = soup.select('.p-news-list__item, .p-card, article, .news-list li')
    for card in cards:
        title_el = card.select_one('.p-card__title, .title, h3, h2, a')
        img_el = card.select_one('img')
        link_el = card.select_one('a')
        
        if title_el:
            title = title_el.get_text(strip=True)
            # 过滤掉通用的栏目大标题
            if not title or "新商品情報" in title or title == "ニュース":
                continue
            
            img = make_abs_url(url, img_el.get('src') if img_el else '')
            link = make_abs_url(url, link_el.get('href') if link_el else '')
            
            if not any(i['title'] == title for i in items):
                items.append({'title': title, 'img': img, 'link': link})
        if len(items) >= 5:
            break
    return items

def fetch_maruchan():
    """东洋水产"""
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
        if len(items) >= 5:
            break
    return items

def fetch_myojo():
    """明星食品 - 仅抓取 main 区域"""
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
        if len(items) >= 5:
            break
    return items

def fetch_acecook():
    """Acecook"""
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
        if len(items) >= 5:
            break
    return items

# ==================== 主逻辑与模版替换 ====================

def main():
    print("开始抓取泡面情报...")
    
    brands = [
        {"name": "日清食品 (Nissin)", "fetcher": fetch_nissin},
        {"name": "东洋水产 (Maruchan)", "fetcher": fetch_maruchan},
        {"name": "明星食品 (Myojo)", "fetcher": fetch_myojo},
        {"name": "エースコック (Acecook)", "fetcher": fetch_acecook},
    ]

    result_data = {}
    for brand in brands:
        name = brand["name"]
        print(f"抓取: {name}")
        try:
            result_data[name] = brand["fetcher"]()
        except Exception as e:
            print(f"  失败: {e}")
            result_data[name] = []

    # 东九区时间
    now_jst = datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M")

    # 1. 保存 history.json / data.json 供备份
    output_json = {
        "update_time": now_jst,
        "brands": result_data
    }
    with open("history.json", "w", encoding="utf-8") as f:
        json.dump(output_json, f, ensure_ascii=False, indent=2)

    # 2. 如果 index.html 中有 {{ UPDATE_TIME }} 占位符，执行直接替换
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            html_content = f.read()

        # 替换更新时间
        if "{{ UPDATE_TIME }}" in html_content:
            html_content = html_content.replace("{{ UPDATE_TIME }}", now_jst)

        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html_content)

    print(f"完成！更新时间：{now_jst}")

if __name__ == "__main__":
    main()
