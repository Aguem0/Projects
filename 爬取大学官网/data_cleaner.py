"""
data_cleaner.py - 数据清洗和解析模块

本模块主要功能：
1. 表格文本解析器(TableParser)：从OCR识别的文本中提取招生数据
   - 解析表格格式的OCR文本，提取学院代码、学院名称、专业名称、选考科目
   - 支持回退解析模式，当表格解析失败时使用正则表达式提取字段

2. 数据清洗器(DataCleaner)：清洗和修复数据库中的错误数据
   - 删除无效记录（空专业名称、无效学院代码等）
   - 删除重复记录（保留最早插入的记录）
   - 修复常见的OCR识别错误（学院名称、专业名称、选考科目格式错误）

版本要求: Python3.9 / PaddleOCR2.7.0.3 / PaddlePaddle2.6.2 / NumPy1.26.4
"""

import re
import pymysql
from pymysql.cursors import DictCursor
import dp_config


class TableParser:
    """
    表格文本解析器

    功能说明：
    - 负责从OCR识别的文本中提取结构化招生数据
    - 支持表格格式解析和回退解析两种模式
    - 通过识别特定的标记符号（学院代码、专业名称、选考科目等）来分割文本
    """

    def __init__(self):
        """
        初始化表格解析器

        说明：
        - 创建一个轻量级的解析器实例
        - 不需要数据库连接，仅用于文本解析
        """
        pass

    def parse(self, ocr_text):
        """
        解析OCR文本的入口方法

        功能说明：
        - 首先尝试表格格式解析
        - 如果表格解析失败，则使用回退解析

        参数说明：
            ocr_text: OCR识别后的原始文本

        返回值说明：
            list: 解析后的数据字典列表，每个字典包含：
                - college_code: 学院代码
                - college_name: 学院名称
                - major_name: 专业名称
                - subject_requirements: 选考科目
        """
        table_results = self._parse_table_format(ocr_text)

        if table_results:
            return table_results

        return self._fallback_parse(ocr_text)

    def _parse_table_format(self, ocr_text):
        """
        解析表格格式的OCR文本

        功能说明：
        - 识别表头行（包含"学院代码"、"学院名称"、"专业名称"、"选考科目"关键字）
        - 从表头后开始，逐行解析数据
        - 通过2位数字识别学院代码，通过"学院"/"系"/"学部"关键字识别学院名称
        - 通过特定标记（"物理"、"化学"、"2门科目"等）分离专业名称和选考科目

        参数说明：
            ocr_text: OCR识别后的原始文本

        返回值说明：
            list: 解析后的数据字典列表，解析失败返回None
        """
        lines = [line.strip() for line in ocr_text.split('\n') if line.strip()]
        results = []

        header_keywords = ['学院代码', '学院名称', '专业名称', '选考科目']
        header_line_idx = -1

        for i, line in enumerate(lines):
            # 清理行文本，移除多余空白字符
            line_clean = re.sub(r'\s+', '', line)
            # 检查是否包含所有表头关键字（学院代码、学院名称、专业名称、选考科目）
            if all(kw in line_clean for kw in header_keywords):
                header_line_idx = i
                break

        # 确定数据起始位置（表头行之后）
        data_start_idx = header_line_idx + 1 if header_line_idx >= 0 else 0

        current_college_code = ''
        current_college_name = ''

        i = data_start_idx
        while i < len(lines):
            line = lines[i]

            # 检查是否为2位数字的学院代码
            code_match = re.match(r'^(\d{2})$', line)
            if code_match:
                potential_code = code_match.group(1)
                i += 1

                # 检查下一行是否为学院名称（包含"学院"、"系"、"学部"关键字）
                if i < len(lines):
                    next_line = lines[i]
                    # 尝试匹配学院名称格式（如"航空宇航学院"）
                    college_pattern = re.match(r'^(.{2,10}学院|.{2,10}系|.{2,10}学部)\s*$', next_line)
                    if college_pattern:
                        # 成功匹配到学院名称，更新当前学院信息
                        current_college_code = potential_code
                        current_college_name = college_pattern.group(1)
                        i += 1
                    # 如果下一行仍是2位数字，说明这是连续的学院代码行
                    elif re.match(r'^\d{2}$', next_line):
                        current_college_code = potential_code
                        current_college_name = ''
                        continue
                    else:
                        # 下一行不是学院名称，记录代码但学院名称留空
                        current_college_code = potential_code
                        current_college_name = ''
                else:
                    continue
            else:
                # 当前行不是学院代码，跳过
                i += 1
                continue

            # 检查学院代码是否有效（不能为空）
            if not current_college_code:
                i += 1
                continue

            # 收集属于同一专业的多行文本
            major_lines = []
            while i < len(lines):
                check_line = lines[i]
                # 检查是否遇到新的学院代码（2位数字）
                if re.match(r'^\d{2}$', check_line):
                    break
                # 检查是否遇到新的学院名称行
                if '学院' in check_line or '系' in check_line or '学部' in check_line:
                    college_check = re.match(r'^(.{2,10}学院|.{2,10}系|.{2,10}学部)$', check_line)
                    # 如果是新学院名称（长度较短），则停止收集
                    if college_check and len(check_line) <= 10:
                        break
                major_lines.append(check_line)
                i += 1

            # 如果没有收集到任何专业行，跳过处理
            if not major_lines:
                continue

            # 将多行专业文本合并为完整字符串
            full_text = ''.join(major_lines)

            # 定义分隔标记，用于分离专业名称和选考科目
            all_markers = [
                '2门科目考生均须选考方可报考',
                '1门科目考生必须选考方可报考',
                '不提科目要求',
                '物理，化学',
                '物理,化学',
                '物理，',
                '化学，'
            ]

            # 在文本中查找最先出现的分隔标记
            marker_idx = -1
            found_marker = None
            for marker in all_markers:
                idx = full_text.find(marker)
                # 选择最早出现的标记
                if idx != -1:
                    if marker_idx == -1 or idx < marker_idx:
                        marker_idx = idx
                        found_marker = marker

            # 如果没找到标准标记，尝试查找"物理，"或"化学，"
            if marker_idx == -1:
                for sep in ['物理，', '化学，']:
                    idx = full_text.find(sep)
                    if idx != -1:
                        marker_idx = idx
                        found_marker = sep[:-1]  # 去掉逗号
                        break

            major_name = ''
            subject_requirements = ''

            # 根据分隔标记位置分割专业名称和选考科目
            # marker_idx > 0：标记在文本中间，可以正常分割
            if marker_idx > 0:
                major_name = full_text[:marker_idx].strip()
                subject_requirements = full_text[marker_idx:].strip()
            # marker_idx == 0 且找到了标记：整行都是选考科目信息
            elif marker_idx == 0 and found_marker:
                subject_requirements = full_text.strip()
            # 未找到任何标记：整行都是专业名称
            else:
                major_name = full_text

            # 处理标准选考科目格式的补全
            # 如果文本中包含"2门科目考生均须选考"，说明物理和化学都需要
            if '2门科目考生均须选考方可报考' in full_text:
                subject_requirements = '物理，化学（2门科目考生均须选考方可报考）'
            # 如果文本中包含"1门科目考生必须选考"，说明只需要物理
            elif '1门科目考生必须选考方可报考' in full_text:
                subject_requirements = '物理（1门科目考生必须选考方可报考）'
            # 如果文本中包含"不提科目要求"
            elif '不提科目要求' in full_text:
                subject_requirements = '不提科目要求'
            # 如果找到了"物理"或"化学"标记，需要补全为完整格式
            elif found_marker in ['物理', '化学']:
                # 以"物理"开头但没有"化学"，添加化学
                if subject_requirements.startswith('物理') and '化学' not in subject_requirements:
                    subject_requirements = '物理，化学（2门科目考生均须选考方可报考）'
                # 以"化学"开头但没有"物理"，添加物理
                elif subject_requirements.startswith('化学') and '物理' not in subject_requirements:
                    subject_requirements = '物理，化学（2门科目考生均须选考方可报考）'
            # 如果选考科目没有以"）"结尾，需要补充括号格式
            elif subject_requirements and not subject_requirements.endswith('）'):
                subject_requirements = subject_requirements + '（2门科目考生均须选考方可报考）'

            # 只有当专业名称有效（长度>=2）且有学院名称时才添加数据
            if major_name and len(major_name) >= 2 and current_college_name:
                data = {
                    'college_code': current_college_code,
                    'college_name': current_college_name,
                    'major_name': major_name,
                    'subject_requirements': subject_requirements
                }
                results.append(data)
            continue

        # 返回解析结果，如果没有则返回None
        return results if results else None

    def _fallback_parse(self, ocr_text):
        """
        回退解析方法（当表格解析失败时使用）

        功能说明：
        - 当表格解析无法提取有效数据时使用
        - 通过正则表达式模式匹配各个字段
        - 适用于OCR识别不完整或格式混乱的情况

        参数说明：
            ocr_text: OCR识别后的原始文本

        返回值说明：
            list: 包含一条数据字典的列表
        """
        results = []
        data = {
            'college_code': self._extract_college_code(ocr_text),
            'college_name': self._extract_college_name(ocr_text),
            'major_name': self._extract_major_name(ocr_text) or '未知专业',
            'subject_requirements': self._extract_subject_requirements(ocr_text)
        }
        results.append(data)
        return results

    def _extract_college_code(self, text):
        """
        从文本中提取学院代码

        功能说明：
        - 通过正则表达式匹配学院代码
        - 优先匹配"学院代码"等关键字后的4-10位字母数字
        - 其次匹配独立的2位数字

        参数说明：
            text: 输入文本

        返回值说明：
            str: 提取到的学院代码，未找到返回空字符串
        """
        patterns = [
            r'(?:学院代码|代码|院系代码)[:：]?\s*([A-Za-z0-9]{4,10})',
            r'(?<!\d)(?<!\w)([0-9]{2})(?!\d)(?!\w)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return ''

    def _extract_college_name(self, text):
        """
        从文本中提取学院名称

        功能说明：
        - 通过正则表达式匹配学院名称
        - 匹配以"学院"、"系"、"学部"结尾的字符串
        - 长度范围2-15个字符

        参数说明：
            text: 输入文本

        返回值说明：
            str: 提取到的学院名称，未找到返回空字符串
        """
        patterns = [
            r'(?:学院|系|学部)[:：]?\s*([^\s\d\n]{2,15}(?:学院|系|学部|大学))',
            r'([^\s\d\n]{2,10}学院)',
            r'([^\s\d\n]{2,10}系)',
            r'([^\s\d\n]{2,10}学部)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return ''

    def _extract_major_name(self, text):
        """
        从文本中提取专业名称

        功能说明：
        - 通过正则表达式匹配专业名称
        - 匹配以"专业"、"类"、"方向"结尾的字符串
        - 长度范围2-20个字符

        参数说明：
            text: 输入文本

        返回值说明：
            str: 提取到的专业名称，未找到返回空字符串
        """
        patterns = [
            r'(?:专业|类|方向)[:：]?\s*([^\s\d\n]{2,20}(?:专业|类|方向))',
            r'([^\s\d\n]{2,15}专业)',
            r'([^\s\d\n]{2,10}(?:类|方向))',
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return ''

    def _extract_subject_requirements(self, text):
        """
        从文本中提取选考科目

        功能说明：
        - 通过正则表达式匹配选考科目信息
        - 匹配物理、化学、生物、历史、地理、政治等科目组合
        - 支持"3+1+2"等选考模式

        参数说明：
            text: 输入文本

        返回值说明：
            str: 提取到的选考科目，未找到返回空字符串
        """
        patterns = [
            r'(?:选考|必考|科目|考试科目)[:：]?\s*([物理化学生物历史地理政治\d，,、]+)',
            r'(?:3\+1\+2|3\+3|3\+1\+1)[:：]?\s*([物理化学生物历史地理政治\d，,、]+)',
            r'([物理化学生物历史地理政治合卷，,、]+)',
            r'(物理，化学|物理,化学|物理、化学)(?:（[^）]+）)?',
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1) if match.lastindex == 1 else match.group(0)
        return ''


class DataCleaner:
    """
    数据清洗类

    功能说明：
    - 提供数据库数据的清洗和修复功能
    - 删除无效和重复的记录
    - 修复OCR识别过程中产生的常见错误
    - 支持学院名称、专业名称、选考科目的错误修复
    """

    COLLEGE_NAME_FIXES = {
        '字航': '航空宇航',
        '字': '学',
        '材料科学与': '材料科学与工程学院',
        '经济与管理': '经济与管理学院',
        '体育学院': '体育学院',
        '艺术学院': '艺术学院',
        '人文社会科学学院': '人文社会科学学院',
        '软件学院': '软件学院',
        '电气与控制工程': '电气与控制工程学院',
        '能源与动力': '能源与动力工程学院',
        '半导体与物理': '半导体与物理学院',
        '化学与化工': '化学与化工学院',
    }

    MAJOR_NAME_FIXES = {
        '航空字航': '航空宇航',
        '无人驾驶航空器系统工程': '无人驾驶航空器系统工程',
        '飞行器设计与工程': '飞行器设计与工程',
    }

    SUBJECT_PATTERN_FIXES = [
        ('（(\\d)门科目考生均须选考方可报考）', r'（\\1门科目考生均须选考方可报考）'),
        ('(2门科目考生均须选考方可报考）', '物理，化学（2门科目考生均须选考方可报考）'),
    ]

    def __init__(self, db_helper=None):
        """
        初始化数据清洗器

        参数说明：
            db_helper: 数据库辅助对象，如果为None则创建新对象

        说明：
        - 如果传入db_helper，则使用传入的连接（外部连接）
        - 如果不传入，则创建新的DatabaseHelper实例
        """
        if db_helper is None:
            import db_helper as dh
            self.db = dh.DatabaseHelper()
        else:
            self.db = db_helper
        self.stats = {
            'invalid_removed': 0,
            'duplicates_removed': 0,
            'fixed': 0
        }
        self._external_connection = db_helper is not None

    def clean_all(self):
        """
        执行完整的数据清洗流程

        功能说明：
        - 删除无效记录（专业名称为空或过短、学院代码为空）
        - 删除重复记录（保留最早插入的记录）
        - 修复学院名称错误
        - 修复专业名称错误
        - 修复选考科目格式错误

        返回值说明：
            dict: 清洗统计信息，包含：
                - invalid_removed: 删除的无效记录数
                - duplicates_removed: 删除的重复记录数
                - fixed: 修复的错误记录数
        """
        self.stats = {'invalid_removed': 0, 'duplicates_removed': 0, 'fixed': 0}

        if not self._external_connection:
            if not self.db.connect():
                return self.stats

        self._remove_invalid_records()
        self._remove_duplicates()
        self._fix_college_names()
        self._fix_major_names()
        self._fix_subject_patterns()

        return self.stats

    def _remove_invalid_records(self):
        """
        删除无效记录

        功能说明：
        - 查询专业名称为空、长度小于2、学院代码为空的记录
        - 将这些无效记录从数据库中删除

        说明：
        - 专业名称为空的记录是无效的，无法使用
        - 学院代码为空的记录也是无效的
        """
        try:
            select_sql = f"""
                SELECT id, college_code, college_name, major_name, subject_requirements
                FROM {dp_config.TABLE_NAME}
                WHERE major_name IS NULL
                   OR major_name = ''
                   OR LENGTH(major_name) < 2
                   OR college_code = ''
            """
            self.db.cursor.execute(select_sql)
            invalid_records = self.db.cursor.fetchall()

            if invalid_records:
                ids_to_delete = [str(r['id']) for r in invalid_records]
                delete_sql = f"DELETE FROM {dp_config.TABLE_NAME} WHERE id IN ({','.join(ids_to_delete)})"
                self.db.cursor.execute(delete_sql)
                self.db.connection.commit()
                self.stats['invalid_removed'] = len(invalid_records)

        except Exception as e:
            self.db.connection.rollback()

    def _remove_duplicates(self):
        """
        删除重复记录

        功能说明：
        - 根据学院代码、学院名称、专业名称、选考科目的组合判断重复
        - 保留每组重复记录中id最小的（最早插入的）记录
        - 删除其他重复的记录

        说明：
        - 使用字典来跟踪已见过的记录组合
        - 按id升序处理，确保保留最早的记录
        """
        try:
            select_sql = f"""
                SELECT id, college_code, college_name, major_name, subject_requirements
                FROM {dp_config.TABLE_NAME}
                ORDER BY id ASC
            """
            self.db.cursor.execute(select_sql)
            all_records = self.db.cursor.fetchall()

            seen = {}
            duplicate_ids = []

            for record in all_records:
                key = (
                    record['college_code'] or '',
                    record['college_name'] or '',
                    record['major_name'] or '',
                    record['subject_requirements'] or ''
                )

                if key in seen:
                    duplicate_ids.append(record['id'])
                else:
                    seen[key] = record['id']

            if duplicate_ids:
                ids_str = ','.join(str(id) for id in duplicate_ids)
                delete_sql = f"DELETE FROM {dp_config.TABLE_NAME} WHERE id IN ({ids_str})"
                self.db.cursor.execute(delete_sql)
                self.db.connection.commit()
                self.stats['duplicates_removed'] = len(duplicate_ids)

        except Exception as e:
            self.db.connection.rollback()

    def _fix_college_names(self):
        """
        修复学院名称错误

        功能说明：
        - 遍历所有记录，检查学院名称是否在错误映射表中
        - 如果发现错误名称，替换为正确的名称
        - 例如："字航" -> "航空宇航"，"材料科学与" -> "材料科学与工程学院"

        说明：
        - 使用COLLEGE_NAME_FIXES字典存储错误名称到正确名称的映射
        - 支持部分匹配替换
        """
        fixes_applied = 0

        try:
            select_sql = f"SELECT id, college_name FROM {dp_config.TABLE_NAME}"
            self.db.cursor.execute(select_sql)
            records = self.db.cursor.fetchall()

            for record in records:
                if not record['college_name']:
                    continue

                original = record['college_name']
                fixed = original

                for wrong, correct in self.COLLEGE_NAME_FIXES.items():
                    if wrong in fixed:
                        fixed = fixed.replace(wrong, correct)

                if fixed != original:
                    update_sql = f"UPDATE {dp_config.TABLE_NAME} SET college_name = %s WHERE id = %s"
                    self.db.cursor.execute(update_sql, (fixed, record['id']))
                    fixes_applied += 1

            if fixes_applied > 0:
                self.db.connection.commit()
                self.stats['fixed'] += fixes_applied

        except Exception as e:
            self.db.connection.rollback()

    def _fix_major_names(self):
        """
        修复专业名称错误

        功能说明：
        - 遍历所有记录，检查专业名称是否在错误映射表中
        - 如果发现错误名称，替换为正确的名称
        - 例如："航空字航" -> "航空宇航"

        说明：
        - 使用MAJOR_NAME_FIXES字典存储错误名称到正确名称的映射
        """
        fixes_applied = 0

        try:
            select_sql = f"SELECT id, major_name FROM {dp_config.TABLE_NAME}"
            self.db.cursor.execute(select_sql)
            records = self.db.cursor.fetchall()

            for record in records:
                if not record['major_name']:
                    continue

                original = record['major_name']
                fixed = original

                for wrong, correct in self.MAJOR_NAME_FIXES.items():
                    if wrong in fixed:
                        fixed = fixed.replace(wrong, correct)

                if fixed != original:
                    update_sql = f"UPDATE {dp_config.TABLE_NAME} SET major_name = %s WHERE id = %s"
                    self.db.cursor.execute(update_sql, (fixed, record['id']))
                    fixes_applied += 1

            if fixes_applied > 0:
                self.db.connection.commit()
                self.stats['fixed'] += fixes_applied

        except Exception as e:
            self.db.connection.rollback()

    def _fix_subject_patterns(self):
        """
        修复选考科目格式错误

        功能说明：
        - 遍历所有记录，检查选考科目是否符合标准格式
        - 如果发现格式错误，替换为正确的格式
        - 例如：缺失"物理，化学"前缀的补全

        说明：
        - 使用SUBJECT_PATTERN_FIXES列表存储模式替换规则
        - 每个规则是一个元组（错误模式，正确模式）
        """
        fixes_applied = 0

        try:
            select_sql = f"SELECT id, subject_requirements FROM {dp_config.TABLE_NAME}"
            self.db.cursor.execute(select_sql)
            records = self.db.cursor.fetchall()

            for record in records:
                if not record['subject_requirements']:
                    continue

                original = record['subject_requirements']
                fixed = original

                for wrong_pattern, correct_pattern in self.SUBJECT_PATTERN_FIXES:
                    if wrong_pattern in fixed:
                        fixed = fixed.replace(wrong_pattern, correct_pattern)

                if fixed != original:
                    update_sql = f"UPDATE {dp_config.TABLE_NAME} SET subject_requirements = %s WHERE id = %s"
                    self.db.cursor.execute(update_sql, (fixed, record['id']))
                    fixes_applied += 1

            if fixes_applied > 0:
                self.db.connection.commit()
                self.stats['fixed'] += fixes_applied

        except Exception as e:
            self.db.connection.rollback()


def clean_enrollment_data(db_helper=None):
    """
    便捷函数：执行数据清洗

    功能说明：
    - 创建一个DataCleaner实例并执行清洗
    - 提供简单的接口调用数据清洗功能

    参数说明：
        db_helper: 数据库辅助对象，如果为None则创建新对象

    返回值说明：
        dict: 清洗统计信息
    """
    cleaner = DataCleaner(db_helper)
    return cleaner.clean_all()
