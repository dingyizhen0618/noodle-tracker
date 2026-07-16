import os
import datetime
import requests
from bs4 import BeautifulSoup

# 伪装成浏览器，防止被网站拦截
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8"
}

def safe_scrape(url, parser_func):
    """通用的安全爬取函数，即使某个网站挂了，也不会影响其他网站的更新"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.encoding = 'utf-8'
        if response.status_code == 200:
            return parser_func(BeautifulSoup(response.text, 'html.parser'))
        return [{"title": f"访问失败 (状态码: {response.status_code})", "link": url}]
    except Exception as e:
        return [{"title": f"连接超时或解析出错: {str(e)[:30]}...", "link": url}]

# --- 各大官网的具体解析规则 ---

def parse_nissin(soup):
    # 日清食品新闻发布页
    results = []
    items = soup.select('.news-list-item, .news-title, article a') # 兼容多种可能的标签
    for item in items[:6]:
        title = item.get_text().strip()
        link = item.get('href', '')
        if title and len(title) > 5:
            if link and not link.startswith('http'):
                link = "https://www.nissin.com" + link
            results.append({"title": title, "link": link or "https://www.nissin.com/jp/company/news/"})
    return results if results else [{"title": "暂无更新，建议前往官网查看", "link": "https://www.nissin.com/jp/company/news/"}]

def parse_toyosuisan(soup):
    # 东洋水产商品页
    results = []
    items = soup.select('.product-list a, .list-product a, a[href*="products/detail"]')
    if not items: # 备用：抓取页面中前几个商品链接
        items = soup.find_all('a', href=True)[:10]
    for item in items:
        title = item.get_text().strip()
        link = item['href']
        if title and len(title) > 5:
            if not link.startswith('http'):
                link = "https://www.maruchan.co.jp" + link
            results.append({"title": title, "link": link})
        if len(results) >= 6:
            break
    return results if results else [{"title": "暂无新商品更新，点击前往官网", "link": "https://www.maruchan.co.jp/products/"}]

def parse_myojo(soup):
    # 明星食品
    results = []
    items = soup.select('.news-list a, .news-item a, a[href*="news"]')
    for item in items[:6]:
        title = item.get_text().strip()
        link = item['href']
        if title and len(title) > 5:
            if not link.startswith('http'):
                link = "https://www.myojofoods.co.jp" + link
            results.append({"title": title, "link": link})
    return results if results else [{"title": "暂无新商品更新，点击前往官网", "link": "https://www.myojofoods.co.jp/"}]

def parse_acecook(soup):
    # Acecook 新着商品
    results = []
    items = soup.select('.arrival-list a, .product-list a, a[href*="products/detail"]')
    if not items:
        items = soup.find_all('a', href=True)[:8]
    for item in items:
        title = item.get_text().strip().replace('\n', ' ')
        link = item['href']
        if title and len(title) > 5:
            if not link.startswith('http'):
                link = "https://www.acecook.co.jp" + link
            results.append({"title": title, "link": link})
        if len(results) >= 6:
            break
    return results if results else [{"title": "暂无新商品更新，点击前往官网", "link": "https://www.acecook.co.jp/products/arrival/"}]

def parse_asahi(soup):
    # 朝日饮料新品
    results = []
    items = soup.select('.news-release-list a, .product-list a, a[href*="products"]')
    if not items:
        items = soup.find_all('a', href=True)[:8]
    for item in items:
        title = item.get_text().strip()
        link = item['href']
        if title and len(title) > 5:
            if not link.startswith('http'):
                link = "https://www.asahiinryo.co.jp" + link
            results.append({"title": title, "link": link})
        if len(results) >= 6:
            break
    return results if results else [{"title": "暂无新商品更新，点击前往官网", "link": "https://www.asahiinryo.co.jp/products/new/"}]

# --- 主程序：抓取并生成网页 ---

def main():
    data = {
        "东洋水产 (Maruchan)": safe_scrape("https://www.maruchan.co.jp/products/", parse_toyosuisan),
        "日清食品 (Nissin)": safe_scrape("https://www.nissin.com/jp/company/news/", parse_nissin),
        "明星食品 (Myojo)": safe_scrape("https://www.myojofoods.co.jp/", parse_myojo),
        "エースコック (Acecook)": safe_scrape("https://www.acecook.co.jp/products/arrival/", parse_acecook),
        "朝日饮料 (Asahi)": safe_scrape("https://www.asahiinryo.co.jp/products/new/", parse_asahi),
    }

    update_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 构建精美的 Tailwind CSS 网页
    html_content = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🍜 日系食品/饮品新品监控站</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-50 text-gray-800 font-sans min-h-screen pb-12">
        <div class="max-w-6xl mx-auto px-4 py-8">
            <!-- 头部 -->
            <div class="text-center mb-10">
                <h1 class="text-4xl font-extrabold text-orange-600 mb-2">🍜 日系方便面/饮品新品情报站</h1>
                <p class="text-gray-500">自动爬取各大官网最新发布，吃货必备！</p>
                <span class="inline-block bg-orange-100 text-orange-800 text-xs px-3 py-1 rounded-full mt-4 font-semibold">
                    最后更新时间: {update_time} (每日自动刷新)
                </span>
            </div>

            <!-- 监控网格 -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    """

    for company, items in data.items():
        html_content += f"""
                <div class="bg-white rounded-2xl shadow-sm hover:shadow-md transition duration-300 border border-gray-100 p-6">
                    <h2 class="text-xl font-bold text-gray-900 border-b-2 border-orange-400 pb-2 mb-4 flex items-center justify-between">
                        <span>{company}</span>
                        <span class="flex h-3 w-3 relative">
                          <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                          <span class="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
                        </span>
                    </h2>
                    <ul class="space-y-3">
        """
        for item in items:
            html_content += f"""
                        <li class="group">
                            <a href="{item['link']}" target="_blank" class="block text-sm text-gray-600 hover:text-orange-600 hover:underline transition duration-200 leading-relaxed">
                                • {item['title']}
                            </a>
                        </li>
            """
        html_content += """
                    </ul>
                </div>
        """

    html_content += """
            </div>
            
            <!-- 页脚 -->
            <div class="text-center text-xs text-gray-400 mt-12">
                Powered by Gemini AI 🤖 | 每天定时自动拉取更新
            </div>
        </div>
    </body>
    </html>
    """

    # 保存为本地网页
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("网页生成成功！生成的文件名为 index.html")

if __name__ == "__main__":
    main()
