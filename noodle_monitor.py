import os
import json
import datetime
import urllib3
import requests
from bs4 import BeautifulSoup

# 禁用安全请求警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "ja,ko,zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive"
}

def send_wechat_notification(new_items):
    """通过 Server酱 自动发送微信服务通知/公众号弹窗"""
    serverchan_key = os.environ.get("SERVERCHAN_KEY")
    if not serverchan_key:
        print("未配置 SERVERCHAN_KEY，跳过微信推送。")
        return

    title = f"🍜 发现 {len(new_items)} 个重点品牌新品上新！"
    content = "### 🚨 最新抓取的重点品牌新品提醒：\n\n"
    
    for item in new_items:
        img_md = f"![{item['title']}]({item['image']})\n" if item.get('image') else ""
        content += f"* **[{item['company']}]** [{item['title']}]({item['link']})\n{img_md}\n"
        
    content += f"\n*发送时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"

    url = f"https://sctapi.ftqq.com/{serverchan_key}.send"
    data = {"title": title, "desp": content}
    try:
        res = requests.post(url, data=data, timeout=10)
        print("微信推送结果:", res.json())
    except Exception as e:
        print("微信推送失败:", e)

def safe_scrape(url, parser_func, custom_headers=None):
    headers = custom_headers if custom_headers else HEADERS
    try:
        response = requests.get(url, headers=headers, timeout=25, verify=False)
        if response.encoding == 'ISO-8859-1' or response.encoding is None:
            response.encoding = response.apparent_encoding
        else:
            response.encoding = 'utf-8'
            
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            return parser_func(soup, url)
        return [{"title": f"访问失败 ({response.status_code})", "link": url, "image": ""}]
    except Exception as e:
        return [{"title": f"连接超时: {str(e)[:20]}", "link": url, "image": ""}]

def make_absolute(link, base_url):
    if not link:
        return ""
    if link.startswith('http'):
        return link
    if link.startswith('//'):
        return "https:" + link
    if link.startswith('/'):
        from urllib.parse import urlparse
        parsed = urlparse(base_url)
        return f"{parsed.scheme}://{parsed.netloc}{link}"
    return base_url.rsplit('/', 1)[0] + '/' + link

def extract_img(element, base_url):
    """从 HTML 节点中提取第一张缩略图"""
    img_tag = element.find('img') if element else None
    if img_tag:
        src = img_tag.get('src') or img_tag.get('data-src') or img_tag.get('data-original') or ""
        return make_absolute(src, base_url)
    return ""

# ==================== 各家解析规则 (带图片提取) ====================

def parse_nissin(soup, base_url):
    results = []
    items = soup.select('.news-list-item, .news-list li, article, .news-title-box')
    if not items:
        items = soup.select('.news-list-item a, .news-list a, article a, .news-title a')
    for item in items:
        a_tag = item if item.name == 'a' else item.find('a')
        if not a_tag: continue
        title = a_tag.get_text().strip()
        link = make_absolute(a_tag.get('href', ''), base_url)
        img = extract_img(item, base_url)
        if title and len(title) > 8:
            results.append({"title": title, "link": link, "image": img})
        if len(results) >= 5: break
    return results if results else [{"title": "日清官网新闻页", "link": base_url, "image": ""}]

def parse_toyosuisan(soup, base_url):
    results = []
    items = soup.select('.product-list-item, .product-box, .list-product, li')
    for item in items:
        a_tag = item.find('a', href=True)
        if not a_tag: continue
        title = " ".join(a_tag.get_text().split())
        link = make_absolute(a_tag.get('href', ''), base_url)
        img = extract_img(item, base_url)
        if title and len(title) > 4 and "一覧" not in title and "products/detail" in link:
            results.append({"title": title, "link": link, "image": img})
        if len(results) >= 5: break
    return results if results else [{"title": "东洋水产新品页", "link": base_url, "image": ""}]

def parse_myojo(soup, base_url):
    results = []
    items = soup.select('.news-list__item, .news-item, li')
    for item in items:
        a_tag = item.find('a', href=True)
        if not a_tag: continue
        title = a_tag.get_text().strip()
        link = make_absolute(a_tag.get('href', ''), base_url)
        img = extract_img(item, base_url)
        if title and len(title) > 5:
            results.append({"title": title, "link": link, "image": img})
        if len(results) >= 5: break
    return results if results else [{"title": "明星食品官网", "link": base_url, "image": ""}]

def parse_acecook(soup, base_url):
    results = []
    items = soup.select('.arrival-list li, .product-list li, .arrival-item')
    for item in items:
        a_tag = item.find('a', href=True)
        if not a_tag: continue
        title = " ".join(a_tag.get_text().strip().split())
        link = make_absolute(a_tag.get('href', ''), base_url)
        img = extract_img(item, base_url)
        if title and len(title) > 4 and "詳細" not in title:
            results.append({"title": title, "link": link, "image": img})
        if len(results) >= 5: break
    return results if results else [{"title": "Acecook 新着商品页", "link": base_url, "image": ""}]

def parse_asahi(soup, base_url):
    results = []
    items = soup.select('.news-release-list li, .product-list li, article')
    for item in items:
        a_tag = item.find('a', href=True)
        if not a_tag: continue
        title = a_tag.get_text().strip()
        link = make_absolute(a_tag.get('href', ''), base_url)
        img = extract_img(item, base_url)
        if title and len(title) > 6 and "一覧" not in title:
            results.append({"title": title, "link": link, "image": img})
        if len(results) >= 5: break
    return results if results else [{"title": "朝日饮料新品页", "link": base_url, "image": ""}]

def parse_house(soup, base_url):
    results = []
    items = soup.select('.news-list li, .release-list li, article')
    for item in items:
        a_tag = item.find('a', href=True)
        if not a_tag: continue
        title = a_tag.get_text().strip()
        link = make_absolute(a_tag.get('href', ''), base_url)
        img = extract_img(item, base_url)
        if title and len(title) > 8:
            results.append({"title": title, "link": link, "image": img})
        if len(results) >= 5: break
    return results if results else [{"title": "好侍食品新闻页", "link": base_url, "image": ""}]

def parse_ajinomoto(soup, base_url):
    results = []
    items = soup.select('.press-list li, .news-list li, .c-list__item')
    for item in items:
        a_tag = item.find('a', href=True)
        if not a_tag: continue
        title = " ".join(a_tag.get_text().strip().split())
        link = make_absolute(a_tag.get('href', ''), base_url)
        img = extract_img(item, base_url)
        if title and len(title) > 6:
            results.append({"title": title, "link": link, "image": img})
        if len(results) >= 5: break
    return results if results else [{"title": "味之素新闻发布页", "link": base_url, "image": ""}]

def parse_seven_eleven(soup, base_url):
    results = []
    items = soup.select('.p-recommend__list .item, .product-list li, .item_inner')
    for item in items:
        a_tag = item.find('a', href=True)
        if not a_tag: continue
        title = " ".join(a_tag.get_text().strip().split())
        link = make_absolute(a_tag.get('href', ''), base_url)
        img = extract_img(item, base_url)
        if title and len(title) > 4:
            results.append({"title": title, "link": link, "image": img})
        if len(results) >= 5: break
    return results if results else [{"title": "日本7-11新品页", "link": base_url, "image": ""}]

def parse_familymart(soup, base_url):
    results = []
    items = soup.select('.goods-list li, .p-goods-list li, .ly-mod-goods-list li')
    for item in items:
        a_tag = item.find('a', href=True)
        if not a_tag: continue
        title = " ".join(a_tag.get_text().strip().split())
        link = make_absolute(a_tag.get('href', ''), base_url)
        img = extract_img(item, base_url)
        if title and len(title) > 4:
            results.append({"title": title, "link": link, "image": img})
        if len(results) >= 5: break
    return results if results else [{"title": "日本全家新品页", "link": base_url, "image": ""}]

def parse_kirin(soup, base_url):
    results = []
    items = soup.select('.news-list li, .release-list li, .c-card')
    for item in items:
        a_tag = item.find('a', href=True)
        if not a_tag: continue
        title = " ".join(a_tag.get_text().strip().split())
        link = make_absolute(a_tag.get('href', ''), base_url)
        img = extract_img(item, base_url)
        if title and len(title) > 8:
            results.append({"title": title, "link": link, "image": img})
        if len(results) >= 5: break
    return results if results else [{"title": "麒麟集团新闻页", "link": base_url, "image": ""}]

def parse_calbee(soup, base_url):
    results = []
    items = soup.select('.p-product-list__item, .product-list li, .new-product li')
    for item in items:
        a_tag = item.find('a', href=True)
        if not a_tag: continue
        title = " ".join(a_tag.get_text().strip().split())
        link = make_absolute(a_tag.get('href', ''), base_url)
        img = extract_img(item, base_url)
        if title and len(title) > 3 and "一覧" not in title:
            results.append({"title": title, "link": link, "image": img})
        if len(results) >= 5: break
    return results if results else [{"title": "卡乐比新品页", "link": base_url, "image": ""}]

def parse_samyang(soup, base_url):
    results = []
    items = soup.select('.news-list li, .product-list li, li')
    for item in items:
        a_tag = item.find('a', href=True)
        if not a_tag: continue
        title = " ".join(a_tag.get_text().strip().split())
        link = make_absolute(a_tag.get('href', ''), base_url)
        img = extract_img(item, base_url)
        if title and len(title) > 6 and ("board/news" in link or "pm/detail" in link):
            results.append({"title": title, "link": link, "image": img})
        if len(results) >= 5: break
    return results if results else [{"title": "三养食品官网", "link": base_url, "image": ""}]

def parse_nongshim(soup, base_url):
    results = []
    items = soup.select('.news-list li, .product-list li, .prd-list li')
    for item in items:
        a_tag = item.find('a', href=True)
        if not a_tag: continue
        title = " ".join(a_tag.get_text().strip().split())
        link = make_absolute(a_tag.get('href', ''), base_url)
        img = extract_img(item, base_url)
        if title and len(title) > 3 and ("news/dir" in link or "prd/list" in link):
            results.append({"title": title, "link": link, "image": img})
        if len(results) >= 5: break
    return results if results else [{"title": "农心官网", "link": base_url, "image": ""}]

# ==================== ⚙️ 主程序与 HTML 生成 ====================

def main():
    kirin_headers = HEADERS.copy()
    kirin_headers["Referer"] = "https://www.kirinholdings.com/"
    
    ajinomoto_headers = HEADERS.copy()
    ajinomoto_headers["Referer"] = "https://www.ajinomoto.co.jp/"

    data = {
        "日清食品 (Nissin)": safe_scrape("https://www.nissin.com/jp/company/news/", parse_nissin),
        "东洋水产 (Maruchan)": safe_scrape("https://www.maruchan.co.jp/products/", parse_toyosuisan),
        "明星食品 (Myojo)": safe_scrape("https://www.myojofoods.co.jp/", parse_myojo),
        "エースコック (Acecook)": safe_scrape("https://www.acecook.co.jp/products/arrival/", parse_acecook),
        "朝日饮料 (Asahi)": safe_scrape("https://www.asahiinryo.co.jp/products/new/", parse_asahi),
        "好侍食品 (House)": safe_scrape("https://housefoods-group.com/newsrelease/", parse_house),
        "味之素 (Ajinomoto)": safe_scrape("https://www.ajinomoto.co.jp/company/jp/pressrelease/", parse_ajinomoto, custom_headers=ajinomoto_headers),
        "日本 7-11": safe_scrape("https://www.sej.co.jp/products/a/thisweek/", parse_seven_eleven),
        "日本全家": safe_scrape("https://www.family.co.jp/goods/newgoods.html", parse_familymart),
        "麒麟集团 (Kirin)": safe_scrape("https://www.kirinholdings.com/jp/news/", parse_kirin, custom_headers=kirin_headers),
        "卡乐比 (Calbee)": safe_scrape("https://www.calbee.co.jp/products/new/", parse_calbee),
        "韩国三养 (Samyang)": safe_scrape("https://www.samyangfoods.com", parse_samyang),
        "韩国农心 (Nongshim)": safe_scrape("https://www.nongshim.com", parse_nongshim),
    }

    history_file = "history.json"
    old_history = {}
    if os.path.exists(history_file):
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                old_history = json.load(f)
        except Exception:
            old_history = {}

    new_items_to_notify = []
    new_history = {}

    for company, items in data.items():
        new_history[company] = [item['title'] for item in items]
        old_titles = old_history.get(company, [])
        
        if old_titles: 
            for item in items:
                if item['title'] not in old_titles and "前往" not in item['title'] and "访问失败" not in item['title']:
                    new_items_to_notify.append({"company": company, "title": item['title'], "link": item['link'], "image": item.get('image', '')})

    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(new_history, f, ensure_ascii=False, indent=2)

    if new_items_to_notify:
        print(f"检测到 {len(new_items_to_notify)} 个新动态，正在发送微信提醒...")
        send_wechat_notification(new_items_to_notify)
    else:
        print("暂无新上新动态。")

    update_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🍜 全球食品/饮品新品情报站</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .product-card {{
            transition: transform 0.2s ease, shadow 0.2s ease;
        }}
        .product-card:hover {{
            transform: translateY(-2px);
        }}
    </style>
</head>
<body class="bg-gray-50 text-gray-800 font-sans min-h-screen pb-16">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <!-- Header Section -->
        <div class="text-center mb-12">
            <h1 class="text-3xl sm:text-4xl font-extrabold text-orange-600 tracking-tight mb-2">🍜 全球方便面/食品新品情报站</h1>
            <p class="text-sm sm:text-base text-gray-500 max-w-xl mx-auto">自动巡逻重点品牌官网 · 直观展示新品名称与商品缩略图</p>
            <div class="mt-4 inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-800">
                <span class="w-2 h-2 mr-2 bg-green-500 rounded-full animate-pulse"></span>
                更新时间: {update_time} (微信通知就绪)
            </div>
        </div>

        <!-- Brands Grid -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
"""
    for company, items in data.items():
        html_content += f"""
            <!-- Brand Card -->
            <div class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden flex flex-col justify-between">
                <div class="p-5">
                    <div class="flex items-center justify-between border-b border-gray-100 pb-3 mb-4">
                        <h2 class="text-base font-bold text-gray-900 tracking-tight">{company}</h2>
                        <span class="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">{len(items)} 个新动态</span>
                    </div>
                    <div class="space-y-4">
"""
        for item in items:
            img_html = f'<img src="{item["image"]}" alt="{item["title"]}" class="w-16 h-16 object-cover rounded-lg border border-gray-100 flex-shrink-0 bg-gray-50 mr-3" loading="lazy" onerror="this.style.display=\'none\'">' if item.get('image') else ''
            html_content += f"""
                        <a href="{item['link']}" target="_blank" class="product-card flex items-start p-2 rounded-xl hover:bg-orange-50/60 transition duration-150 group">
                            {img_html}
                            <div class="flex-1 min-w-0">
                                <p class="text-xs font-semibold text-gray-800 group-hover:text-orange-600 line-clamp-2 leading-snug">
                                    {item['title']}
                                </p>
                            </div>
                        </a>
"""
        html_content += """
                    </div>
                </div>
            </div>
"""

    html_content += """
        </div>
    </div>
</body>
</html>
"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

if __name__ == "__main__":
    main()
