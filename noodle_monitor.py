import os
import datetime
import urllib3
import requests
from bs4 import BeautifulSoup

# 禁用安全请求警告（针对部分网站忽略SSL证书时使用）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 升级版浏览器伪装，模仿真实的电脑请求，防止被东洋水产等阻断
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

def safe_scrape(url, parser_func):
    """通用的安全爬取函数，支持自动编码识别，忽略SSL证书报错"""
    try:
        # verify=False 忽略证书校验，增加 timeout 防止卡死
        response = requests.get(url, headers=HEADERS, timeout=20, verify=False)
        
        # 核心修复：自动检测网页的真实编码（解决朝日饮料乱码问题）
        if response.encoding == 'ISO-8859-1' or response.encoding is None:
            response.encoding = response.apparent_encoding
        else:
            response.encoding = 'utf-8' # 默认尝试使用 utf-8
            
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            return parser_func(soup)
        return [{"title": f"访问失败 (状态码: {response.status_code})", "link": url}]
    except Exception as e:
        return [{"title": f"连接超时或解析出错: {str(e)[:40]}", "link": url}]

# --- 精准定位解析规则 ---

def parse_nissin(soup):
    # 日清食品新闻发布页
    results = []
    # 缩小范围到新闻列表容器中
    items = soup.select('.news-list-item a, .news-list a, article a')
    for item in items:
        title = item.get_text().strip()
        link = item.get('href', '')
        if title and len(title) > 10: # 过滤掉极短的分类标签
            if link and not link.startswith('http'):
                link = "https://www.nissin.com" + link
            results.append({"title": title, "link": link})
        if len(results) >= 6:
            break
    return results if results else [{"title": "日清官网排版微调，建议直接点击查看", "link": "https://www.nissin.com/jp/company/news/"}]

def parse_toyosuisan(soup):
    # 东洋水产商品页
    results = []
    # 精准定位：只找包含在商品卡片内的链接
    items = soup.select('.product-list-item a, .product-box a, .list-product a, a[href*="products/detail"]')
    if not items:
        # 备用方案：寻找带有特定产品标识的链接
        items = soup.find_all('a', href=lambda x: x and 'products/detail' in x)
    
    for item in items:
        # 去除多余的空格和换行
        title = " ".join(item.get_text().split())
        link = item['href']
        if title and len(title) > 4 and "一覧" not in title:
            if not link.startswith('http'):
                link = "https://www.maruchan.co.jp" + link
            results.append({"title": title, "link": link})
        if len(results) >= 6:
            break
    return results if results else [{"title": "点击前往东洋水产新品页", "link": "https://www.maruchan.co.jp/products/"}]

def parse_myojo(soup):
    # 明星食品
    results = []
    # 定位至新闻区块
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
    return results if results else [{"title": "点击前往明星食品官网", "link": "https://www.myojofoods.co.jp/"}]

def parse_acecook(soup):
    # Acecook 新着商品 (避开头部和页脚导航)
    results = []
    # 精准定位到新商品主内容区域下的列表
    items = soup.select('main .arrival-list a, #contents .product-list a, .arrival-item a')
    if not items:
        # 备用：查找页面中所有带有 products/detail 路径的链接，这类必然是商品
        items = soup.find_all('a', href=lambda x: x and 'products/detail' in x)
        
    for item in items:
        # 提取商品名字，避开图片占位符或空标签
        title = item.get_text().strip().replace('\n', ' ')
        title = " ".join(title.split()) # 清理多余空格
        link = item['href']
        if title and len(title) > 4 and "詳細" not in title:
            if not link.startswith('http'):
                link = "https://www.acecook.co.jp" + link
            results.append({"title": title, "link": link})
        if len(results) >= 6:
            break
    return results if results else [{"title": "点击前往 Acecook 新着商品页", "link": "https://www.acecook.co.jp/products/arrival/"}]

def parse_asahi(soup):
    # 朝日饮料新品 (避开全局导航)
    results = []
    # 锁定在主要的文章列表、或者包含新品新闻发布的区域
    items = soup.select('.news-release-list a, main a[href*="products"], #content a[href*="products"]')
    if not items:
        items = soup.find_all('a', href=lambda x: x and ('products/' in x or 'news/' in x))
        
    for item in items:
        title = item.get_text().strip()
        link = item['href']
        if title and len(title) > 6 and "一覧" not in title and "商品情報" not in title:
            if not link.startswith('http'):
                link = "https://www.asahiinryo.co.jp" + link
            results.append({"title": title, "link": link})
        if len(results) >= 6:
            break
    return results if results else [{"title": "点击前往朝日饮料新品页", "link": "https://www.asahiinryo.co.jp/products/new/"}]

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

    # 保存为网页文件
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("网页重新生成成功！")

if __name__ == "__main__":
    main()
