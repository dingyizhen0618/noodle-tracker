import os
import json
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta

# 请求头配置，模仿真实浏览器访问
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ja,zh-CN;q=0.9,zh;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
}

def get_url(url):
    """通用网络请求函数"""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=12)
        if resp.status_code == 200:
            # 自动识别编码
            resp.encoding = resp.apparent_encoding or 'utf-8'
            return resp.text
    except Exception as e:
        print(f"[Error] 请求失败 {url}: {e}")
    return None

def make_absolute_url(base_url, src):
    """将相对路径图片转为绝对路径"""
    if not src:
        return ""
    if src.startswith("//"):
        return "https:" + src
    elif src.startswith("http"):
        return src
    elif src.startswith("/"):
        # 提取域名部分
        domain = re.match(r'(https?://[^/]+)', base_url)
        return (domain.group(1) if domain else "") + src
    else:
        return base_url.rsplit('/', 1)[0] + '/' + src

# ==================== 各品牌精准抓取解析器 ====================

def fetch_nissin():
    """日清食品 (Nissin)"""
    url = "https://www.nissin.com/jp/products/news/"
    html = get_url(url)
    items = []
    if not html:
        return items
    soup = BeautifulSoup(html, 'html.parser')
    # 查找日清新闻/新品卡片
    cards = soup.select('.p-news-list__item, .p-card, article')
    for card in cards:
        title_el = card.select_one('.p-card__title, .title, h3, h2')
        img_el = card.select_one('img')
        link_el = card.select_one('a')
        
        if title_el:
            title = title_el.get_text(strip=True)
            img = make_absolute_url(url, img_el.get('src') if img_el else '')
            link = make_absolute_url(url, link_el.get('href') if link_el else '')
            if title and not any(i['title'] == title for i in items):
                items.append({'title': title, 'img': img, 'link': link})
        if len(items) >= 5:
            break
    return items

def fetch_maruchan():
    """东洋水产 (Maruchan)"""
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
            img = make_absolute_url(url, img_el.get('src') if img_el else '')
            link = make_absolute_url(url, link_el.get('href') if link_el else '')
            if title and not any(i['title'] == title for i in items):
                items.append({'title': title, 'img': img, 'link': link})
        if len(items) >= 5:
            break
    return items

def fetch_myojo():
    """明星食品 (Myojo) - 精准定位 main 主体，避免抓到页脚隐私政策"""
    url = "https://www.myojofoods.co.jp/news/"
    html = get_url(url)
    items = []
    if not html:
        return items
    soup = BeautifulSoup(html, 'html.parser')
    # 限制在 main 主体区域内
    cards = soup.select('main .p-news-list__item, main .c-card-news, main article')
    for card in cards:
        title_el = card.select_one('.c-card-news__title, .title, h3')
        img_el = card.select_one('img')
        link_el = card.select_one('a')
        
        if title_el:
            title = title_el.get_text(strip=True)
            # 过滤掉隐私政策和非新闻类的杂项
            if "プライバシー" in title or "サイトのご利用" in title or "サステナビリティ" in title:
                continue
            img = make_absolute_url(url, img_el.get('src') if img_el else '')
            link = make_absolute_url(url, link_el.get('href') if link_el else '')
            if title and not any(i['title'] == title for i in items):
                items.append({'title': title, 'img': img, 'link': link})
        if len(items) >= 5:
            break
    return items

def fetch_acecook():
    """エースコック (Acecook)"""
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
            img = make_absolute_url(url, img_el.get('src') if img_el else '')
            link = make_absolute_url(url, link_el.get('href') if link_el else '')
            if title and not any(i['title'] == title for i in items):
                items.append({'title': title, 'img': img, 'link': link})
        if len(items) >= 5:
            break
    return items

def fetch_samyang():
    """韩国三养 (Samyang)"""
    url = "https://www.samyangfoods.com/news/list.do"
    html = get_url(url)
    items = []
    if not html:
        return items
    soup = BeautifulSoup(html, 'html.parser')
    cards = soup.select('.board_list tr, .news_list li, .list_item')
    for card in cards:
        title_el = card.select_one('.title, td.subject, a')
        img_el = card.select_one('img')
        link_el = card.select_one('a')
        
        if title_el:
            title = title_el.get_text(strip=True)
            img = make_absolute_url(url, img_el.get('src') if img_el else '')
            link = make_absolute_url(url, link_el.get('href') if link_el else '')
            if title and title != "제목" and not any(i['title'] == title for i in items):
                items.append({'title': title, 'img': img, 'link': link})
        if len(items) >= 5:
            break
    return items

def fetch_sej():
    """日本 7-Eleven 新品"""
    url = "https://www.sej.co.jp/products/a/newpage/"
    html = get_url(url)
    items = []
    if not html:
        return items
    soup = BeautifulSoup(html, 'html.parser')
    cards = soup.select('.list_inner, .item_launch')
    for card in cards:
        title_el = card.select_one('.item_ttl, .title, a')
        img_el = card.select_one('img')
        link_el = card.select_one('a')
        
        if title_el:
            title = title_el.get_text(strip=True)
            img = make_absolute_url(url, img_el.get('src') if img_el else '')
            link = make_absolute_url(url, link_el.get('href') if link_el else '')
            if title and not any(i['title'] == title for i in items):
                items.append({'title': title, 'img': img, 'link': link})
        if len(items) >= 5:
            break
    return items

def fetch_familymart():
    """日本 FamilyMart 全家新品"""
    url = "https://www.family.co.jp/goods/newgoods.html"
    html = get_url(url)
    items = []
    if not html:
        return items
    soup = BeautifulSoup(html, 'html.parser')
    cards = soup.select('.ly-mod-item-list li, .item-card')
    for card in cards:
        title_el = card.select_one('.ly-mod-item-name, .title')
        img_el = card.select_one('img')
        link_el = card.select_one('a')
        
        if title_el:
            title = title_el.get_text(strip=True)
            img = make_absolute_url(url, img_el.get('src') if img_el else '')
            link = make_absolute_url(url, link_el.get('href') if link_el else '')
            if title and not any(i['title'] == title for i in items):
                items.append({'title': title, 'img': img, 'link': link})
        if len(items) >= 5:
            break
    return items

# ==================== 主任务与数据导出 ====================

def main():
    print("开始抓取日韩泡面新品数据...")
    
    # 定义品牌及其对应抓取函数（已屏蔽/移除 Asahi, Kirin, Calbee, Ajinomoto, House 等非泡面品牌）
    brands = [
        {"name": "日清食品 (Nissin)", "fetcher": fetch_nissin},
        {"name": "东洋水产 (Maruchan)", "fetcher": fetch_maruchan},
        {"name": "明星食品 (Myojo)", "fetcher": fetch_myojo},
        {"name": "エースコック (Acecook)", "fetcher": fetch_acecook},
        {"name": "韩国三养 (Samyang)", "fetcher": fetch_samyang},
        {"name": "日本 7-11 新品", "fetcher": fetch_sej},
        {"name": "日本全家新品", "fetcher": fetch_familymart},
    ]

    result_data = {}
    
    for brand in brands:
        name = brand["name"]
        print(f"正在抓取: {name} ...")
        try:
            items = brand["fetcher"]()
            result_data[name] = items
            print(f"  -> 成功抓取到 {len(items)} 条数据")
        except Exception as e:
            print(f"  -> {name} 抓取时发生异常: {e}")
            result_data[name] = []

    # 获取当前东九区时间 (UTC+9)
    jst_time = datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M:%S")

    # 导出 json 供前端页面或者调试使用
    output = {
        "update_time": jst_time,
        "brands": result_data
    }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n抓取完成！数据已更新至 data.json，更新时间: {jst_time}")

if __name__ == "__main__":
    main()
