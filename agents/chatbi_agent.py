"""
ChatBI Agent
使用 Agently 框架将自然语言查询转换为 SQL 查询
"""
from agently import Agently
import json
from typing import Dict, List, Any, Tuple
from config import Config
from database.db_manager import DatabaseManager
from loguru import logger
import re
import pandas as pd

class ChatBIAgent:
    """ChatBI Agent 类"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        
        # 验证配置
        if not Config.DASHSCOPE_API_KEY:
            raise ValueError("DashScope API 密钥未配置，请在 .env 文件中设置 DASHSCOPE_API_KEY")
        
        # 创建专门的 SQL 生成 Agent
        self.sql_agent = self._create_sql_agent()
        if not self.sql_agent:
            raise RuntimeError("SQL Agent 创建失败")
        
        # 创建数据分析 Agent
        self.analysis_agent = self._create_analysis_agent()
        if not self.analysis_agent:
            raise RuntimeError("分析 Agent 创建失败")
        
        # 获取数据库结构信息
        self.db_schema = self.db_manager.get_database_schema()
        
        logger.info("ChatBI Agent 初始化完成")
    
    def _create_sql_agent(self):
        """创建 SQL 生成专用 Agent"""
        try:
            # 使用 Agently 4.0 正确的 API
            agent = Agently.create_agent()
            
            # 配置 API 密钥和模型 - 使用 OpenAI 兼容模式连接 DashScope
            if Config.DASHSCOPE_API_KEY:
                # 使用 OpenAI 兼容模式连接 DashScope
                agent.set_settings("plugins.ModelRequester.activate", "OpenAICompatible")
                agent.set_settings("plugins.ModelRequester.OpenAICompatible.base_url", "https://dashscope.aliyuncs.com/compatible-mode/v1")
                agent.set_settings("plugins.ModelRequester.OpenAICompatible.auth", f"Bearer {Config.DASHSCOPE_API_KEY}")
                agent.set_settings("plugins.ModelRequester.OpenAICompatible.default_model.chat", Config.AGENTLY_MODEL_CODE)
                logger.info(f"SQL Agent 配置 DashScope 模型 (OpenAI 兼容): {Config.AGENTLY_MODEL_CODE}")
            else:
                logger.error("DashScope API 密钥未配置")
                return None
            
            logger.info("SQL 生成 Agent 创建成功")
            return agent
        except Exception as e:
            logger.error(f"SQL Agent 创建失败: {e}")
            return None
    
    def _create_analysis_agent(self):
        """创建数据分析专用 Agent"""
        try:
            # 使用 Agently 4.0 正确的 API
            agent = Agently.create_agent()
            
            # 配置 API 密钥和模型 - 使用 OpenAI 兼容模式连接 DashScope
            if Config.DASHSCOPE_API_KEY:
                # 使用 OpenAI 兼容模式连接 DashScope
                agent.set_settings("plugins.ModelRequester.activate", "OpenAICompatible")
                agent.set_settings("plugins.ModelRequester.OpenAICompatible.base_url", "https://dashscope.aliyuncs.com/compatible-mode/v1")
                agent.set_settings("plugins.ModelRequester.OpenAICompatible.auth", f"Bearer {Config.DASHSCOPE_API_KEY}")
                agent.set_settings("plugins.ModelRequester.OpenAICompatible.default_model.chat", Config.AGENTLY_MODEL_QA)
                logger.info(f"分析 Agent 配置 DashScope 模型 (OpenAI 兼容): {Config.AGENTLY_MODEL_QA}")
            else:
                logger.error("DashScope API 密钥未配置")
                return None
            
            logger.info("数据分析 Agent 创建成功")
            return agent
        except Exception as e:
            logger.error(f"分析 Agent 创建失败: {e}")
            return None
    
    def _get_schema_prompt(self) -> str:
        """生成数据库结构描述"""
        schema_text = f"数据库名称: {self.db_schema['database_name']}\n\n"
        schema_text += "可用的表和字段:\n"
        
        for table_name, table_info in self.db_schema['tables'].items():
            schema_text += f"\n表名: {table_name}\n"
            
            # 添加表备注信息
            if table_info.get('table_comment'):
                schema_text += f"表说明: {table_info['table_comment']}\n"
            
            schema_text += "字段:\n"
            
            for column in table_info['columns']:
                nullable_text = "可空" if column['nullable'] else "非空"
                column_line = f"  - {column['name']} ({column['type']}, {nullable_text})"
                
                # 添加字段备注信息
                if column.get('comment'):
                    column_line += f" - {column['comment']}"
                
                schema_text += column_line + "\n"
            
            if table_info['primary_keys']:
                schema_text += f"主键: {', '.join(table_info['primary_keys'])}\n"
            
            if table_info['foreign_keys']:
                schema_text += "外键:\n"
                for fk in table_info['foreign_keys']:
                    schema_text += f"  - {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}\n"
        
        return schema_text
    
    def natural_language_to_sql(self, user_query: str) -> Tuple[bool, Dict[str, Any]]:
        """将自然语言查询转换为 SQL"""
        try:
            schema_prompt = self._get_schema_prompt()
            
            # 构建系统角色信息
            role_info = """你是一个专业的 SQL 查询生成专家。
你精通各种数据库系统，能够根据用户的自然语言描述生成准确的 SQL 查询语句。
你严格遵守安全规范，只生成 SELECT 查询，绝不生成任何修改数据的语句。"""
            

            user_input = f"""
数据库结构信息:
{schema_prompt}

用户查询: {user_query}

重要规则:
1. 只生成 SELECT 查询，不允许 INSERT、UPDATE、DELETE 等修改操作
2. 确保生成的 SQL 语法正确且符合标准
3. 自动添加 LIMIT 子句限制结果数量（最大 {Config.MAX_RESULTS_LIMIT} 行）
4. 使用适当的 WHERE 条件和 JOIN 语句
5. 对于模糊查询使用 LIKE 操作符
6. **重要**: 充分利用表说明和字段备注信息来理解业务含义，准确匹配用户的自然语言查询意图
7. 当字段名不够明确时，参考字段备注选择正确的字段
8. 根据表说明理解表的业务用途，选择合适的表进行查询
"""
            
            # 使用 Agently 4.0 的链式调用和结构化输出
            (
                self.sql_agent
                .info(role_info)
                .input(user_input)
                .output({
                    "sql": (str, "生成的SQL查询语句"),
                    "explanation": (str, "查询逻辑的中文解释"),
                    "confidence": (float, "置信度，0.0到1.0之间"),
                    "tables_used": ([str], "使用的表名列表"),
                    "query_type": (str, "查询类型描述")
                })
            )
            
            # 获取响应
            response = self.sql_agent.get_response()
            
            # 解析 Agent 响应
            logger.info(f"Agent 响应类型: {type(response)}")
            logger.info(f"Agent 响应内容: {response}")
            
            # 获取结构化结果
            result = None
            if hasattr(response, 'get_result'):
                result = response.get_result()
                logger.info(f"结构化结果: {result}")
            elif isinstance(response, dict):
                result = response
            elif isinstance(response, str):
                try:
                    result = json.loads(response)
                except json.JSONDecodeError:
                    # 如果不是 JSON 格式，构造一个简单的响应
                    logger.warning("Agent 返回非结构化格式，尝试解析")
                    result = {
                        "sql": "SELECT 'Agent响应解析失败' as message",
                        "explanation": f"Agent 原始响应: {response}",
                        "confidence": 0.5,
                        "tables_used": [],
                        "query_type": "错误响应"
                    }
            else:
                # 构造默认响应
                result = {
                    "sql": "SELECT 'Agent响应格式错误' as message",
                    "explanation": f"无法解析 Agent 响应: {str(response)}",
                    "confidence": 0.3,
                    "tables_used": [],
                    "query_type": "解析错误"
                }
            
            # 验证生成的 SQL
            if result and 'sql' in result:
                sql = result['sql']
                is_valid, validation_msg = self.db_manager.validate_sql(sql)
                
                if not is_valid:
                    return False, {
                        'error': f'生成的 SQL 验证失败: {validation_msg}',
                        'generated_sql': sql
                    }
                
                return True, result
            else:
                return False, {'error': '无法从 Agent 响应中提取 SQL'}
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败: {e}")
            return False, {'error': 'Agent 返回格式错误'}
        except Exception as e:
            logger.error(f"SQL 生成失败: {e}")
            return False, {'error': f'SQL 生成失败: {str(e)}'}
    
    def execute_query_with_analysis(self, user_query: str) -> Dict[str, Any]:
        """执行查询并提供智能分析"""
        # 第一步：生成 SQL
        success, sql_result = self.natural_language_to_sql(user_query)
        
        if not success:
            return {
                'success': False,
                'error': sql_result.get('error', '未知错误'),
                'user_query': user_query
            }
        
        # 第二步：执行 SQL 查询
        sql = sql_result['sql']
        success, query_result = self.db_manager.execute_query(sql)
        
        if not success:
            return {
                'success': False,
                'error': f'SQL 执行失败: {query_result}',
                'sql': sql,
                'user_query': user_query
            }
        
        # 第三步：分析查询结果
        analysis = self._analyze_results(user_query, sql_result, query_result)
        
        return {
            'success': True,
            'user_query': user_query,
            'sql_info': sql_result,
            'query_results': query_result,
            'analysis': analysis
        }
    
    def _analyze_results(self, user_query: str, sql_info: Dict, query_result: Dict) -> Dict[str, Any]:
        """分析查询结果并提供洞察"""
        try:
            data = query_result.get('data', [])
            columns = query_result.get('columns', [])
            row_count = query_result.get('row_count', 0)
            sql = sql_info.get('sql', '')
            
            # 分析查询类型
            query_type = self._analyze_query_type(sql, data, columns)
            
            # 获取可视化建议
            visualization_suggestion = self.get_visualization_suggestion(query_type, data)
            
            # 构建角色信息
            role_info = """你是一个专业的数据分析专家。
你擅长从查询结果中发现有价值的信息和洞察，能够提供专业的数据解读和建议。
你的分析要深入浅出，既专业又易懂。"""
            
            # 构建分析提示
            analysis_input = f"""
用户原始问题: {user_query}
生成的SQL: {sql}
查询说明: {sql_info.get('explanation', '')}

查询结果统计:
- 返回行数: {row_count}
- 字段数量: {len(columns)}
- 字段列表: {', '.join(columns)}

查询类型分析:
- 是否为清单查询: {query_type['is_list']}
- 是否为聚合查询: {query_type['is_aggregate']}
- 是否为时间序列: {query_type['is_time_series']}

前5行数据示例:
{json.dumps(data[:5], ensure_ascii=False, indent=2)}

请提供以下分析:
1. 数据概览和主要发现
2. 数值型数据的统计特征（如果有）
3. 可能的业务洞察
4. 数据质量评估
5. 建议的后续分析方向

请用中文回答，内容要专业且易懂。
"""
            
            # 使用分析 Agent
            try:
                (
                    self.analysis_agent
                    .info(role_info)
                    .input(analysis_input)
                )
                
                # 获取响应
                analysis_response = self.analysis_agent.get_response()
                
                logger.info(f"分析 Agent 响应类型: {type(analysis_response)}")
                
                # 处理分析响应
                if hasattr(analysis_response, 'get_text'):
                    detailed_analysis = analysis_response.get_text()
                elif isinstance(analysis_response, str):
                    detailed_analysis = analysis_response
                else:
                    detailed_analysis = str(analysis_response)
                    
            except Exception as e:
                logger.error(f"分析 Agent 调用失败: {e}")
                detailed_analysis = "数据分析功能暂时不可用，但查询成功完成。"
            
            return {
                'summary': f"共查询到 {row_count} 条记录，包含 {len(columns)} 个字段",
                'detailed_analysis': detailed_analysis,
                'data_preview': data[:10],  # 返回前10行作为预览
                'statistics': self._calculate_basic_stats(data, columns),
                'query_type': query_type,
                'visualization': visualization_suggestion
            }
            
        except Exception as e:
            logger.error(f"结果分析失败: {e}")
            return {
                'summary': f"查询成功，返回 {query_result.get('row_count', 0)} 条记录",
                'detailed_analysis': "分析功能暂时不可用",
                'data_preview': query_result.get('data', [])[:10],
                'statistics': {},
                'query_type': {'should_visualize': False},
                'visualization': {'should_visualize': False}
            }
    
    def _calculate_basic_stats(self, data: List[Dict], columns: List[str]) -> Dict[str, Any]:
        """计算基本统计信息"""
        stats = {}
        
        if not data:
            return stats
        
        for column in columns:
            column_data = [row.get(column) for row in data if row.get(column) is not None]
            
            if not column_data:
                continue
            
            # 检查是否为数值类型
            numeric_data = []
            for value in column_data:
                try:
                    if isinstance(value, (int, float)):
                        numeric_data.append(float(value))
                    elif isinstance(value, str) and value.replace('.', '').replace('-', '').isdigit():
                        numeric_data.append(float(value))
                except:
                    continue
            
            if numeric_data:
                stats[column] = {
                    'type': 'numeric',
                    'count': len(numeric_data),
                    'min': min(numeric_data),
                    'max': max(numeric_data),
                    'avg': sum(numeric_data) / len(numeric_data),
                    'non_null_count': len(column_data)
                }
            else:
                # 字符串类型统计
                unique_values = set(str(v) for v in column_data)
                stats[column] = {
                    'type': 'text',
                    'count': len(column_data),
                    'unique_count': len(unique_values),
                    'most_common': max(unique_values, key=lambda x: sum(1 for v in column_data if str(v) == x)) if unique_values else None
                }
        
        return stats
    
    def _analyze_query_type(self, sql: str, data: List[Dict], columns: List[str]) -> Dict[str, Any]:
        """分析查询类型并提供可视化建议"""
        sql_lower = sql.lower()
        
        # 检查是否为清单类型查询
        is_list_query = (
            'limit' in sql_lower and 
            not any(keyword in sql_lower for keyword in ['group by', 'count(', 'sum(', 'avg(', 'max(', 'min('])
        )
        
        # 检查是否为聚合查询
        is_aggregate_query = any(keyword in sql_lower for keyword in ['group by', 'count(', 'sum(', 'avg(', 'max(', 'min('])
        
        # 检查是否为时间序列查询
        is_time_series = False
        time_keywords = ['date', 'time', 'year', 'month', 'day', 'created_at', 'updated_at']
        for col in columns:
            if any(keyword in col.lower() for keyword in time_keywords):
                is_time_series = True
                break
        
        # 分析数据特征
        df = pd.DataFrame(data) if data else pd.DataFrame()
        
        query_type = {
            'is_list': is_list_query,
            'is_aggregate': is_aggregate_query,
            'is_time_series': is_time_series,
            'should_visualize': not is_list_query and (is_aggregate_query or is_time_series),
            'data_shape': df.shape if not df.empty else (0, 0),
            'numeric_columns': [],
            'categorical_columns': [],
            'date_columns': []
        }
        
        # 分析列类型
        if not df.empty:
            for col in df.columns:
                try:
                    # 尝试转换为数值类型
                    pd.to_numeric(df[col], errors='raise')
                    query_type['numeric_columns'].append(col)
                except:
                    # 检查是否为日期类型
                    if any(keyword in col.lower() for keyword in time_keywords):
                        query_type['date_columns'].append(col)
                    else:
                        query_type['categorical_columns'].append(col)
        
        return query_type
    
    def get_visualization_suggestion(self, query_type: Dict[str, Any], data: List[Dict]) -> Dict[str, Any]:
        """根据查询类型和数据特征生成可视化建议"""
        if not query_type['should_visualize'] or not data:
            return {'should_visualize': False, 'reason': '清单类型查询或无数据，不需要可视化'}
        
        suggestions = []
        numeric_cols = query_type['numeric_columns']
        categorical_cols = query_type['categorical_columns']
        date_cols = query_type['date_columns']
        
        # 时间序列图表
        if query_type['is_time_series'] and date_cols and numeric_cols:
            suggestions.append({
                'chart_type': 'line',
                'title': '时间序列趋势图',
                'x_column': date_cols[0],
                'y_column': numeric_cols[0],
                'description': '展示数据随时间的变化趋势'
            })
        
        # 条形图/柱状图
        if categorical_cols and numeric_cols:
            suggestions.append({
                'chart_type': 'bar',
                'title': '分类数据对比图',
                'x_column': categorical_cols[0],
                'y_column': numeric_cols[0],
                'description': '对比不同类别的数值大小'
            })
        
        # 饼图（适用于分类数据占比）
        if len(categorical_cols) >= 1 and len(numeric_cols) >= 1 and len(data) <= 20:
            suggestions.append({
                'chart_type': 'pie',
                'title': '占比分析图',
                'labels_column': categorical_cols[0],
                'values_column': numeric_cols[0],
                'description': '展示各部分的占比关系'
            })
        
        # 散点图（适用于两个数值变量）
        if len(numeric_cols) >= 2:
            suggestions.append({
                'chart_type': 'scatter',
                'title': '相关性分析图',
                'x_column': numeric_cols[0],
                'y_column': numeric_cols[1],
                'description': '分析两个数值变量之间的关系'
            })
        
        return {
            'should_visualize': True,
            'suggestions': suggestions[:2],  # 最多返回2个建议
            'primary_suggestion': suggestions[0] if suggestions else None
        }
    
    def get_suggested_queries(self, table_name: str = None) -> List[Dict[str, str]]:
        """获取建议的查询示例"""
        suggestions = [
            {
                'query': '职业卫生技术服务中心2025年每个月的工资总额趋势',
                'description': '时间序列分析'
            },
            {
                'query': '2025年2月各产品线人工成本总额对比',
                'description': '条形图'
            },
             {
                'query': '青岛 2025年各月份税前利润总额',
                'description': '时间序列分析'
            },
        ]
        
        if table_name and table_name in self.db_schema['tables']:
            table_info = self.db_schema['tables'][table_name]
            table_suggestions = [
                {
                    'query': f'查看{table_name}表的基本统计信息',
                    'description': f'了解{table_name}表的数据概况'
                },
                {
                    'query': f'显示{table_name}表的前20条记录',
                    'description': f'预览{table_name}表数据'
                }
            ]
            suggestions.extend(table_suggestions)
        
        return suggestions
    
    def get_database_metadata_report(self) -> Dict[str, Any]:
        """获取数据库元数据完整性报告"""
        try:
            report = self.db_manager.get_metadata_completeness_report()
            
            # 添加AI分析和建议
            if report:
                ai_analysis = self._analyze_metadata_quality(report)
                report['ai_analysis'] = ai_analysis
            
            return report
            
        except Exception as e:
            logger.error(f"获取元数据报告失败: {e}")
            return {'error': str(e)}
    
    def _analyze_metadata_quality(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """分析元数据质量并提供AI建议"""
        summary = report.get('summary', {})
        overall_score = summary.get('overall_score', 0)
        
        # 根据得分提供建议
        if overall_score >= 80:
            quality_level = "优秀"
            ai_advice = "您的数据库元数据质量很高，这将大大提升ChatBI的查询准确性。"
        elif overall_score >= 60:
            quality_level = "良好"
            ai_advice = "您的数据库元数据质量不错，但仍有改进空间。建议补充缺失的表和字段备注。"
        elif overall_score >= 40:
            quality_level = "一般"
            ai_advice = "建议优先为核心业务表添加详细的备注说明，这将显著提升自然语言查询的准确性。"
        else:
            quality_level = "需要改进"
            ai_advice = "强烈建议为所有表和关键字段添加业务含义备注，这对ChatBI的理解能力至关重要。"
        
        return {
            'quality_level': quality_level,
            'score': overall_score,
            'advice': ai_advice,
            'impact_on_chatbi': self._get_impact_description(overall_score)
        }
    
    def _get_impact_description(self, score: float) -> str:
        """描述元数据质量对ChatBI性能的影响"""
        if score >= 80:
            return "高质量的元数据使ChatBI能够精确理解用户查询意图，生成准确的SQL语句。"
        elif score >= 60:
            return "良好的元数据覆盖率能帮助ChatBI正确理解大部分查询，但在复杂业务场景下可能需要用户提供更多上下文。"
        elif score >= 40:
            return "中等的元数据质量可能导致ChatBI在理解某些业务术语时出现偏差，建议用户使用更具体的字段名称。"
        else:
            return "缺少元数据可能导致ChatBI难以准确理解业务含义，建议用户在查询时提供具体的表名和字段名。" 