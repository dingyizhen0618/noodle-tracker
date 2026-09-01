import os
import json
import datetime
import urllib3
import requests
from bs4 import BeautifulSoup

# 禁用安全请求警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 全局浏览器伪装
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

    # 构建微信消息内容 (Markdown 格式)
    title = f"🍜 发现 {len(new_items)} 个日韩食品新品上新！"
    content = "### 🚨 最新抓取的重点品牌新品提醒：\n\n"
    
    for item in new_items:
        content += f"* **[{item['company']}]** [{item['title']}]({item['link']})\n"
        
    content += f"\n\n*发送时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"

    # 发送请求给 Server酱 API
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
            return parser_func(soup)
        return [{"title": f"访问失败 ({response.status_code})", "link": url}]
    except Exception as e:
        return [{"title": f"连接超时: {str(e)[:20]}", "link": url}]

# ==================== 各家解析规则 (保持稳健) ====================

def parse_nissin(soup):
    results = []
    items = soup.select('.news-list-item a, .news-list a, article a, .news-title a')
    for item in items:
        title = item.get_text().strip()
        link = item.get('href', '')
        if title and len(title) > 8:
            if link and not link.startswith('http'): link = "https://www.nissin.com" + link
            results.append({"title": title, "link": link})
        if len(results) >= 5: break
    return results if results else [{"title": "日清官网新闻页", "link": "https://www.nissin.com/jp/company/news/"}]

def parse_toyosuisan(soup):
    results = []
    items = soup.select('.product-list-item a, .product-box a, .list-product a, a[href*="products/detail"]')
    for item in items:
        title = " ".join(item.get_text().split())
        link = item.get('href', '')
        if title and len(title) > 4 and "一覧" not in title:
            if not link.startswith('http'): link = "https://www.maruchan.co.jp" + link
            results.append({"title": title, "link": link})
        if len(results) >= 5: break
    return results if results else [{"title": "东洋水产新品页", "link": "https://www.maruchan.co.jp/products/"}]

def parse_myojo(soup):
    results = []
    items = soup.select('.news-list__item a, .news-item a, .news-list a')
    for item in items:
        title = item.get_text().strip()
        link = item.get('href', '')
        if title and len(title) > 5:
            if not link.startswith('http'): link = "https://www.myojofoods.co.jp" + link
            results.append({"title": title, "link": link})
        if len(results) >= 5: break
    return results if results else [{"title": "明星食品官网", "link": "https://www.myojofoods.co.jp/"}]

def parse_acecook(soup):
    results = []
    items = soup.select('main .arrival-list a, #contents .product-list a, .arrival-item a')
    for item in items:
        title = " ".join(item.get_text().strip().split())
        link = item.get('href', '')
        if title and len(title) > 4 and "詳細" not in title:
            if not link.startswith('http'): link = "https://www.acecook.co.jp" + link
            results.append({"title": title, "link": link})
        if len(results) >= 5: break
    return results if results else [{"title": "Acecook 新着商品页", "link": "https://www.acecook.co.jp/products/arrival/"}]

def parse_asahi(soup):
    results = []
    items = soup.select('.news-release-list a, main a[href*="products"], #content a[href*="products"]')
    for item in items:
        title = item.get_text().strip()
        link = item.get('href', '')
        if title and len(title) > 6 and "一覧" not in title:
            if not link.startswith('http'): link = "https://www.asahiinryo.co.jp" + link
            results.append({"title": title, "link": link})
        if len(results) >= 5: break
    return results if results else [{"title": "朝日饮料新品页", "link": "https://www.asahiinryo.co.jp/products/new/"}]

def parse_house(soup):
    results = []
    items = soup.select('.news-list a, .release-list a, a[href*="newsrelease"]')
    for item in items:
        title = item.get_text().strip()
        link = item.get('href', '')
        if title and len(title) > 8:
            if not link.startswith('http'): link = "https://housefoods-group.com" + link
            results.append({"title": title, "link": link})
        if len(results) >= 5: break
    return results if results else [{"title": "好侍食品新闻页", "link": "https://housefoods-group.com/newsrelease/"}]

def parse_ajinomoto(soup):
    results = []
    items = soup.select('.press-list a, .news-list a, .c-list__item a, a[href*="company/jp/pressrelease"]')
    for item in items:
        title = " ".join(item.get_text().strip().split())
        link = item.get('href', '')
        if title and len(title) > 6:
            if link and not link.startswith('http'): link = "https://www.ajinomoto.co.jp" + link
            results.append({"title": title, "link": link})
        if len(results) >= 5: break
    return results if results else [{"title": "味之素新闻发布页", "link": "https://www.ajinomoto.co.jp/company/jp/pressrelease/"}]

def parse_seven_eleven(soup):
    results = []
    items = soup.select('.p-recommend__list a, .product-list a, a[href*="products/a/item"]')
    for item in items:
        title = " ".join(item.get_text().strip().split())
        link = item.get('href', '')
        if title and len(title) > 4:
            if not link.startswith('http'): link = "https://www.sej.co.jp" + link
            results.append({"title": title, "link": link})
        if len(results) >= 5: break
    return results if results else [{"title": "日本7-11新品页", "link": "https://www.sej.co.jp/products/a/thisweek/"}]

def parse_familymart(soup):
    results = []
    items = soup.select('.goods-list a, .p-goods-list a, a[href*="goods/newgoods"]')
    for item in items:
        title = " ".join(item.get_text().strip().split())
        link = item.get('href', '')
        if title and len(title) > 4:
            if not link.startswith('http'): link = "https://www.family.co.jp" + link
            results.append({"title": title, "link": link})
        if len(results) >= 5: break
    return results if results else [{"title": "日本全家新品页", "link": "https://www.family.co.jp/goods/newgoods.html"}]

def parse_kirin(soup):
    results = []
    items = soup.select('.news-list a, .release-list a, .c-card-link, a[href*="news/press"]')
    for item in items:
        title = " ".join(item.get_text().strip().split())
        link = item.get('href', '')
        if title and len(title) > 8:
            if link and not link.startswith('http'): link = "https://www.kirinholdings.com" + link
            results.append({"title": title, "link": link})
        if len(results) >= 5: break
    return results if results else [{"title": "麒麟集团新闻页", "link": "https://www.kirinholdings.com/jp/news/"}]

def parse_calbee(soup):
    results = []
    items = soup.select('.p-product-list__item a, .product-list a, .new-product a, a[href*="products/detail"]')
    for item in items:
        title = " ".join(item.get_text().strip().split())
        link = item.get('href', '')
        if title and len(title) > 3 and "一覧" not in title:
            if link and not link.startswith('http'): link = "https://www.calbee.co.jp" + link
            results.append({"title": title, "link": link})
        if len(results) >= 5: break
    return results if results else [{"title": "卡乐比新品页", "link": "https://www.calbee.co.jp/products/new/"}]

def parse_samyang(soup):
    results = []
    items = soup.select('.news-list a, .product-list a, a[href*="board/news"], a[href*="pm/detail"]')
    for item in items:
        title = " ".join(item.get_text().strip().split())
        link = item.get('href', '')
        if title and len(title) > 6:
            if not link.startswith('http'): link = "https://www.samyangfoods.com" + link
            results.append({"title": title, "link": link})
        if len(results) >= 5: break
    return results if results else [{"title": "三养食品官网", "link": "https://www.samyangfoods.com"}]

def parse_nongshim(soup):
    results = []
    items = soup.select('.news-list a, .product-list a, .prd-list a, a[href*="news/dir"], a[href*="prd/list"]')
    for item in items:
        title = " ".join(item.get_text().strip().split())
        link = item.get('href', '')
        if title and len(title) > 3:
            if link and not link.startswith('http'): link = "https://www.nongshim.com" + link
            results.append({"title": title, "link": link})
        if len(results) >= 5: break
    return results if results else [{"title": "农心官网", "link": "https://www.nongshim.com"}]

# ==================== ⚙️ 变动比对与主程序 ====================

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

    #读取上次记录的历史数据历史文件
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

    # 比对新旧数据
    for company, items in data.items():
        new_history[company] = [item['title'] for item in items]
        old_titles = old_history.get(company, [])
        
        # 如果不是第一次运行，且抓到了不在历史记录里的标题，则记为“新品上新”
        if old_titles: 
            for item in items:
                # 排除提示性信息
                if item['title'] not in old_titles and "前往" not in item['title'] and "访问失败" not in item['title']:
                    new_items_to_notify.append({"company": company, "title": item['title'], "link": item['link']})

    # 保存最新历史记录
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(new_history, f, ensure_ascii=False, indent=2)

    # 如果有新发现，发送微信提醒！
    if new_items_to_notify:
        print(f"检测到 {len(new_items_to_notify)} 个新动态，正在发送微信提醒...")
        send_wechat_notification(new_items_to_notify)
    else:
        print("暂无新上新动态。")

    # 生成 HTML 网页
    update_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
            <div class="text-center mb-10">
                <h1 class="text-4xl font-extrabold text-orange-600 mb-2">🍜 全球方便面/零食新品情报站</h1>
                <p class="text-gray-500">自动巡逻 + 微信同步强提醒</p>
                <span class="inline-block bg-orange-100 text-orange-800 text-xs px-3 py-1 rounded-full mt-4 font-semibold">
                    更新时间: {update_time} (微信弹窗已就绪)
                </span>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
    """
    for company, items in data.items():
        html_content += f"""
                <div class="bg-white rounded-2xl shadow-sm hover:shadow-md transition duration-300 border border-gray-100 p-5">
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
                            <a href="{item['link']}" target="_blank" class="block text-xs text-gray-600 hover:text-orange-600 hover:underline transition duration-200">
                                • {item['title']}
                            </a>
                        </li>
            """
        html_content += "</ul></div>"

    html_content += "</div></div></body></html>"

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

if __name__ == "__main__":
    main()
