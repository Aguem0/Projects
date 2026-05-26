"""
db_helper.py - 数据库操作模块

本模块主要功能：
1. 数据库连接管理
   - 建立和关闭MySQL数据库连接
   - 自动创建不存在的数据库

2. 数据表管理
   - 创建中北大学招生计划数据表
   - 检查表是否存在

3. 数据操作
   - 插入单条和批量招生计划数据
   - 查询所有数据或按学院名称查询
   - 清空数据表

版本要求: Python3.9 / PaddleOCR2.7.0.3 / PaddlePaddle2.6.2 / NumPy1.26.4

数据库表结构：
- id: 自增主键
- college_code: 学院代码（VARCHAR）
- college_name: 学院名称（VARCHAR）
- major_name: 专业名称（VARCHAR，非空）
- subject_requirements: 选考科目（VARCHAR）
- created_at: 创建时间戳
"""

import pymysql
from pymysql.cursors import DictCursor
import dp_config


class DatabaseHelper:
    """
    数据库操作辅助类

    功能说明：
    - 封装数据库连接管理、创建表、增删改查等操作
    - 使用DictCursor返回字典格式的查询结果
    - 自动处理数据库不存在的情况

    属性说明：
    - db_config: 数据库配置信息
    - connection: 数据库连接对象
    - cursor: 数据库游标对象
    """

    def __init__(self, db_config=None):
        """
        初始化数据库辅助类

        参数说明：
            db_config: 数据库配置字典，如果为None则使用dp_config.DB_CONFIG

        说明：
        - 如果传入配置，则使用传入的配置
        - 如果不传入，则使用dp_config中的默认配置
        """
        if db_config is None:
            self.db_config = dp_config.DB_CONFIG
        else:
            self.db_config = db_config
        self.connection = None
        self.cursor = None

    def connect(self):
        """
        建立数据库连接

        功能说明：
        - 尝试建立与MySQL数据库的连接
        - 如果连接失败且错误码为1049（数据库不存在），则自动创建数据库
        - 使用DictCursor以字典格式返回查询结果

        返回值说明：
            bool: 连接是否成功
        """
        try:
            # 如果已有连接，先关闭
            if self.connection is not None:
                self.close()
            # 建立新的数据库连接
            self.connection = pymysql.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                user=self.db_config['user'],
                password=self.db_config['password'],
                database=self.db_config['database'],
                charset=self.db_config['charset']
            )
            self.cursor = self.connection.cursor(DictCursor)
            print("[数据库] 连接成功")
            return True
        except pymysql.err.OperationalError as e:
            error_code = e.args[0] if e.args else 0
            # 如果错误码为1049（数据库不存在），尝试创建数据库
            if error_code == 1049:
                print(f"[数据库] 数据库 '{self.db_config['database']}' 不存在，正在创建...")
                if self.create_database():
                    # 数据库创建成功后，递归调用connect建立连接
                    return self.connect()
            print(f"[数据库] 连接失败: {e}")
            return False
        except Exception as e:
            print(f"[数据库] 连接失败: {e}")
            return False

    def close(self):
        """
        关闭数据库连接和游标

        功能说明：
        - 安全关闭游标和连接
        - 即使关闭失败也会继续尝试关闭另一方
        - 用于释放数据库资源
        """
        if self.cursor is not None:
            try:
                self.cursor.close()
            except:
                pass
            self.cursor = None
        if self.connection is not None:
            try:
                self.connection.close()
            except:
                pass
            self.connection = None
        print("[数据库] 连接已关闭")

    def create_database(self):
        """
        创建数据库（如果不存在）

        功能说明：
        - 连接到MySQL服务器（不指定数据库）
        - 使用CREATE DATABASE IF NOT EXISTS创建数据库
        - 设置字符集为utf8mb4以支持中文

        返回值说明：
            bool: 数据库创建是否成功
        """
        conn = None
        cursor = None
        try:
            temp_config = self.db_config.copy()
            temp_config.pop('database')
            conn = pymysql.connect(**temp_config)
            cursor = conn.cursor()
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS {self.db_config['database']} "
                f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            conn.commit()
            print(f"[数据库] 数据库 '{self.db_config['database']}' 创建成功或已存在")
            return True
        except Exception as e:
            print(f"[数据库] 创建数据库失败: {e}")
            return False
        finally:
            if cursor is not None:
                try:
                    cursor.close()
                except:
                    pass
            if conn is not None:
                try:
                    conn.close()
                except:
                    pass

    def create_tables(self):
        """
        创建所需的数据表

        功能说明：
        - 创建中北大学招生计划表enrollment_plans
        - 表包含id、学院代码、学院名称、专业名称、选考科目、创建时间
        - 设置id为主键，学院代码、学院名称、专业名称为索引

        返回值说明：
            bool: 表创建是否成功
        """
        create_enrollment_table = f"""
        CREATE TABLE IF NOT EXISTS {dp_config.TABLE_NAME} (
            id INT AUTO_INCREMENT PRIMARY KEY COMMENT 'ID',
            college_code VARCHAR(50) COMMENT '学院代码',
            college_name VARCHAR(100) COMMENT '学院名称',
            major_name VARCHAR(100) NOT NULL COMMENT '专业名称',
            subject_requirements VARCHAR(200) COMMENT '选考科目',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            INDEX idx_college_code (college_code) COMMENT '学院代码索引',
            INDEX idx_college_name (college_name) COMMENT '学院名称索引',
            INDEX idx_major (major_name) COMMENT '专业名称索引'
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='中北大学招生计划表'
        """

        try:
            # 如果游标不存在，先建立连接
            if self.cursor is None:
                if not self.connect():
                    return False

            # 执行建表SQL
            self.cursor.execute(create_enrollment_table)
            self.connection.commit()
            print("[数据库] 数据表创建成功")
            return True
        except Exception as e:
            print(f"[数据库] 创建数据表失败: {e}")
            # 发生错误时回滚事务
            if self.connection:
                self.connection.rollback()
            return False

    def ensure_tables_exist(self):
        """
        确保所有表都存在，如果不存在则创建

        功能说明：
        - 先检查表是否存在
        - 如果表不存在，则调用create_tables创建

        返回值说明：
            bool: 表是否存在或创建成功
        """
        if self.cursor is None:
            if not self.connect():
                return False

        if not self._table_exists(dp_config.TABLE_NAME):
            print(f"[数据库] 表 {dp_config.TABLE_NAME} 不存在，需要创建")
            return self.create_tables()

        print(f"[数据库] 表 {dp_config.TABLE_NAME} 已存在")
        return True

    def _table_exists(self, table_name):
        """
        检查表是否存在

        参数说明：
            table_name: 要检查的表名

        返回值说明：
            bool: 表是否存在
        """
        try:
            check_sql = f"SHOW TABLES LIKE '{table_name}'"
            self.cursor.execute(check_sql)
            result = self.cursor.fetchone()
            return result is not None
        except Exception as e:
            print(f"[数据库] 检查表存在性失败: {e}")
            return False

    def insert_enrollment_data(self, data):
        """
        插入单条招生计划数据

        参数说明：
            data: 招生计划数据字典，包含：
                - college_code: 学院代码
                - college_name: 学院名称
                - major_name: 专业名称
                - subject_requirements: 选考科目

        返回值说明：
            bool: 插入是否成功
        """
        if not self.ensure_tables_exist():
            return False

        if self.cursor is None:
            if not self.connect():
                return False

        insert_sql = f"""
        INSERT INTO {dp_config.TABLE_NAME} (
            college_code, college_name, major_name, subject_requirements
        )
        VALUES (
            %(college_code)s, %(college_name)s, %(major_name)s, %(subject_requirements)s
        )
        """

        try:
            self.cursor.execute(insert_sql, data)
            self.connection.commit()
            return True
        except Exception as e:
            print(f"[数据库] 插入数据失败: {e}")
            if self.connection:
                self.connection.rollback()
            return False

    def insert_enrollment_batch(self, data_list):
        """
        批量插入招生计划数据

        参数说明：
            data_list: 招生计划数据字典列表

        返回值说明：
            bool: 批量插入是否成功
        """
        # 检查数据列表是否为空
        if not data_list:
            print("[数据库] 没有数据需要插入")
            return True

        # 确保表存在
        if not self.ensure_tables_exist():
            return False

        # 确保游标可用
        if self.cursor is None:
            if not self.connect():
                return False

        insert_sql = f"""
        INSERT INTO {dp_config.TABLE_NAME} (
            college_code, college_name, major_name, subject_requirements
        )
        VALUES (
            %(college_code)s, %(college_name)s, %(major_name)s, %(subject_requirements)s
        )
        """

        try:
            # 使用executemany进行批量插入
            self.cursor.executemany(insert_sql, data_list)
            self.connection.commit()
            print(f"[数据库] 成功批量插入 {len(data_list)} 条数据")
            return True
        except Exception as e:
            print(f"[数据库] 批量插入失败: {e}")
            # 发生错误时回滚事务
            if self.connection:
                self.connection.rollback()
            return False

    def query_all(self, limit=1000):
        """
        查询所有招生计划数据

        参数说明：
            limit: 返回结果数量限制，默认1000条

        返回值说明：
            list: 查询结果列表，每条结果是字典格式
        """
        if self.cursor is None:
            if not self.connect():
                return []

        query_sql = f"""
            SELECT * FROM {dp_config.TABLE_NAME}
            ORDER BY college_name, major_name
            LIMIT %s
        """

        try:
            self.cursor.execute(query_sql, (limit,))
            return self.cursor.fetchall()
        except Exception as e:
            print(f"[数据库] 查询失败: {e}")
            return []

    def query_by_college(self, college_name):
        """
        根据学院名称查询

        参数说明：
            college_name: 学院名称

        返回值说明：
            list: 查询结果列表，按专业名称排序
        """
        if self.cursor is None:
            if not self.connect():
                return []

        query_sql = f"""
            SELECT * FROM {dp_config.TABLE_NAME}
            WHERE college_name = %s
            ORDER BY major_name
        """

        try:
            self.cursor.execute(query_sql, (college_name,))
            return self.cursor.fetchall()
        except Exception as e:
            print(f"[数据库] 查询失败: {e}")
            return []

    def delete_all(self):
        """
        删除所有数据

        功能说明：
        - 清空enrollment_plans表中的所有数据
        - 表结构保留，只删除数据

        返回值说明：
            bool: 删除是否成功
        """
        if self.cursor is None:
            if not self.connect():
                return False

        delete_sql = f"DELETE FROM {dp_config.TABLE_NAME}"

        try:
            self.cursor.execute(delete_sql)
            self.connection.commit()
            print(f"[数据库] 已清空所有数据")
            return True
        except Exception as e:
            print(f"[数据库] 删除失败: {e}")
            if self.connection:
                self.connection.rollback()
            return False
