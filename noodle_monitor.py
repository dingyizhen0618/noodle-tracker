import os
import json
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta

# 模拟真实的桌面 Chrome 浏览器 Headers，包含 Referer
BASE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "ja,zh-CN;q=0.9,zh;q=0.8,en;q=0.7",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}

def get_url(url):
    try:
        headers = BASE_HEADERS.copy()
        headers["Referer"] = url
        resp = requests.get(url, headers=headers, timeout=15)
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

# 过滤垃圾词汇（隐私政策、公司介绍等非商品内容）
FILTER_WORDS = ["プライバシー", "サステナビリティ", "利用規約", "会社概要", "IR情報", "採用情報", "お問い合わせ"]

# ==================== 1. 日清食品 (Nissin) ====================
def fetch_nissin():
    url = "https://www.nissin.com/jp/products/news/"
    html = get_url(url)
    items = []
    if not html:
        return items
    soup = BeautifulSoup(html, 'html.parser')
    
    # 获取所有的链接区块
    links = soup.find_all('a', href=True)
    for a in links:
        href = a['href']
        # 筛选产品/新闻详情页链接
        if '/news/' in href or '/products/' in href:
            text = a.get_text(strip=True)
            img = a.find('img')
            img_src = img.get('src') if img else ''
            
            # 如果没有直接包含文本，向上找父级容器里的标题
            if not text:
                parent = a.find_parent(['article', 'li', 'div'])
                if parent:
                    title_el = parent.select_one('h2, h3, .title, .p-card__title')
                    if title_el:
                        text = title_el.get_text(strip=True)
            
            if text and len(text) > 3 and not any(w in text for w in FILTER_WORDS) and text != "ニュース":
                abs_link = make_abs_url(url, href)
                abs_img = make_abs_url(url, img_src)
                if not any(i['title'] == text for i in items):
                    items.append({'title': text, 'img': abs_img, 'link': abs_link})
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
    
    # 查找新闻列表项
    elements = soup.select('.news-list li, .newsBox, article, tr, li')
    for el in elements:
        a_tag = el.find('a', href=True)
        if not a_tag:
            continue
        title = el.get_text(strip=True)
        # 清理日期格式干扰
        title = re.sub(r'^\d{4}\.\d{2}\.\d{2}', '', title).strip()
        img_el = el.find('img')
        
        if title and len(title) > 4 and not any(w in title for w in FILTER_WORDS):
            link = make_abs_url(url, a_tag['href'])
            img = make_abs_url(url, img_el.get('src') if img_el else '')
            if not any(i['title'] == title for i in items):
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
    
    cards = soup.select('main a, article a, .p-news-list__item a')
    for a in cards:
        href = a.get('href', '')
        text = a.get_text(strip=True)
        img_el = a.find('img')
        
        if text and len(text) > 3 and not any(w in text for w in FILTER_WORDS):
            link = make_abs_url(url, href)
            img = make_abs_url(url, img_el.get('src') if img_el else '')
            if not any(i['title'] == text for i in items):
                items.append({'title': text, 'img': img, 'link': link})
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
    
    cards = soup.select('.news-list__item, .p-news-item, article, li')
    for card in cards:
        a_tag = card.find('a', href=True)
        if not a_tag:
            continue
        title = card.get_text(strip=True)
        title = re.sub(r'^\d{4}\.\d{2}\.\d{2}', '', title).strip()
        img_el = card.find('img')
        
        if title and len(title) > 3 and not any(w in title for w in FILTER_WORDS):
            link = make_abs_url(url, a_tag['href'])
            img = make_abs_url(url, img_el.get('src') if img_el else '')
            if not any(i['title'] == title for i in items):
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

    # 修改为中国时间 (UTC+8)
    now_cst = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M")

    # 保底显示机制：若未获取到数据则显示文字提示
    if total_count == 0:
        all_cards_html = '<div style="text-align: center; padding: 50px 20px; color: #64748b;">官网巡逻中，暂未检测到新发布商品，请稍后刷新。</div>'

    # 保存至 history.json
    with open("history.json", "w", encoding="utf-8") as f:
        json.dump({"update_time": now_cst, "brands": result_data}, f, ensure_ascii=False, indent=2)

    # 替换 index.html
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            html_content = f.read()

        html_content = re.sub(r'🟢 更新时间:.*?(?=</div>)', f'🟢 更新时间: {now_cst}', html_content)
        
        if "<!-- CONTENT_START -->" in html_content and "<!-- CONTENT_END -->" in html_content:
            pattern = r"<!-- CONTENT_START -->[\s\S]*?<!-- CONTENT_END -->"
            replacement = f"<!-- CONTENT_START -->\n{all_cards_html}\n<!-- CONTENT_END -->"
            html_content = re.sub(pattern, replacement, html_content)

        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html_content)

    print(f"\n=== 执行完成！更新时间(北京时间)：{now_cst} ===")

if __name__ == "__main__":
    main()
