"""
数据库管理器
处理数据仓库连接、表结构分析、SQL 查询执行
"""
import pandas as pd
import sqlalchemy as sa
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError
from typing import Dict, List, Tuple, Optional, Any
import json
from config import Config
from loguru import logger

# 兼容性配置：使用 PyMySQL 替代 MySQLdb
try:
    import pymysql
    # 注册 PyMySQL 作为 MySQL 的默认驱动
    pymysql.install_as_MySQLdb()
    logger.info("PyMySQL 已配置为 MySQL 默认驱动")
except ImportError:
    logger.warning("PyMySQL 未安装，MySQL 连接可能失败")

class DatabaseManager:
    """数据库管理器类"""
    
    def __init__(self, db_url: str = None):
        self.engine = None
        self.inspector = None
        self.schema_cache = {}
        self.current_db_url = db_url
        self.connect()
    
    def connect(self):
        """连接数据库"""
        try:
            # 根据数据库类型调整连接字符串
            db_url = self._prepare_db_url()
            self.engine = create_engine(db_url, pool_pre_ping=True)
            self.inspector = inspect(self.engine)
            logger.info(f"数据库连接成功 (类型: {Config.DB_TYPE})")
            return True
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            logger.error(f"数据库配置: 类型={Config.DB_TYPE}, 主机={Config.DB_HOST}, 端口={Config.DB_PORT}")
            return False
    
    def switch_database(self, db_url: str) -> bool:
        """切换数据库连接"""
        try:
            # 关闭现有连接
            if self.engine:
                self.engine.dispose()
            
            # 清除缓存
            self.schema_cache = {}
            
            # 更新数据库URL
            self.current_db_url = db_url
            
            # 建立新连接
            self.engine = create_engine(db_url, pool_pre_ping=True)
            
            # 测试新连接
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            self.inspector = inspect(self.engine)
            
            logger.info(f"数据库切换成功: {db_url}")
            return True
            
        except Exception as e:
            logger.error(f"数据库切换失败: {e}")
            return False
    
    def _prepare_db_url(self) -> str:
        """准备数据库连接字符串"""
        # 如果有自定义URL则使用自定义URL，否则使用配置文件的URL
        db_url = self.current_db_url or Config.DB_URL
        
        # 如果是 MySQL 且使用默认格式，自动修改为 PyMySQL 格式
        if Config.DB_TYPE.lower() == 'mysql' and db_url.startswith('mysql://'):
            db_url = db_url.replace('mysql://', 'mysql+pymysql://')
            logger.info("自动转换 MySQL 连接字符串为 PyMySQL 格式")
        
        # 如果是 PostgreSQL 且没有指定驱动，使用 psycopg2
        elif Config.DB_TYPE.lower() == 'postgresql' and db_url.startswith('postgresql://'):
            if '+' not in db_url.split('://')[0]:
                db_url = db_url.replace('postgresql://', 'postgresql+psycopg2://')
                logger.info("自动转换 PostgreSQL 连接字符串为 psycopg2 格式")
        
        return db_url
    
    def get_table_names(self) -> List[str]:
        """获取所有表名"""
        try:
            return self.inspector.get_table_names()
        except Exception as e:
            logger.error(f"获取表名失败: {e}")
            return []
    
    def get_table_schema(self, table_name: str, force_refresh: bool = False) -> Dict[str, Any]:
        """获取表结构信息"""
        if not force_refresh and table_name in self.schema_cache:
            return self.schema_cache[table_name]
        
        try:
            columns = self.inspector.get_columns(table_name)
            foreign_keys = self.inspector.get_foreign_keys(table_name)
            primary_keys = self.inspector.get_pk_constraint(table_name)
            indexes = self.inspector.get_indexes(table_name)
            
            # 获取表的备注信息
            table_comment = self._get_table_comment(table_name)
            
            schema_info = {
                'table_name': table_name,
                'table_comment': table_comment,  # 新增表备注
                'columns': [
                    {
                        'name': col['name'],
                        'type': str(col['type']),
                        'nullable': col['nullable'],
                        'default': col.get('default'),
                        'comment': col.get('comment', ''),  # 新增字段备注
                    }
                    for col in columns
                ],
                'primary_keys': primary_keys.get('constrained_columns', []),
                'foreign_keys': [
                    {
                        'constrained_columns': fk['constrained_columns'],
                        'referred_table': fk['referred_table'],
                        'referred_columns': fk['referred_columns']
                    }
                    for fk in foreign_keys
                ],
                'indexes': [
                    {
                        'name': idx['name'],
                        'columns': idx['column_names']
                    }
                    for idx in indexes
                ]
            }
            
            self.schema_cache[table_name] = schema_info
            return schema_info
            
        except Exception as e:
            logger.error(f"获取表结构失败 {table_name}: {e}")
            return {}
    
    def _get_table_comment(self, table_name: str) -> str:
        """获取表的备注信息"""
        try:
            # 根据不同数据库类型查询表备注
            if Config.DB_TYPE.lower() == 'mysql':
                sql = text("""
                SELECT table_comment 
                FROM information_schema.tables 
                WHERE table_schema = :db_name AND table_name = :table_name
                """)
                with self.engine.connect() as connection:
                    result = connection.execute(sql, {"db_name": Config.DB_NAME, "table_name": table_name})
                    row = result.fetchone()
                    return row[0] if row and row[0] else ''
                    
            elif Config.DB_TYPE.lower() == 'postgresql':
                sql = text("""
                SELECT obj_description(oid, 'pg_class') as table_comment
                FROM pg_class 
                WHERE relname = :table_name AND relkind = 'r'
                """)
                with self.engine.connect() as connection:
                    result = connection.execute(sql, {"table_name": table_name})
                    row = result.fetchone()
                    return row[0] if row and row[0] else ''
                    
            else:
                # 其他数据库类型暂不支持
                return ''
                
        except Exception as e:
            logger.error(f"获取表备注失败 {table_name}: {e}")
            return ''
    
    def get_database_schema(self) -> Dict[str, Any]:
        """获取整个数据库的结构信息"""
        tables = self.get_table_names()
        database_schema = {
            'database_name': Config.DB_NAME,
            'tables': {}
        }
        
        for table in tables:
            schema = self.get_table_schema(table)
            if schema:
                database_schema['tables'][table] = schema
        
        return database_schema
    
    def execute_query(self, sql: str, params: Dict = None) -> Tuple[bool, Any]:
        """执行 SQL 查询"""
        try:
            # 限制结果数量，防止返回过多数据
            if sql.strip().upper().startswith('SELECT'):
                if 'LIMIT' not in sql.upper():
                    sql += f" LIMIT {Config.MAX_RESULTS_LIMIT}"
            
            with self.engine.connect() as connection:
                result = connection.execute(text(sql), params or {})
                
                if result.returns_rows:
                    # 查询操作
                    df = pd.read_sql(text(sql), connection, params=params)
                    return True, {
                        'type': 'query',
                        'data': df.to_dict('records'),
                        'columns': df.columns.tolist(),
                        'row_count': len(df)
                    }
                else:
                    # 修改操作
                    return True, {
                        'type': 'modify',
                        'rows_affected': result.rowcount
                    }
                    
        except SQLAlchemyError as e:
            logger.error(f"SQL 执行失败: {e}")
            return False, str(e)
        except Exception as e:
            logger.error(f"查询执行异常: {e}")
            return False, str(e)
    
    def validate_sql(self, sql: str) -> Tuple[bool, str]:
        """验证 SQL 语法"""
        try:
            # 基本 SQL 注入检查
            dangerous_keywords = [
                'DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE', 
                'INSERT', 'UPDATE', 'EXEC', 'EXECUTE'
            ]
            
            sql_upper = sql.upper()
            for keyword in dangerous_keywords:
                if keyword in sql_upper:
                    return False, f"检测到危险的 SQL 关键字: {keyword}"
            
            # 尝试解析 SQL
            with self.engine.connect() as connection:
                # 使用 EXPLAIN 来验证语法，但不执行
                explain_sql = f"EXPLAIN {sql}"
                connection.execute(text(explain_sql))
            
            return True, "SQL 语法正确"
            
        except Exception as e:
            return False, f"SQL 语法错误: {e}"
    
    def get_sample_data(self, table_name: str, limit: int = 5) -> Dict[str, Any]:
        """获取表的示例数据"""
        try:
            sql = f"SELECT * FROM {table_name} LIMIT {limit}"
            success, result = self.execute_query(sql)
            
            if success and result['type'] == 'query':
                return {
                    'table_name': table_name,
                    'sample_data': result['data'],
                    'columns': result['columns']
                }
            return {}
            
        except Exception as e:
            logger.error(f"获取示例数据失败 {table_name}: {e}")
            return {}
    
    def get_table_statistics(self, table_name: str) -> Dict[str, Any]:
        """获取表的统计信息"""
        try:
            # 获取行数
            count_sql = f"SELECT COUNT(*) as row_count FROM {table_name}"
            success, result = self.execute_query(count_sql)
            
            stats = {'table_name': table_name}
            if success:
                stats['row_count'] = result['data'][0]['row_count']
            
            # 获取数值列的统计信息
            schema = self.get_table_schema(table_name)
            numeric_columns = [
                col['name'] for col in schema.get('columns', [])
                if 'INT' in str(col['type']).upper() or 'FLOAT' in str(col['type']).upper() or 'DECIMAL' in str(col['type']).upper()
            ]
            
            if numeric_columns:
                stats_cols = ', '.join([
                    f"AVG({col}) as avg_{col}, MIN({col}) as min_{col}, MAX({col}) as max_{col}"
                    for col in numeric_columns[:5]  # 限制列数
                ])
                stats_sql = f"SELECT {stats_cols} FROM {table_name}"
                success, result = self.execute_query(stats_sql)
                
                if success:
                    stats['numeric_stats'] = result['data'][0]
            
            return stats
            
        except Exception as e:
            logger.error(f"获取表统计信息失败 {table_name}: {e}")
            return {'table_name': table_name}
    
    def get_metadata_completeness_report(self) -> Dict[str, Any]:
        """获取数据库元数据完整性报告"""
        try:
            tables = self.get_table_names()
            report = {
                'total_tables': len(tables),
                'tables_with_comments': 0,
                'tables_without_comments': [],
                'fields_with_comments': 0,
                'total_fields': 0,
                'metadata_coverage': {},
                'recommendations': []
            }
            
            for table_name in tables:
                schema = self.get_table_schema(table_name)
                if not schema:
                    continue
                
                # 检查表备注
                has_table_comment = bool(schema.get('table_comment'))
                if has_table_comment:
                    report['tables_with_comments'] += 1
                else:
                    report['tables_without_comments'].append(table_name)
                
                # 检查字段备注
                columns = schema.get('columns', [])
                report['total_fields'] += len(columns)
                
                fields_with_comments = sum(1 for col in columns if col.get('comment'))
                report['fields_with_comments'] += fields_with_comments
                
                # 表级别的元数据覆盖率
                field_coverage = fields_with_comments / len(columns) if columns else 0
                report['metadata_coverage'][table_name] = {
                    'table_comment': has_table_comment,
                    'field_comment_coverage': field_coverage,
                    'total_fields': len(columns),
                    'commented_fields': fields_with_comments
                }
            
            # 计算总体覆盖率
            table_comment_coverage = report['tables_with_comments'] / report['total_tables'] if report['total_tables'] else 0
            field_comment_coverage = report['fields_with_comments'] / report['total_fields'] if report['total_fields'] else 0
            
            # 生成建议
            if table_comment_coverage < 0.8:
                report['recommendations'].append(f"建议为 {len(report['tables_without_comments'])} 个表添加备注说明")
            
            if field_comment_coverage < 0.6:
                uncommented_fields = report['total_fields'] - report['fields_with_comments']
                report['recommendations'].append(f"建议为 {uncommented_fields} 个字段添加备注说明")
            
            report['summary'] = {
                'table_comment_coverage': round(table_comment_coverage * 100, 2),
                'field_comment_coverage': round(field_comment_coverage * 100, 2),
                'overall_score': round((table_comment_coverage + field_comment_coverage) / 2 * 100, 2)
            }
            
            return report
            
        except Exception as e:
            logger.error(f"获取元数据完整性报告失败: {e}")
            return {}
    
    def close(self):
        """关闭数据库连接"""
        if self.engine:
            self.engine.dispose()
            logger.info("数据库连接已关闭")
    
    def clear_schema_cache(self):
        """清除架构缓存"""
        self.schema_cache.clear()
        logger.info("数据库架构缓存已清除")
    
    def update_table_comment(self, table_name: str, comment: str) -> Tuple[bool, str]:
        """更新表的备注信息"""
        try:
            if Config.DB_TYPE.lower() == 'mysql':
                # MySQL 语法
                sql = text("ALTER TABLE `{table_name}` COMMENT = :comment".format(table_name=table_name))
                with self.engine.connect() as connection:
                    with connection.begin():  # 使用事务
                        connection.execute(sql, {"comment": comment})
            elif Config.DB_TYPE.lower() == 'postgresql':
                # PostgreSQL 语法
                sql = text('COMMENT ON TABLE "{table_name}" IS :comment'.format(table_name=table_name))
                with self.engine.connect() as connection:
                    with connection.begin():  # 使用事务
                        connection.execute(sql, {"comment": comment})
            else:
                return False, f"不支持的数据库类型: {Config.DB_TYPE}"
            
            # 清除缓存，强制重新获取
            if table_name in self.schema_cache:
                del self.schema_cache[table_name]
            
            # 强制刷新inspector缓存
            self.inspector = inspect(self.engine)
            
            logger.info(f"已更新表 {table_name} 的备注: {comment}")
            return True, "表备注更新成功"
            
        except Exception as e:
            logger.error(f"更新表备注失败 {table_name}: {e}")
            return False, f"更新失败: {str(e)}"
    
    def update_column_comment(self, table_name: str, column_name: str, comment: str, column_definition: str = None) -> Tuple[bool, str]:
        """更新字段的备注信息"""
        try:
            if Config.DB_TYPE.lower() == 'mysql':
                # MySQL 需要完整的字段定义
                if not column_definition:
                    # 获取当前字段定义
                    schema = self.get_table_schema(table_name)
                    column_info = None
                    for col in schema.get('columns', []):
                        if col['name'] == column_name:
                            column_info = col
                            break
                    
                    if not column_info:
                        return False, f"字段 {column_name} 不存在"
                    
                    # 构建字段定义
                    nullable = "NULL" if column_info['nullable'] else "NOT NULL"
                    
                    # 处理默认值
                    default_clause = ""
                    if column_info.get('default') is not None:
                        default_value = column_info['default']
                        # 如果默认值是字符串类型，需要加引号（除非是特殊关键字）
                        if isinstance(default_value, str):
                            special_keywords = ['CURRENT_TIMESTAMP', 'NOW()', 'NULL']
                            if default_value.upper() not in special_keywords:
                                default_value = f"'{default_value}'"
                        default_clause = f" DEFAULT {default_value}"
                    
                    column_definition = f"{column_info['type']} {nullable}{default_clause}"
                
                # 使用格式化的SQL和命名参数
                sql = text("ALTER TABLE `{table_name}` MODIFY COLUMN `{column_name}` {column_definition} COMMENT :comment".format(
                    table_name=table_name, 
                    column_name=column_name, 
                    column_definition=column_definition
                ))
                with self.engine.connect() as connection:
                    with connection.begin():  # 使用事务
                        connection.execute(sql, {"comment": comment})
                    
            elif Config.DB_TYPE.lower() == 'postgresql':
                # PostgreSQL 语法
                sql = text('COMMENT ON COLUMN "{table_name}"."{column_name}" IS :comment'.format(
                    table_name=table_name, 
                    column_name=column_name
                ))
                with self.engine.connect() as connection:
                    with connection.begin():  # 使用事务
                        connection.execute(sql, {"comment": comment})
            else:
                return False, f"不支持的数据库类型: {Config.DB_TYPE}"
            
            # 清除缓存，强制重新获取
            if table_name in self.schema_cache:
                del self.schema_cache[table_name]
            
            # 强制刷新inspector缓存
            self.inspector = inspect(self.engine)
            
            logger.info(f"已更新表 {table_name} 字段 {column_name} 的备注: {comment}")
            return True, "字段备注更新成功"
            
        except Exception as e:
            logger.error(f"更新字段备注失败 {table_name}.{column_name}: {e}")
            return False, f"更新失败: {str(e)}"
    
    def get_table_details_for_editing(self, table_name: str = None, force_refresh: bool = False) -> Dict[str, Any]:
        """获取用于编辑的表详细信息"""
        try:
            if table_name:
                # 获取指定表的详细信息
                schema = self.get_table_schema(table_name, force_refresh=force_refresh)
                if not schema:
                    return {'error': f'表 {table_name} 不存在'}
                
                return {
                    'table_name': table_name,
                    'table_comment': schema.get('table_comment', ''),
                    'columns': schema.get('columns', []),
                    'primary_keys': schema.get('primary_keys', []),
                    'foreign_keys': schema.get('foreign_keys', [])
                }
            else:
                # 获取所有表的摘要信息
                tables = self.get_table_names()
                table_summary = []
                
                for table in tables:
                    schema = self.get_table_schema(table)
                    if schema:
                        table_summary.append({
                            'table_name': table,
                            'table_comment': schema.get('table_comment', ''),
                            'column_count': len(schema.get('columns', [])),
                            'has_pk': bool(schema.get('primary_keys', [])),
                            'has_fk': bool(schema.get('foreign_keys', []))
                        })
                
                return {'tables': table_summary}
                
        except Exception as e:
            logger.error(f"获取表详细信息失败: {e}")
            return {'error': str(e)} 