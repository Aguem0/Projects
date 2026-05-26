"""
zhongbei.py - 中北大学招生爬虫模块
本模块用于从指定网页中提取招生计划图片，进行本地OCR识别后插入数据库

版本: Python3.9 / PaddleOCR2.7.0.3 / PaddlePaddle2.6.2 / NumPy1.26.4

主要功能：
1. 爬取目标网页中<p style="text-align: center">标签下的img图片
2. 下载图片到本地指定文件夹
3. 对本地图片进行OCR识别
4. 将识别文字结果插入MySQL数据库

目标网址：https://zbzs.nuc.edu.cn/info/1016/3805.htm

数据库表结构：学院代码, 学院名称, 专业名称, 选考科目
"""

import requests
from bs4 import BeautifulSoup
import re
import time
import os
import hashlib
from urllib.parse import urlparse, parse_qs
import dp_config
import db_helper
import data_cleaner
from ocr_processor import init_paddleocr, get_ocr_engine
from data_cleaner import TableParser


class ZhongbeiCrawler:
    """
    中北大学招生爬虫类

    核心功能：
    - 从目标网页提取招生计划图片
    - 下载图片到本地并进行OCR识别
    - 将识别结果插入数据库（学院代码, 学院名称, 专业名称, 选考科目）
    """

    def __init__(self):
        """
        初始化爬虫配置
        """
        self.config = dp_config.UNIVERSITY_URLS['zhongbei']
        self.crawler_config = dp_config.CRAWLER_CONFIG
        self.base_url = self.config['base_url']
        self.zb_url = self.config.get('zb_url', 'https://zbzs.nuc.edu.cn')
        self.enrollment_url = self.config.get('enrollment_url', 'https://zbzs.nuc.edu.cn/info/1016/3805.htm')
        self.school_name = self.config['name']

        self.session = requests.Session()
        self.headers = dp_config.HEADERS.copy()
        self.headers['User-Agent'] = self.crawler_config['user_agent']

        self.download_folder = dp_config.DOWNLOAD_FOLDER
        if not os.path.exists(self.download_folder):
            os.makedirs(self.download_folder)
            print(f"[爬虫] 创建下载目录: {self.download_folder}")

        self.db = db_helper.DatabaseHelper()
        self.parser = TableParser()

        self.provinces = dp_config.PROVINCES
        self.enrollment_types = dp_config.ENROLLMENT_TYPES

        self._check_system_ready()

    def _check_system_ready(self):
        """
        检查系统依赖是否就绪
        """
        print("=" * 60)
        print("[爬虫] 中北大学招生爬虫启动")
        print(f"[爬虫] 目标网址: {self.enrollment_url}")
        print("=" * 60)

    def init_ocr(self):
        """
        初始化PaddleOCR引擎（单例模式）

        Returns:
            bool: 初始化是否成功
        """
        ocr_engine, initialized = get_ocr_engine()

        # 如果引擎已初始化且可用，直接返回成功
        if initialized and ocr_engine is not None:
            print("[OCR] PaddleOCR引擎已就绪")
            return True

        # 引擎未初始化，执行初始化操作
        ocr_engine = init_paddleocr()

        # 检查初始化结果
        if ocr_engine is None:
            print("[OCR] PaddleOCR引擎初始化失败")
            return False

        print("[OCR] PaddleOCR引擎初始化成功")
        return True

    def fetch_page(self, url, retry=0):
        """
        获取网页内容

        Args:
            url: 目标URL地址
            retry: 当前重试次数

        Returns:
            str: 网页HTML内容，失败返回None
        """
        if retry >= self.crawler_config['retry_times']:
            print(f"[爬虫] 重试次数已达上限，获取失败: {url}")
            return None

        try:
            response = self.session.get(
                url,
                headers=self.headers,
                timeout=self.crawler_config['timeout']
            )

            # 判断HTTP响应状态码
            if response.status_code == 200:
                # 成功响应，设置编码并返回网页内容
                response.encoding = response.apparent_encoding
                print(f"[爬虫] 网页获取成功: {url}")
                return response.text
            else:
                # 非200状态码，触发重试
                print(f"[爬虫] HTTP错误: {response.status_code}，正在重试...")
                return self.fetch_page(url, retry + 1)

        except requests.RequestException as e:
            # 请求异常（如网络超时、连接拒绝），触发重试
            print(f"[爬虫] 请求异常: {e}，正在重试...")
            return self.fetch_page(url, retry + 1)

    def _normalize_url(self, href, base=None):
        """
        标准化URL链接

        Args:
            href: 原始链接
            base: 基础URL

        Returns:
            str: 标准化后的完整URL
        """
        if not href:
            return None
        if base is None:
            base = self.base_url
        if href.startswith('http'):
            return href
        elif href.startswith('//'):
            return 'https:' + href
        elif href.startswith('/'):
            return base + href
        elif href.startswith('./') or href.startswith('../'):
            return requests.compat.urljoin(base, href)
        return None

    def _extract_extension_from_url(self, url):
        """
        从URL中提取文件扩展名

        Args:
            url: 图片URL

        Returns:
            str: 文件扩展名（含点号）
        """
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        e_param = query_params.get('e', [''])[0] if query_params.get('e') else ''

        if e_param:
            e_param_lower = e_param.lower()
            for ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']:
                if ext in e_param_lower:
                    return ext

        url_lower = url.lower()
        for ext in ['.png', '.gif', '.bmp', '.webp', '.jpg', '.jpeg']:
            if ext in url_lower:
                return ext
        return '.jpg'

    def _is_valid_image_url(self, url):
        """
        判断URL是否为有效的招生计划图片

        Args:
            url: 图片URL

        Returns:
            bool: 是否有效
        """
        if not url:
            return False

        url_lower = url.lower()
        invalid_patterns = ['spacer.gif', 'pixel', 'blank', 'icon', 'logo', 'btn',
                           'button', 'avatar', 'header', 'footer', 'bg_', 'nav_']

        if any(pattern in url_lower for pattern in invalid_patterns):
            return False

        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        return any(ext in url_lower for ext in valid_extensions) or 'virtual_attach_file' in url_lower

    def _calculate_md5(self, content):
        """
        计算图片内容的MD5值

        Args:
            content: 图片二进制内容

        Returns:
            str: MD5哈希值
        """
        return hashlib.md5(content).hexdigest()

    def _check_image_exists(self, md5_hash):
        """
        检查图片是否已存在（通过MD5比对）

        Args:
            md5_hash: 图片MD5哈希值

        Returns:
            str: 已存在图片的完整路径，不存在返回None
        """
        if not os.path.exists(self.download_folder):
            return None

        for filename in os.listdir(self.download_folder):
            if filename.endswith(('.jpg', '.png', '.gif', '.bmp', '.webp')):
                filepath = os.path.join(self.download_folder, filename)
                try:
                    with open(filepath, 'rb') as f:
                        file_md5 = self._calculate_md5(f.read())
                    if file_md5 == md5_hash:
                        return filepath
                except:
                    continue
        return None

    def _generate_filename(self, index, ext):
        """
        生成招生计划图片的文件名

        Args:
            index: 图片索引序号
            ext: 文件扩展名

        Returns:
            str: 文件名
        """
        return f"zhongbei_enrollment_{index:03d}{ext}"

    def find_center_aligned_images(self, html_content):
        """
        查找网页中<p style="text-align: center">标签下的img图片

        Args:
            html_content: 网页HTML内容

        Returns:
            list: 图片URL列表
        """
        if html_content is None:
            return []

        soup = BeautifulSoup(html_content, 'html.parser')
        image_urls = []

        center_p_tags = soup.find_all('p', style=re.compile(r'text-align\s*:\s*center'))
        print(f"[爬虫] 找到 {len(center_p_tags)} 个居中段落标签")

        # 优先从居中段落中提取图片
        for p_tag in center_p_tags:
            imgs = p_tag.find_all('img')
            for img in imgs:
                img_url = img.get('src') or img.get('data-src') or img.get('lazy-src')
                if img_url:
                    full_url = self._normalize_url(img_url, self.zb_url)
                    # 验证URL有效且未被重复添加
                    if full_url and self._is_valid_image_url(full_url):
                        if full_url not in image_urls:
                            image_urls.append(full_url)

        # 如果居中段落没有找到，尝试在所有img标签中查找带virtual_attach_file的图片
        all_imgs = soup.find_all('img')
        for img in all_imgs:
            img_url = img.get('src') or img.get('data-src') or img.get('lazy-src')
            if img_url and 'virtual_attach_file' in img_url.lower():
                full_url = self._normalize_url(img_url, self.zb_url)
                # 确保URL有效且未被重复添加
                if full_url and full_url not in image_urls:
                    image_urls.append(full_url)

        print(f"[爬虫] 共找到 {len(image_urls)} 个招生计划图片")
        return image_urls

    def download_image(self, img_url, index):
        """
        下载图片到本地指定文件夹

        Args:
            img_url: 图片URL
            index: 图片索引序号

        Returns:
            str: 下载后的本地文件路径，失败返回None
        """
        try:
            time.sleep(self.crawler_config['image_delay'])

            response = self.session.get(
                img_url,
                headers=self.headers,
                timeout=self.crawler_config['timeout']
            )

            # 检查HTTP状态码是否为200（成功）
            if response.status_code != 200:
                print(f"[爬虫] 图片下载失败，HTTP状态码: {response.status_code}")
                return None

            content = response.content

            # 检查下载内容大小，过小可能表示下载失败
            if len(content) < 1000:
                print(f"[爬虫] 图片内容过小，可能下载失败")
                return None

            # 计算MD5哈希，检查图片是否已存在
            md5_hash = self._calculate_md5(content)
            existing_path = self._check_image_exists(md5_hash)

            # 如果图片已存在，直接返回已存在的路径
            if existing_path:
                print(f"[爬虫] 图片已存在: {existing_path}")
                return existing_path

            ext = self._extract_extension_from_url(img_url)
            filename = self._generate_filename(index, ext)
            filepath = os.path.join(self.download_folder, filename)

            with open(filepath, 'wb') as f:
                f.write(content)

            print(f"[爬虫] 图片下载成功: {filepath}")
            return filepath

        except requests.RequestException as e:
            print(f"[爬虫] 图片下载请求异常: {e}")
        except Exception as e:
            print(f"[爬虫] 图片保存失败: {e}")

        return None

    def parse_ocr_text(self, ocr_text):
        """
        解析OCR识别文本，提取招生计划数据

        Args:
            ocr_text: OCR识别后的文本

        Returns:
            list: 解析后的数据字典列表
        """
        results = self.parser.parse(ocr_text)
        if results:
            print(f"[解析] 解析成功，共 {len(results)} 条数据")
        return results

    def ocr_and_process(self, img_path):
        """
        对本地图片进行OCR识别并解析

        Args:
            img_path: 本地图片路径

        Returns:
            list: 解析后的数据字典列表
        """
        if not os.path.exists(img_path):
            print(f"[OCR] 图片文件不存在: {img_path}")
            return []

        print(f"[OCR] 开始识别图片: {img_path}")

        # 检查OCR引擎是否已初始化
        if not self.init_ocr():
            print("[OCR] OCR初始化失败，无法进行识别")
            return []

        ocr_engine, _ = get_ocr_engine()
        # 再次检查引擎实例是否有效
        if ocr_engine is None:
            print("[OCR] OCR引擎未初始化")
            return []

        try:
            # 执行OCR识别
            result = ocr_engine.ocr(img_path, cls=True)

            # 检查识别结果是否为空
            if result is None or len(result) == 0:
                print(f"[OCR] 识别结果为空")
                return []

            # 解析OCR结果，提取文本内容
            full_text = ''
            if result and len(result) > 0:
                for line in result:
                    if line:
                        for item in line:
                            # 提取文本内容（item格式：[坐标, (文本, 置信度)]）
                            if item and len(item) >= 2:
                                text = item[1][0] if isinstance(item[1], tuple) else item[1]
                                full_text += text + '\n'

            print(f"[OCR] 识别成功，获取到 {len(full_text)} 个字符")

            # 使用TableParser解析文本
            enrollment_data_list = self.parse_ocr_text(full_text.strip())
            return enrollment_data_list

        except Exception as e:
            print(f"[OCR] 识别过程出错: {e}")
            return []

    def run(self):
        """
        执行完整的爬取流程

        Returns:
            int: 成功插入数据库的数据条数
        """
        print("\n" + "=" * 60)
        print("[爬虫] 开始执行爬取任务")
        print("=" * 60)

        # 步骤1：连接数据库并确保表存在
        if not self.db.connect():
            print("[错误] 数据库连接失败")
            return 0

        if not self.db.ensure_tables_exist():
            print("[错误] 数据表创建失败")
            self.db.close()
            return 0

        print("[数据库] 连接成功，数据表就绪")

        # 步骤2：获取目标网页内容
        html_content = self.fetch_page(self.enrollment_url)

        if not html_content:
            print("[错误] 获取目标网页失败")
            self.db.close()
            return 0

        # 步骤3：解析网页标题
        soup = BeautifulSoup(html_content, 'html.parser')
        page_title = soup.find('title')
        page_title = page_title.get_text(strip=True) if page_title else "中北大学招生计划"
        print(f"[爬虫] 页面标题: {page_title}")

        # 步骤4：从网页中查找招生计划图片
        image_urls = self.find_center_aligned_images(html_content)

        # 检查是否找到图片
        if not image_urls:
            print("[警告] 未找到任何招生计划图片")
            self.db.close()
            return 0

        print(f"[爬虫] 开始处理 {len(image_urls)} 个图片...")

        # 步骤5：遍历处理每个图片
        all_data = []
        fail_count = 0

        for index, img_url in enumerate(image_urls, start=1):
            print(f"\n[进度] 处理第 {index}/{len(image_urls)} 个图片")

            # 下载图片
            img_path = self.download_image(img_url, index)

            if img_path is None:
                fail_count += 1
                continue

            # 执行OCR识别和解析
            enrollment_data_list = self.ocr_and_process(img_path)

            if not enrollment_data_list:
                fail_count += 1
                continue

            # 收集解析结果
            for data in enrollment_data_list:
                all_data.append(data)

        # 步骤6：插入数据库并执行数据清洗
        if all_data:
            print(f"\n[数据库] 正在插入 {len(all_data)} 条数据...")
            if self.db.insert_enrollment_batch(all_data):
                print(f"[数据库] 数据插入成功")
                # 执行数据清洗
                stats = data_cleaner.clean_enrollment_data(self.db)
                final_count = len(all_data) - stats['invalid_removed'] - stats['duplicates_removed']
            else:
                print(f"[数据库] 数据插入失败")
                final_count = 0
                stats = {'invalid_removed': 0, 'duplicates_removed': 0, 'fixed': 0}
        else:
            final_count = 0
            stats = {'invalid_removed': 0, 'duplicates_removed': 0, 'fixed': 0}

        print("\n" + "=" * 60)
        print(f"[清洗] 清洗成功，共删除无效记录 {stats.get('invalid_removed', 0)} 条")
        print(f"[清洗] 删除重复记录 {stats.get('duplicates_removed', 0)} 条")
        print("-" * 60)
        print("[爬虫] 任务完成")
        print(f"[统计] 成功处理: {final_count} 条数据")
        print(f"[统计] 失败图片: {fail_count} 个")
        print("=" * 60)


def main():
    """
    主函数
    """
    crawler = ZhongbeiCrawler()
    crawler.run()


if __name__ == '__main__':
    main()