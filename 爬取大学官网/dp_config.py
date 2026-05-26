"""
dp_config.py - 项目配置文件

本模块主要功能：
1. 数据库配置
   - MySQL数据库连接参数（主机、端口、用户名、密码、数据库名、字符集）

2. 爬虫配置
   - HTTP请求超时时间
   - 重试次数
   - User-Agent头
   - 请求间隔延迟

3. PaddleOCR配置
   - 是否使用角度分类器
   - 语言设置
   - 是否使用GPU
   - 日志显示配置

4. 大学URL配置
   - 中北大学的目标网址
   - 招生信息页面URL
   - 搜索关键字

5. 其他配置
   - HTTP请求头
   - 图片下载目录
   - 省份列表
   - 招生类型列表

版本要求: Python3.9 / PaddleOCR2.7.0.3 / PaddlePaddle2.6.2 / NumPy1.26.4
"""

import os

DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '123456',
    'database': 'university_enrollment',
    'charset': 'utf8mb4'
}

CRAWLER_CONFIG = {
    'timeout': 30,
    'retry_times': 3,
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'delay': 2,
    'image_delay': 3
}

PADDLEOCR_CONFIG = {
    'use_angle_cls': True,
    'lang': 'chinese',
    'use_gpu': False,
    'show_log': False
}

UNIVERSITY_URLS = {
    'zhongbei': {
        'name': '中北大学',
        'base_url': 'https://www.nuc.edu.cn',
        'zb_url': 'https://zbzs.nuc.edu.cn',
        'enrollment_url': 'https://zbzs.nuc.edu.cn/info/1016/3805.htm',
        'enrollment_path': '/zhaosheng/xxgk.htm',
        'search_keywords': ['招生计划', '招生简章']
    }
}

TABLE_NAME = 'enrollment_plans'

HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

DOWNLOAD_FOLDER = r'e:\Development_files\Python\爬取大学官网\招生计划图片'

PROVINCES = [
    '北京', '天津', '河北', '山西', '内蒙古', '辽宁', '吉林', '黑龙江',
    '上海', '江苏', '浙江', '安徽', '福建', '江西', '山东', '河南',
    '湖北', '湖南', '广东', '广西', '海南', '重庆', '四川', '贵州',
    '云南', '西藏', '陕西', '甘肃', '青海', '宁夏', '新疆', '全国'
]

ENROLLMENT_TYPES = [
    '理科', '文科', '物理类', '历史类', '综合改革', '艺术类', '体育类', '普通类'
]
