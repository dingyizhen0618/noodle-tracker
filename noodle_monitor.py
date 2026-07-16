import os
import datetime
import urllib3
import requests
from bs4 import BeautifulSoup

# 禁用安全请求警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 顶级浏览器伪装
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "ja,ko,en-US;q=0.9,en;q=0.8",
    "Connection": "keep-alive"
}

def safe_scrape(url, parser_func):
    """通用的安全爬取函数，自动识别日文、韩文编码，防止乱码"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=20, verify=False)
        # 自动识别日韩文等不同网页的编码格式
        if response.encoding == 'ISO-8859-1' or response.encoding is None:
            response.encoding = response.apparent_encoding
        else:
            response.encoding = 'utf-8'
            
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            return parser_func(soup)
        return [{"title": f"访问失败 (状态码: {response.status_code})", "link": url}]
    except Exception as e:
        return [{"title": f"连接超时或解析出错: {str(e)[:40]}", "link": url}]

# ==================== 🍜 原有 5 家公司解析规则 ====================

def parse_nissin(soup):
    results = []
    items = soup.select('.news-list-item a, .news-list a, article a, .news-title a')
    for item in items:
        title = item.get_text().strip()
        link = item.get('href', '')
        if title and len(title) > 8:
            if link and not link.startswith('http'):
                link = "https://www.nissin.com" + link
            results.append({"title": title, "link": link})
        if len(results) >= 6:
            break
    return results if results else [{"title": "前往日清官网新闻页", "link": "https://www.nissin.com/jp/company/news/"}]

def parse_toyosuisan(soup):
    results = []
    items = soup.select('.product-list-item a, .product-box a, .list-product a, a[href*="products/detail"]')
    if not items:
        items = soup.find_all('a', href=lambda x: x and 'products/detail' in x)
    for item in items:
        title = " ".join(item.get_text().split())
        link = item['href']
        if title and len(title) > 4 and "一覧" not in title:
            if not link.startswith('http'):
                link = "https://www.maruchan.co.jp" + link
            results.append({"title": title, "link": link})
        if len(results) >= 6:
            break
    return results if results else [{"title": "前往东洋水产新品页", "link": "https://www.maruchan.co.jp/products/"}]

def parse_myojo(soup):
    results = []
    items = soup.select('.news-list__item a, .news-item a, .news-list a')
    for item in items:
        title = item.get_text().strip()
        link = item['href']
        if title and len(title) > 5:
            if not link.startswith('http'):
                link = "https://www.myojofoods.co.jp" + link
            results.append({"title": title, "link": link})
        if len(results) >= 6:
            break
    return results if results else [{"title": "前往明星食品官网", "link": "https://www.myojofoods.co.jp/"}]

def parse_acecook(soup):
    results = []
    items = soup.select('main .arrival-list a, #contents .product-list a, .arrival-item a')
    if not items:
        items = soup.find_all('a', href=lambda x: x and 'products/detail' in x)
    for item in items:
        title = " ".join(item.get_text().strip().split())
        link = item['href']
        if title and len(title) > 4 and "詳細" not in title:
            if not link.startswith('http'):
                link = "https://www.acecook.co.jp" + link
            results.append({"title": title, "link": link})
        if len(results) >= 6:
            break
    return results if results else [{"title": "前往 Acecook 新着商品页", "link": "https://www.acecook.co.jp/products/arrival/"}]

def parse_asahi(soup):
    results = []
    items = soup.select('.news-release-list a, main a[href*="products"], #content a[href*="products"]')
    if not items:
        items = soup.find_all('a', href=lambda x: x and ('products/' in x or 'news/' in x))
    for item in items:
        title = item.get_text().strip()
        link = item['href']
        if title and len(title) > 6 and "一覧" not in title and "商品信息" not in title:
            if not link.startswith('http'):
                link = "https://www.asahiinryo.co.jp" + link
            results.append({"title": title, "link": link})
        if len(results) >= 6:
            break
    return results if results else [{"title": "前往朝日饮料新品页", "link": "https://www.asahiinryo.co.jp/products/new/"}]

# ==================== 🆕 新增 8 家公司解析规则 ====================

def parse_house(soup):
    # 好侍食品 (House Foods) 新闻页
    results = []
    items = soup.select('.news-list a, .release-list a, a[href*="newsrelease"]')
    for item in items:
        title = item.get_text().strip()
        link = item['href']
        if title and len(title) > 8:
            if not link.startswith('http'):
                link = "https://housefoods-group.com" + link
            results.append({"title": title, "link": link})
        if len(results) >= 6:
            break
    return results if results else [{"title": "前往好侍食品新闻页", "link": "https://housefoods-group.com/newsrelease/"}]

def parse_ajinomoto(soup):
    # 味之素 (Ajinomoto) 新闻页
    results = []
    items = soup.select('.press-list a, .news-list a, a[href*="press"]')
    for item in items:
        title = item.get_text().strip()
        link = item['href']
        if title and len(title) > 8:
            if not link.startswith('http'):
                link = "https://www.ajinomoto.co.jp" + link
            results.append({"title": title, "link": link})
        if len(results) >= 6:
            break
    return results if results else [{"title": "前往味之素新闻发布页", "link": "https://www.ajinomoto.co.jp/company/jp/pressrelease/"}]

def parse_seven_eleven(soup):
    # 日本 7-11 推荐新品
    results = []
    items = soup.select('.p-recommend__list a, .product-list a, a[href*="products/a/item"]')
    for item in items:
        title = " ".join(item.get_text().strip().split())
        link = item['href']
        if title and len(title) > 4:
            if not link.startswith('http'):
                link = "https://www.sej.co.jp" + link
            results.append({"title": title, "link": link})
        if len(results) >= 6:
            break
    return results if results else [{"title": "前往日本7-11新品页", "link": "https://www.sej.co.jp/products/a/thisweek/"}]

def parse_familymart(soup):
    # 日本全家 (FamilyMart) 今周新商品
    results = []
    items = soup.select('.goods-list a, .p-goods-list a, a[href*="goods/newgoods"]')
    for item in items:
        # 获取商品名（通常在 a 标签内部的 p 标签里）
        title = item.get_text().strip().replace('\n', ' ')
        title = " ".join(title.split())
        link = item['href']
        if title and len(title) > 4:
            if not link.startswith('http'):
                link = "https://www.family.co.jp" + link
            results.append({"title": title, "link": link})
        if len(results) >= 6:
            break
    return results if results else [{"title": "前往日本全家新品页", "link": "https://www.family.co.jp/goods/newgoods.html"}]

def parse_kirin(soup):
    # 麒麟饮料 (Kirin) 新闻发布页
    results = []
    items = soup.select('.news-list a, .release-list a, a[href*="news/press"]')
    for item in items:
        title = item.get_text().strip()
        link = item['href']
        if title and len(title) > 8:
            if not link.startswith('http'):
                link = "https://www.kirinholdings.com" + link
            results.append({"title": title, "link": link})
        if len(results) >= 6:
            break
    return results if results else [{"title": "前往麒麟集团新闻页", "link": "https://www.kirinholdings.com/jp/news/"}]

def parse_calbee(soup):
    # 卡乐比 (Calbee) 新商品页
    results = []
    items = soup.select('.product-list a, .new-product a, a[href*="products/detail"]')
    if not items:
         items = soup.find_all('a', href=lambda x: x and 'products/' in x)
    for item in items:
        title = item.get_text().strip()
        link = item['href']
        if title and len(title) > 4 and "一覧" not in title:
            if not link.startswith('http'):
                link = "https://www.calbee.co.jp" + link
            results.append({"title": title, "link": link})
        if len(results) >= 6:
            break
    return results if results else [{"title": "前往卡乐比新品页", "link": "https://www.calbee.co.jp/products/new/"}]

def parse_samyang(soup):
    # 韩国三养 (Samyang Foods) 新闻/新品页（韩文自动识别）
    results = []
    items = soup.select('.news-list a, .product-list a, a[href*="board/news"], a[href*="pm/detail"]')
    if not items:
        items = soup.find_all('a', href=lambda x: x and ('news' in x or 'product' in x))
    for item in items:
        title = " ".join(item.get_text().strip().split())
        link = item['href']
        if title and len(title) > 6 and "LIST" not in title:
            if not link.startswith('http'):
                link = "https://www.samyangfoods.com" + link
            results.append({"title": title, "link": link})
        if len(results) >= 6:
            break
    return results if results else [{"title": "前往三养食品官网", "link": "https://www.samyangfoods.com"}]

def parse_nongshim(soup):
    # 韩国农心 (Nongshim) 新商品页
    results = []
    items = soup.select('.news-list a, .product-list a, a[href*="news/dir"], a[href*="prd/list"]')
    if not items:
        items = soup.find_all('a', href=lambda x: x and 'prd/' in x)
    for item in items:
        title = " ".join(item.get_text().strip().split())
        link = item['href']
        if title and len(title) > 4 and "목록" not in title:
            if not link.startswith('http'):
                link = "https://www.nongshim.com" + link
            results.append({"title": title, "link": link})
        if len(results) >= 6:
            break
    return results if results else [{"title": "前往农心官网", "link": "https://www.nongshim.com"}]

# ==================== 🛠 主控制逻辑 ====================

def main():
    # 统一调度 13 个站点的抓取任务
    data = {
        # 原有 5 家
        "日清食品 (Nissin)": safe_scrape("https://www.nissin.com/jp/company/news/", parse_nissin),
        "东洋水产 (Maruchan)": safe_scrape("https://www.maruchan.co.jp/products/", parse_toyosuisan),
        "明星食品 (Myojo)": safe_scrape("https://www.myojofoods.co.jp/", parse_myojo),
        "エースコック (Acecook)": safe_scrape("https://www.acecook.co.jp/products/arrival/", parse_acecook),
        "朝日饮料 (Asahi)": safe_scrape("https://www.asahiinryo.co.jp/products/new/", parse_asahi),
        
        # 新增 8 家
        "好侍食品 (House)": safe_scrape("https://housefoods-group.com/newsrelease/", parse_house),
        "味之素 (Ajinomoto)": safe_scrape("https://www.ajinomoto.co.jp/company/jp/pressrelease/", parse_ajinomoto),
        "日本 7-11 (7-Eleven)": safe_scrape("https://www.sej.co.jp/products/a/thisweek/", parse_seven_eleven),
        "日本全家 (FamilyMart)": safe_scrape("https://www.family.co.jp/goods/newgoods.html", parse_familymart),
        "麒麟集团 (Kirin)": safe_scrape("https://www.kirinholdings.com/jp/news/", parse_kirin),
        "卡乐比 (Calbee)": safe_scrape("https://www.calbee.co.jp/products/new/", parse_calbee),
        "韩国三养 (Samyang)": safe_scrape("https://www.samyangfoods.com", parse_samyang),
        "韩国农心 (Nongshim)": safe_scrape("https://www.nongshim.com", parse_nongshim),
    }

    update_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 构建精美的响应式网页
    html_content = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🍜 全球食品/饮品新品情报站</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-50 text-gray-800 font-sans min-h-screen pb-12">
        <div class="max-w-7xl mx-auto px-4 py-8">
            <!-- 头部 -->
            <div class="text-center mb-10">
                <h1 class="text-4xl font-extrabold text-orange-600 mb-2">🍜 全球方便面/零食新品情报站</h1>
                <p class="text-gray-500">自动爬取日韩各大官网，吃货的第一手前线消息！</p>
                <span class="inline-block bg-orange-100 text-orange-800 text-xs px-3 py-1 rounded-full mt-4 font-semibold">
                    最后更新时间: {update_time} (每日自动刷新)
                </span>
            </div>

            <!-- 监控网格 -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
    """

    for company, items in data.items():
        html_content += f"""
                <div class="bg-white rounded-2xl shadow-sm hover:shadow-md transition duration-300 border border-gray-100 p-5 flex flex-col justify-between">
                    <div>
                        <h2 class="text-lg font-bold text-gray-900 border-b-2 border-orange-400 pb-2 mb-3 flex items-center justify-between">
                            <span>{company}</span>
                            <span class="flex h-2.5 w-2.5 relative">
                              <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                              <span class="relative inline-flex rounded-full h-2.5 w-2.5 bg-green-500"></span>
                            </span>
                        </h2>
                        <ul class="space-y-2.5">
        """
        for item in items:
            html_content += f"""
                            <li class="group">
                                <a href="{item['link']}" target="_blank" class="block text-xs text-gray-600 hover:text-orange-600 hover:underline transition duration-200 leading-relaxed">
                                    • {item['title']}
                                </a>
                            </li>
            """
        html_content += """
                        </ul>
                    </div>
                </div>
        """

    html_content += """
            </div>
            
            <!-- 页脚 -->
            <div class="text-center text-xs text-gray-400 mt-12">
                Powered by Gemini AI 🤖 | 每天自动拉取 13 家官网更新
            </div>
        </div>
    </body>
    </html>
    """

    # 保存网页文件
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("大满贯！13家公司的网页重新生成成功！")

if __name__ == "__main__":
    main()
