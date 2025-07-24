#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ChatBI Gradio Frontend
使用 Gradio 提供友好的 Web 界面进行自然语言数据查询
"""

import gradio as gr
import pandas as pd
import json
from typing import Tuple, Dict, Any
from loguru import logger
from config import Config
from database.db_manager import DatabaseManager
from agents.chatbi_agent import ChatBIAgent
from auth_config import auth_config
import traceback
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sqlparse

class GradioChatBI:
    """Gradio ChatBI 应用类"""
    
    def __init__(self):
        """初始化应用"""
        self.db_manager = None
        self.chatbi_agent = None
        self.current_user = None
        self.current_user_id = None
        self.initialize_components()
    
    def initialize_components(self):
        """初始化组件"""
        try:
            # 初始化数据库管理器（默认配置）
            self.db_manager = DatabaseManager()
            
            # 初始化 ChatBI Agent
            self.chatbi_agent = ChatBIAgent(self.db_manager)
            
            logger.info("Gradio ChatBI 应用初始化成功")
            
        except Exception as e:
            logger.error(f"应用初始化失败: {e}")
            logger.error(traceback.format_exc())
            raise
    
    def initialize_user_session(self, user_id: str, user_info: Dict):
        """初始化用户会话"""
        try:
            self.current_user_id = user_id
            self.current_user = user_info
            
            # 使用新的安全配置方式获取数据库配置
            # 这会动态构建数据库URL，而不是从用户配置中直接读取
            db_config = auth_config.get_employee_database(user_id)
            
            if db_config and db_config.get('db_url'):
                db_url = db_config['db_url']
                
                # 切换到用户专属数据库
                if self.db_manager.switch_database(db_url):
                    # 重新初始化 ChatBI Agent
                    self.chatbi_agent = ChatBIAgent(self.db_manager)
                    logger.info(f"用户 {user_id} 会话初始化成功，数据库: {db_config.get('database_name')} ({db_config.get('database_type')})")
                    return True
                else:
                    logger.error(f"用户 {user_id} 数据库切换失败")
                    return False
            else:
                logger.warning(f"用户 {user_id} 数据库配置无效或URL构建失败")
                return False
                
        except Exception as e:
            logger.error(f"用户会话初始化失败: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def format_sql(self, sql: str) -> str:
        """格式化SQL语句，提升可读性"""
        try:
            # 使用 sqlparse 格式化 SQL
            formatted_sql = sqlparse.format(
                sql,
                reindent=True,          # 重新缩进
                keyword_case='upper',   # 关键字大写
                identifier_case='lower', # 标识符小写
                strip_comments=False,   # 保留注释
                indent_width=2,         # 缩进宽度
                indent_tabs=False,      # 使用空格而不是制表符
                use_space_around_operators=True  # 操作符周围使用空格
            )
            return formatted_sql.strip()
        except Exception as e:
            logger.error(f"SQL格式化失败: {e}")
            return sql  # 如果格式化失败，返回原始SQL
    
    def process_query(self, user_query: str) -> Tuple[str, str, str, str, str, str]:
        """
        处理用户查询
        
        Returns:
            Tuple[生成的SQL, 查询结果表格, 分析结果, 可视化图表, 状态信息, 错误信息]
        """
        if not user_query.strip():
            return "", "", "", None, "⚠️ 请输入查询问题", ""
        
        try:
            # 执行查询并获取分析
            result = self.chatbi_agent.execute_query_with_analysis(user_query)
            
            if not result['success']:
                error_msg = result.get('error', '未知错误')
                return "", "", "", None, f"❌ 查询失败", f"错误详情：{error_msg}"
            
            # 获取各部分结果
            sql_info = result.get('sql_info', {})
            query_results = result.get('query_results', {})
            analysis = result.get('analysis', {})
            
            # 生成的 SQL - 进行格式化
            raw_sql = sql_info.get('sql', '无')
            generated_sql = self.format_sql(raw_sql) if raw_sql != '无' else '无'
            
            # 查询结果表格
            results_df = self._format_results_table(query_results)
            
            # 分析结果
            analysis_text = self._format_analysis(analysis)
            
            # 生成可视化图表
            chart = self._create_visualization(query_results, analysis)
            
            # 状态信息
            row_count = query_results.get('row_count', 0)
            confidence = sql_info.get('confidence', 0.0)
            status_msg = f"✅ 查询成功！返回 {row_count} 条记录 (置信度: {confidence:.1%})"
            
            return generated_sql, results_df, analysis_text, chart, status_msg, ""
            
        except Exception as e:
            logger.error(f"查询处理失败: {e}")
            logger.error(traceback.format_exc())
            return "", "", "", None, "❌ 系统错误", f"错误详情：{str(e)}"
    
    def _format_results_table(self, query_results: Dict[str, Any]) -> str:
        """格式化查询结果为表格"""
        try:
            data = query_results.get('data', [])
            columns = query_results.get('columns', [])
            
            if not data:
                return "没有查询到数据"
            
            # 创建 DataFrame
            df = pd.DataFrame(data, columns=columns)
            
            # 限制显示行数
            max_rows = 50
            if len(df) > max_rows:
                df_display = df.head(max_rows)
                note = f"\n\n注：仅显示前 {max_rows} 行，共 {len(df)} 行数据"
            else:
                df_display = df
                note = f"\n\n总计 {len(df)} 行数据"
            
            # 转换为 HTML 表格
            html_table = df_display.to_html(index=False, classes='gradio-table', escape=False)
            return html_table + note
            
        except Exception as e:
            logger.error(f"表格格式化失败: {e}")
            return f"表格显示错误: {str(e)}"
    
    def _format_analysis(self, analysis: Dict[str, Any]) -> str:
        """格式化分析结果"""
        try:
            analysis_parts = []
            
            # 概要信息
            summary = analysis.get('summary', '')
            if summary:
                analysis_parts.append(f"📊 **数据概览**\n{summary}\n")
            
            # 查询类型信息
            query_type = analysis.get('query_type', {})
            if query_type:
                type_info = "🔍 **查询类型分析**\n"
                if query_type.get('is_list'):
                    type_info += "- 查询类型：清单查询（列表展示）\n"
                elif query_type.get('is_aggregate'):
                    type_info += "- 查询类型：聚合查询（统计分析）\n"
                if query_type.get('is_time_series'):
                    type_info += "- 包含时间序列数据\n"
                analysis_parts.append(type_info)
            
            # 可视化信息
            visualization = analysis.get('visualization', {})
            if visualization.get('should_visualize'):
                suggestion = visualization.get('primary_suggestion', {})
                if suggestion:
                    viz_info = f"📈 **可视化建议**\n"
                    viz_info += f"- 图表类型：{suggestion.get('description', '数据可视化')}\n"
                    viz_info += f"- 右侧已自动生成对应的可视化图表\n"
                    analysis_parts.append(viz_info)
            else:
                reason = visualization.get('reason', '')
                if reason:
                    analysis_parts.append(f"📋 **可视化说明**\n{reason}\n")
            
            # 详细分析
            detailed_analysis = analysis.get('detailed_analysis', '')
            if detailed_analysis:
                analysis_parts.append(f"🔬 **智能分析**\n{detailed_analysis}\n")
            
            # 统计信息
            statistics = analysis.get('statistics', {})
            if statistics:
                stats_text = "📊 **统计信息**\n"
                for column, stats in statistics.items():
                    if stats.get('type') == 'numeric':
                        stats_text += f"- **{column}**: 最小值 {stats['min']:.2f}, 最大值 {stats['max']:.2f}, 平均值 {stats['avg']:.2f}\n"
                    elif stats.get('type') == 'text':
                        stats_text += f"- **{column}**: {stats['unique_count']} 个不同值，最常见: {stats.get('most_common', 'N/A')}\n"
                analysis_parts.append(stats_text)
            
            return "\n".join(analysis_parts) if analysis_parts else "暂无分析结果"
            
        except Exception as e:
            logger.error(f"分析格式化失败: {e}")
            return f"分析显示错误: {str(e)}"
    
    def _create_visualization(self, query_results: Dict[str, Any], analysis: Dict[str, Any]) -> go.Figure:
        """创建可视化图表"""
        try:
            # 检查是否需要可视化
            visualization_info = analysis.get('visualization', {})
            if not visualization_info.get('should_visualize', False):
                return None
            
            data = query_results.get('data', [])
            if not data:
                return None
            
            # 转换为DataFrame
            df = pd.DataFrame(data)
            
            # 获取可视化建议
            suggestion = visualization_info.get('primary_suggestion')
            if not suggestion:
                return None
            
            chart_type = suggestion.get('chart_type')
            title = suggestion.get('title', '数据可视化')
            
            fig = None
            
            try:
                if chart_type == 'line' and 'x_column' in suggestion and 'y_column' in suggestion:
                    # 时间序列线图
                    x_col = suggestion['x_column']
                    y_col = suggestion['y_column']
                    if x_col in df.columns and y_col in df.columns:
                        # 尝试转换日期列
                        try:
                            df[x_col] = pd.to_datetime(df[x_col])
                        except:
                            pass
                        
                        fig = px.line(df, x=x_col, y=y_col, title=title)
                        fig.update_layout(
                            xaxis_title=x_col,
                            yaxis_title=y_col,
                            height=400
                        )
                
                elif chart_type == 'bar' and 'x_column' in suggestion and 'y_column' in suggestion:
                    # 条形图
                    x_col = suggestion['x_column']
                    y_col = suggestion['y_column']
                    if x_col in df.columns and y_col in df.columns:
                        # 限制显示的类别数量
                        if len(df) > 20:
                            df_plot = df.nlargest(20, y_col)
                        else:
                            df_plot = df
                        
                        fig = px.bar(df_plot, x=x_col, y=y_col, title=title)
                        fig.update_layout(
                            xaxis_title=x_col,
                            yaxis_title=y_col,
                            height=400,
                            xaxis={'tickangle': 45}
                        )
                
                elif chart_type == 'pie' and 'labels_column' in suggestion and 'values_column' in suggestion:
                    # 饼图
                    labels_col = suggestion['labels_column']
                    values_col = suggestion['values_column']
                    if labels_col in df.columns and values_col in df.columns:
                        # 限制显示的类别数量
                        if len(df) > 15:
                            df_plot = df.nlargest(15, values_col)
                        else:
                            df_plot = df
                        
                        fig = px.pie(df_plot, names=labels_col, values=values_col, title=title)
                        fig.update_layout(height=400)
                
                elif chart_type == 'scatter' and 'x_column' in suggestion and 'y_column' in suggestion:
                    # 散点图
                    x_col = suggestion['x_column']
                    y_col = suggestion['y_column']
                    if x_col in df.columns and y_col in df.columns:
                        fig = px.scatter(df, x=x_col, y=y_col, title=title)
                        fig.update_layout(
                            xaxis_title=x_col,
                            yaxis_title=y_col,
                            height=400
                        )
                
                # 如果没有生成图表，尝试自动选择
                if fig is None:
                    fig = self._auto_create_chart(df, title)
                
                if fig:
                    # 设置通用样式
                    fig.update_layout(
                        font=dict(size=12),
                        margin=dict(l=40, r=40, t=60, b=40),
                        showlegend=True
                    )
                
                return fig
                
            except Exception as chart_error:
                logger.error(f"图表生成错误: {chart_error}")
                return self._create_fallback_chart(df)
                
        except Exception as e:
            logger.error(f"可视化创建失败: {e}")
            return None
    
    def _auto_create_chart(self, df: pd.DataFrame, title: str) -> go.Figure:
        """自动创建合适的图表"""
        if df.empty:
            return None
        
        try:
            # 获取数值列和分类列
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
            
            if len(numeric_cols) >= 1 and len(categorical_cols) >= 1:
                # 条形图：分类 vs 数值
                x_col = categorical_cols[0]
                y_col = numeric_cols[0]
                
                # 如果类别太多，只显示前20个
                if len(df[x_col].unique()) > 20:
                    df_plot = df.groupby(x_col)[y_col].sum().nlargest(20).reset_index()
                else:
                    df_plot = df.groupby(x_col)[y_col].sum().reset_index()
                
                fig = px.bar(df_plot, x=x_col, y=y_col, title=title)
                return fig
                
            elif len(numeric_cols) >= 2:
                # 散点图：数值 vs 数值
                fig = px.scatter(df, x=numeric_cols[0], y=numeric_cols[1], title=title)
                return fig
                
            elif len(numeric_cols) >= 1:
                # 直方图：单个数值变量的分布
                fig = px.histogram(df, x=numeric_cols[0], title=f"{title} - {numeric_cols[0]}分布")
                return fig
            
        except Exception as e:
            logger.error(f"自动图表生成失败: {e}")
            return None
    
    def _create_fallback_chart(self, df: pd.DataFrame) -> go.Figure:
        """创建后备图表"""
        try:
            # 简单的数据概览图表
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            if numeric_cols:
                col = numeric_cols[0]
                fig = px.histogram(df, x=col, title=f"数据分布 - {col}")
                return fig
            else:
                # 如果没有数值列，显示数据量
                fig = go.Figure()
                fig.add_annotation(
                    text=f"查询返回 {len(df)} 条记录<br>包含 {len(df.columns)} 个字段",
                    x=0.5, y=0.5,
                    xref="paper", yref="paper",
                    font=dict(size=16),
                    showarrow=False
                )
                fig.update_layout(
                    title="查询结果概览",
                    height=300,
                    xaxis=dict(showgrid=False, showticklabels=False),
                    yaxis=dict(showgrid=False, showticklabels=False)
                )
                return fig
        except:
            return None
    
    def get_example_queries(self) -> list:
        """获取示例查询"""
        try:
            suggestions = self.chatbi_agent.get_suggested_queries()
            return [item['query'] for item in suggestions[:6]]  # 返回前6个示例
        except:
            return [
                "显示销售额最高的10个产品",
                "按月份统计总销售额", 
                "找出最活跃的客户",
                "分析各地区的销售表现",
                "统计各产品类别的平均价格",
                "查看用户注册趋势"
            ]
    
    def get_database_info(self) -> str:
        """获取数据库结构信息"""
        try:
            schema = self.chatbi_agent.db_schema
            
            # 构建美观的表格显示
            info_parts = []
            
            # 数据库基本信息
            info_parts.append("### 📊 数据库概览")
            info_parts.append(f"**数据库名称**: `{schema['database_name']}`")
            info_parts.append(f"**总表数量**: {len(schema['tables'])} 个")
            info_parts.append("")
            
            # 表格详细信息
            info_parts.append("### 📋 数据表详情")
            
            for i, (table_name, table_info) in enumerate(schema['tables'].items(), 1):
                column_count = len(table_info['columns'])
                table_comment = table_info.get('table_comment', '')
                
                # 表头信息
                info_parts.append(f"**{i}. {table_name}**")
                info_parts.append(f"   📈 字段数量: `{column_count}` 个")
                
                if table_comment:
                    info_parts.append(f"   💡 说明: *{table_comment}*")
                
                # 显示部分关键字段
                key_columns = []
                pk_columns = table_info.get('primary_keys', [])
                
                for col in table_info['columns'][:5]:  # 只显示前5个字段
                    col_info = f"`{col['name']}` ({col['type']})"
                    if col['name'] in pk_columns:
                        col_info += " 🔑"
                    if not col['nullable']:
                        col_info += " ⚠️"
                    if col.get('comment'):
                        col_info += f" - {col['comment']}"
                    key_columns.append(f"     • {col_info}")
                
                if key_columns:
                    info_parts.append("   🏗️ 主要字段:")
                    info_parts.extend(key_columns)
                    
                    if column_count > 5:
                        info_parts.append(f"     • ... 还有 {column_count - 5} 个字段")
                
                info_parts.append("")  # 空行分隔
            
            # 元数据质量信息
            try:
                metadata_report = self.chatbi_agent.get_database_metadata_report()
                if metadata_report and 'summary' in metadata_report:
                    summary = metadata_report['summary']
                    ai_analysis = metadata_report.get('ai_analysis', {})
                    
                    info_parts.append("### 🎯 数据质量评估")
                    
                    overall_score = summary.get('overall_score', 0)
                    quality_level = ai_analysis.get('quality_level', '未知')
                    
                    # 根据分数显示不同的emoji
                    if overall_score >= 80:
                        score_emoji = "🟢"
                    elif overall_score >= 60:
                        score_emoji = "🟡" 
                    else:
                        score_emoji = "🔴"
                    
                    info_parts.append(f"**总体评分**: {score_emoji} `{overall_score:.0f}%` ({quality_level})")
                    info_parts.append(f"**表备注覆盖率**: {summary.get('table_comment_coverage', 0):.0f}%")
                    info_parts.append(f"**字段备注覆盖率**: {summary.get('field_comment_coverage', 0):.0f}%")
                    
                    if ai_analysis.get('advice'):
                        info_parts.append(f"**优化建议**: {ai_analysis['advice']}")
                        
            except Exception as e:
                logger.error(f"获取元数据质量信息失败: {e}")
            
            return "\n".join(info_parts)
            
        except Exception as e:
            logger.error(f"获取数据库信息失败: {e}")
            return "❌ 无法获取数据库信息"
    
    def create_interface(self):
        """创建 Gradio 界面"""
        # 自定义 CSS
        custom_css = """
        .gradio-container {
            max-width: 1400px !important;
            margin: 0 auto;
        }
        .gradio-table {
            font-size: 12px;
        }
        .gradio-table th {
            background-color: #f0f0f0;
            font-weight: bold;
        }
        .gr-group {
            border-radius: 8px;
            padding: 15px;
        }
        .gr-button {
            border-radius: 6px;
        }
        .gr-examples {
            margin-top: 10px;
        }
        .gr-examples .gr-button {
            font-size: 13px;
            padding: 8px 12px;
            margin: 2px;
        }
        .login-container {
            max-width: 400px;
            margin: 50px auto;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        """
        
        with gr.Blocks(
            title="ChatBI",
            theme=gr.themes.Soft(),
            css=custom_css
        ) as app:
            
            # 用户状态管理
            user_state = gr.State(None)
            login_state = gr.State(False)
            
            # 登录界面
            with gr.Column(visible=True, elem_classes="login-container") as login_container:
                gr.Markdown("""
                # 🔐 ChatBI 用户登录
                
                请使用您的工号和密码登录系统
                """)
                
                with gr.Tabs():
                    # 登录Tab
                    with gr.TabItem("🔑 登录"):
                        login_employee_id = gr.Textbox(
                            label="工号",
                            placeholder="请输入您的工号",
                            max_lines=1
                        )
                        login_password = gr.Textbox(
                            label="密码",
                            placeholder="请输入密码",
                            type="password",
                            max_lines=1
                        )
                        login_btn = gr.Button("🔑 登录", variant="primary")
                        login_status = gr.Textbox(
                            label="登录状态",
                            interactive=False,
                            visible=False
                        )
                    
                    # 注册Tab
                    with gr.TabItem("📝 注册"):
                        register_employee_id = gr.Textbox(
                            label="工号",
                            placeholder="请输入您的工号",
                            max_lines=1
                        )
                        register_name = gr.Textbox(
                            label="姓名",
                            placeholder="请输入您的姓名",
                            max_lines=1
                        )
                        register_password = gr.Textbox(
                            label="密码",
                            placeholder="密码至少6位，需包含大小写字母和符号",
                            type="password",
                            max_lines=1
                        )
                        register_confirm_password = gr.Textbox(
                            label="确认密码",
                            placeholder="请再次输入密码",
                            type="password",
                            max_lines=1
                        )
                        register_btn = gr.Button("📝 注册", variant="secondary")
                        register_status = gr.Textbox(
                            label="注册状态",
                            interactive=False,
                            visible=False
                        )
                        
                        # 注册说明
                        gr.Markdown("""
                        ### 📋 注册说明
                        - 仅允许特定工号注册，请联系管理员确认权限
                        - 密码要求：至少6位，包含大小写字母和符号
                        - 每个工号仅能注册一次
                        - 注册成功后可直接登录使用
                        """)
            
            # 主应用界面
            with gr.Column(visible=False) as main_container:
                # 用户信息栏
                with gr.Row():
                    user_info_display = gr.Markdown("")
                    logout_btn = gr.Button("🚪 退出登录", size="sm", variant="secondary")
                
                gr.Markdown("""
                # ⭐ ChatBI: InsightAI
                
                产品开发者：肖晞晖（50992）- 应用管理部

                基于数据仓库，无需编写复杂的SQL语句，使用自然语言进行数据查询、分析、可视化，提升数据分析效率！
                """)
                
                with gr.Tabs():
                    # Tab 1: 智能查询
                    with gr.TabItem("🔍 智能查询", id="query_tab"):
                        with gr.Row():
                            with gr.Column(scale=3):
                                # 主查询区域
                                with gr.Group():
                                    gr.Markdown("### 💬 输入您的查询问题")
                                    query_input = gr.Textbox(
                                        label="自然语言查询",
                                        placeholder="例如：显示销售额最高的10个产品",
                                        lines=3,
                                        max_lines=5
                                    )
                                    
                                    with gr.Row():
                                        submit_btn = gr.Button("🔍 开始查询", variant="primary", scale=2)
                                        clear_btn = gr.Button("🗑️ 清空", scale=1)
                                
                                # 状态显示
                                status_output = gr.Textbox(
                                    label="查询状态",
                                    interactive=False,
                                    show_label=True
                                )
                                
                                error_output = gr.Textbox(
                                    label="错误信息",
                                    interactive=False,
                                    visible=False
                                )
                            
                            with gr.Column(scale=2):
                                # 示例查询
                                with gr.Group():
                                    gr.Markdown("### 📋 示例查询")
                                    example_queries = self.get_example_queries()
                                    examples = gr.Examples(
                                        examples=[[q] for q in example_queries],
                                        inputs=[query_input],
                                        label=""
                                    )
                        
                        # 结果显示区域
                        with gr.Row():
                            with gr.Column():
                                with gr.Group():
                                    gr.Markdown("### 🔧 生成的 SQL 查询")
                                    sql_output = gr.Code(
                                        label="",
                                        language="sql",
                                        interactive=False,
                                        show_label=False
                                    )
                        
                        with gr.Row():
                            with gr.Column():
                                with gr.Group():
                                    gr.Markdown("### 📊 查询结果")
                                    results_output = gr.HTML(
                                        label="",
                                        show_label=False
                                    )
                        
                        with gr.Row():
                            with gr.Column(scale=3):
                                with gr.Group():
                                    gr.Markdown("### 🔍 智能分析")
                                    analysis_output = gr.Markdown(
                                        label="",
                                        show_label=False
                                    )
                            
                            with gr.Column(scale=2):
                                with gr.Group():
                                    gr.Markdown("### 📈 数据可视化")
                                    chart_output = gr.Plot(
                                        label="",
                                        show_label=False
                                    )
                    
                    # Tab 2: 数据库管理
                    with gr.TabItem("🗃️ 数据库管理", id="database_tab"):
                        self._create_database_management_tab()
            
            # 查询Tab的事件处理
            def handle_submit(query):
                sql, results, analysis, chart, status, error = self.process_query(query)
                
                # 根据是否有错误来决定错误框的可见性
                error_visible = bool(error.strip())
                
                return (
                    sql,           # sql_output
                    results,       # results_output  
                    analysis,      # analysis_output
                    chart,         # chart_output
                    status,        # status_output
                    error,         # error_output value
                    gr.update(visible=error_visible)  # error_output visibility
                )
            
            def handle_clear():
                return (
                    "",            # query_input
                    "",            # sql_output
                    "",            # results_output
                    "",            # analysis_output
                    None,          # chart_output
                    "",            # status_output
                    "",            # error_output value
                    gr.update(visible=False)  # error_output visibility
                )
            
            # 绑定查询Tab事件
            submit_btn.click(
                fn=handle_submit,
                inputs=[query_input],
                outputs=[sql_output, results_output, analysis_output, chart_output, status_output, error_output, error_output]
            )
            
            query_input.submit(
                fn=handle_submit,
                inputs=[query_input],
                outputs=[sql_output, results_output, analysis_output, chart_output, status_output, error_output, error_output]
            )
            
            clear_btn.click(
                fn=handle_clear,
                outputs=[query_input, sql_output, results_output, analysis_output, chart_output, status_output, error_output, error_output]
            )
            
            # 登录和注册事件处理
            def handle_login(employee_id, password):
                """处理用户登录"""
                if not employee_id or not password:
                    return (
                        gr.update(visible=True, value="❌ 请输入工号和密码"),
                        gr.update(),  # user_state
                        gr.update(visible=True),  # login_container
                        gr.update(visible=False),  # main_container
                        ""  # user_info_display
                    )
                
                success, user_info = auth_config.authenticate_user(employee_id, password)
                
                if success:
                    # 初始化用户会话
                    if self.initialize_user_session(employee_id, user_info):
                        db_config = user_info.get('database_config', {})
                        user_display = f"👤 欢迎，{user_info.get('name', employee_id)} | 📊 数据库：{db_config.get('database_name', '未知')}"
                        
                        return (
                            gr.update(visible=False),  # login_status
                            user_info,  # user_state
                            gr.update(visible=False),  # login_container
                            gr.update(visible=True),   # main_container
                            user_display  # user_info_display
                        )
                    else:
                        return (
                            gr.update(visible=True, value="❌ 数据库连接失败，请联系管理员"),
                            gr.update(),  # user_state
                            gr.update(visible=True),  # login_container
                            gr.update(visible=False),  # main_container
                            ""  # user_info_display
                        )
                else:
                    return (
                        gr.update(visible=True, value="❌ 工号或密码错误"),
                        gr.update(),  # user_state
                        gr.update(visible=True),  # login_container
                        gr.update(visible=False),  # main_container
                        ""  # user_info_display
                    )
            
            def handle_register(employee_id, name, password, confirm_password):
                """处理用户注册"""
                if not all([employee_id, name, password, confirm_password]):
                    return gr.update(visible=True, value="❌ 请填写所有字段")
                
                if password != confirm_password:
                    return gr.update(visible=True, value="❌ 两次输入的密码不一致")
                
                success, message = auth_config.register_user(employee_id, password, name)
                
                if success:
                    return gr.update(visible=True, value=f"✅ {message}，请切换到登录页面")
                else:
                    return gr.update(visible=True, value=f"❌ {message}")
            
            def handle_logout():
                """处理用户退出"""
                self.current_user = None
                self.current_user_id = None
                
                return (
                    None,  # user_state
                    gr.update(visible=True),   # login_container
                    gr.update(visible=False),  # main_container
                    "",    # user_info_display
                    "",    # login_employee_id
                    "",    # login_password
                    gr.update(visible=False)   # login_status
                )
            
            # 绑定登录注册事件
            login_btn.click(
                fn=handle_login,
                inputs=[login_employee_id, login_password],
                outputs=[login_status, user_state, login_container, main_container, user_info_display]
            )
            
            register_btn.click(
                fn=handle_register,
                inputs=[register_employee_id, register_name, register_password, register_confirm_password],
                outputs=[register_status]
            )
            
            logout_btn.click(
                fn=handle_logout,
                outputs=[user_state, login_container, main_container, user_info_display, login_employee_id, login_password, login_status]
            )
        
        return app
    
    def _create_database_management_tab(self):
        """创建数据库管理Tab"""
        gr.Markdown("### 🗃️ 数据库结构管理")
        gr.Markdown("在这里查看和编辑数据库表结构，更新表和字段的备注信息，提升ChatBI的查询准确性。")
        
        with gr.Row():
            with gr.Column(scale=1):
                # 左侧：表列表
                with gr.Group():
                    gr.Markdown("#### 📋 数据表列表")
                    
                    # 刷新和缓存控制按钮
                    with gr.Row():
                        refresh_btn = gr.Button("🔄 刷新", size="sm", scale=1)
                        clear_cache_btn = gr.Button("🗑️ 清除缓存", size="sm", scale=1)
                    
                    # 表列表
                    table_list = gr.Dropdown(
                        choices=[],
                        label="选择数据表",
                        interactive=True,
                        value=None
                    )
                    
                    # 表统计信息
                    table_stats = gr.Markdown("请选择一个表查看详细信息")
                    
                    # 元数据质量报告
                    with gr.Accordion("📊 元数据质量报告", open=False):
                        metadata_report = gr.Markdown("")
            
            with gr.Column(scale=2):
                # 右侧：表详细信息和编辑
                with gr.Group():
                    gr.Markdown("#### 🛠️ 表结构详情与编辑")
                    
                    # 表基本信息编辑
                    with gr.Row():
                        with gr.Column():
                            selected_table_name = gr.Textbox(
                                label="表名",
                                interactive=False,
                                visible=False
                            )
                            
                            table_comment_input = gr.Textbox(
                                label="表备注",
                                placeholder="输入表的业务描述...",
                                lines=2,
                                interactive=True
                            )
                            
                            update_table_btn = gr.Button("💾 更新表备注", variant="secondary")
                    
                    # 字段信息展示和编辑
                    gr.Markdown("#### 📝 字段详情")
                    
                    # 字段表格
                    columns_table = gr.Dataframe(
                        headers=["字段名", "类型", "可空", "主键", "当前备注"],
                        datatype=["str", "str", "str", "str", "str"],
                        row_count=(0, "dynamic"),
                        col_count=(5, "fixed"),
                        interactive=False,
                        wrap=True
                    )
                    
                    # 字段备注编辑
                    with gr.Row():
                        column_name_dropdown = gr.Dropdown(
                            choices=[],
                            label="选择要编辑的字段",
                            interactive=True,
                            allow_custom_value=True,  # 允许自定义值，避免验证错误
                            value=None
                        )
                        
                        column_comment_input = gr.Textbox(
                            label="字段备注",
                            placeholder="输入字段的业务含义...",
                            lines=1,
                            interactive=True
                        )
                    
                    with gr.Row():
                        update_column_btn = gr.Button("💾 更新字段备注", variant="secondary")
                        clear_column_btn = gr.Button("🗑️ 清空", size="sm")
                    
                    # 操作状态显示
                    operation_status = gr.Textbox(
                        label="操作状态",
                        interactive=False,
                        show_label=True
                    )
        
        # 数据库管理Tab的事件处理
        def load_tables():
            """加载表列表"""
            try:
                tables = self.db_manager.get_table_names()
                if tables:
                    return gr.update(choices=tables, value=None)  # 不自动选择第一个表
                else:
                    return gr.update(choices=[], value=None)
            except Exception as e:
                logger.error(f"加载表列表失败: {e}")
                return gr.update(choices=[], value=None)
        
        def load_table_details(table_name, force_refresh=False):
            """加载表详细信息"""
            if not table_name:
                return "", [], gr.update(choices=[], value=None), "", "请选择一个表"
            
            try:
                details = self.db_manager.get_table_details_for_editing(table_name, force_refresh=force_refresh)
                
                if 'error' in details:
                    return "", [], gr.update(choices=[], value=None), "", f"加载失败: {details['error']}"
                
                # 表备注
                table_comment = details.get('table_comment', '')
                
                # 字段信息表格
                columns_data = []
                column_choices = []
                pk_columns = set(details.get('primary_keys', []))
                
                for col in details.get('columns', []):
                    col_name = col['name']
                    col_type = col['type']
                    nullable = "是" if col['nullable'] else "否"
                    is_pk = "是" if col_name in pk_columns else "否"
                    comment = col.get('comment', '') or ''
                    
                    columns_data.append([col_name, col_type, nullable, is_pk, comment])
                    column_choices.append(col_name)
                
                # 统计信息
                stats_info = f"""
**表名**: `{table_name}`
**字段数量**: {len(details.get('columns', []))} 个
**主键**: {', '.join(details.get('primary_keys', [])) or '无'}
**外键**: {len(details.get('foreign_keys', []))} 个
**表备注**: {'✅ 已设置' if table_comment else '❌ 未设置'}
**字段备注覆盖率**: {len([c for c in details.get('columns', []) if c.get('comment')]) / len(details.get('columns', [])) * 100:.0f}%
                """.strip()
                
                return (
                    table_comment,              # table_comment_input
                    columns_data,               # columns_table
                    gr.update(choices=column_choices, value=None),  # column_name_dropdown with proper update
                    stats_info,                 # table_stats
                    f"✅ 已加载表 {table_name} 的详细信息"  # operation_status
                )
                
            except Exception as e:
                logger.error(f"加载表详细信息失败: {e}")
                return "", [], gr.update(choices=[], value=None), "", f"❌ 加载失败: {str(e)}"
        
        def load_metadata_report():
            """加载元数据质量报告"""
            try:
                report = self.chatbi_agent.get_database_metadata_report()
                if 'error' in report:
                    return f"❌ 报告生成失败: {report['error']}"
                
                summary = report.get('summary', {})
                ai_analysis = report.get('ai_analysis', {})
                
                report_text = f"""
**📊 整体评估**
- 总体评分: {summary.get('overall_score', 0):.0f}% ({ai_analysis.get('quality_level', '未知')})
- 表备注覆盖率: {summary.get('table_comment_coverage', 0):.0f}%
- 字段备注覆盖率: {summary.get('field_comment_coverage', 0):.0f}%

**📋 统计信息**
- 总表数: {report.get('total_tables', 0)} 个
- 有备注的表: {report.get('tables_with_comments', 0)} 个
- 字段总数: {report.get('total_fields', 0)} 个
- 有备注的字段: {report.get('fields_with_comments', 0)} 个

**💡 AI建议**
{ai_analysis.get('advice', '暂无建议')}
                """.strip()
                
                return report_text
                
            except Exception as e:
                logger.error(f"生成元数据报告失败: {e}")
                return f"❌ 报告生成失败: {str(e)}"
        
        def update_table_comment(table_name, comment):
            """更新表备注"""
            if not table_name:
                return "❌ 请先选择一个表"
            
            try:
                success, message = self.db_manager.update_table_comment(table_name, comment)
                if success:
                    return f"✅ {message}"
                else:
                    return f"❌ {message}"
            except Exception as e:
                logger.error(f"更新表备注失败: {e}")
                return f"❌ 更新失败: {str(e)}"
        
        def update_table_comment_and_refresh(table_name, comment):
            """更新表备注并刷新显示"""
            # 先更新备注
            status = update_table_comment(table_name, comment)
            
            # 如果更新成功，强制刷新表详情
            if status.startswith("✅"):
                table_comment, columns_data, column_choices, stats_info, _ = load_table_details(table_name, force_refresh=True)
                return (
                    table_comment,       # table_comment_input - 显示更新后的表备注
                    columns_data,        # columns_table - 刷新表格
                    column_choices,      # column_name_dropdown - 刷新字段选择
                    stats_info,          # table_stats - 刷新统计信息
                    status,              # operation_status - 显示操作状态
                    ""                   # column_comment_input - 清空字段备注输入
                )
            else:
                # 更新失败，保持当前状态但显示错误
                return (
                    gr.update(),         # 不更新表备注输入
                    gr.update(),         # 不更新表格
                    gr.update(),         # 不更新字段选择
                    gr.update(),         # 不更新统计信息
                    status,              # 显示错误状态
                    gr.update()          # 不更新字段备注输入
                )
        
        def update_column_comment(table_name, column_name, comment):
            """更新字段备注"""
            if not table_name:
                return "❌ 请先选择一个表"
            if not column_name:
                return "❌ 请选择要编辑的字段"
            
            try:
                success, message = self.db_manager.update_column_comment(table_name, column_name, comment)
                if success:
                    return f"✅ {message}"
                else:
                    return f"❌ {message}"
            except Exception as e:
                logger.error(f"更新字段备注失败: {e}")
                return f"❌ 更新失败: {str(e)}"
        
        def update_column_comment_and_refresh(table_name, column_name, comment):
            """更新字段备注并刷新显示"""
            # 先更新备注
            status = update_column_comment(table_name, column_name, comment)
            
            # 如果更新成功，强制刷新表详情
            if status.startswith("✅"):
                table_comment, columns_data, column_choices, stats_info, _ = load_table_details(table_name, force_refresh=True)
                return (
                    table_comment,       # table_comment_input - 刷新表备注显示
                    columns_data,        # columns_table - 刷新表格显示
                    column_choices,      # column_name_dropdown - 刷新字段选择
                    stats_info,          # table_stats - 刷新统计信息
                    status,              # operation_status - 显示操作状态
                    gr.update(value=None), # column_name_dropdown - 清空字段选择
                    ""                   # column_comment_input - 清空字段备注输入
                )
            else:
                # 更新失败，保持当前状态但显示错误
                return (
                    gr.update(),         # 不更新表备注输入
                    gr.update(),         # 不更新表格
                    gr.update(),         # 不更新字段选择
                    gr.update(),         # 不更新统计信息
                    status,              # 显示错误状态
                    gr.update(),         # 不更新字段选择
                    gr.update()          # 不更新字段备注输入
                )
        
        def load_column_comment(table_name, column_name):
            """加载字段当前备注"""
            if not table_name or not column_name:
                return ""
            
            try:
                details = self.db_manager.get_table_details_for_editing(table_name)
                for col in details.get('columns', []):
                    if col['name'] == column_name:
                        return col.get('comment', '')
                return ""
            except:
                return ""
        
        def clear_cache():
            """清除数据库缓存"""
            try:
                self.db_manager.clear_schema_cache()
                return "✅ 缓存已清除，请重新选择表查看最新数据（提示：更新备注后会自动刷新，通常不需要手动清缓存）"
            except Exception as e:
                logger.error(f"清除缓存失败: {e}")
                return f"❌ 清除缓存失败: {str(e)}"
        
        # 绑定事件
        
        # 使用组件的默认加载行为初始化
        
        # 刷新按钮
        refresh_btn.click(
            fn=load_tables,
            outputs=[table_list]
        ).then(
            fn=load_metadata_report,
            outputs=[metadata_report]
        )
        
        # 清除缓存按钮
        clear_cache_btn.click(
            fn=clear_cache,
            outputs=[operation_status]
        )
        
        # 选择表时加载详细信息
        table_list.change(
            fn=load_table_details,
            inputs=[table_list],
            outputs=[table_comment_input, columns_table, column_name_dropdown, table_stats, operation_status]
        ).then(
            fn=lambda x: x,  # 保存选中的表名
            inputs=[table_list],
            outputs=[selected_table_name]
        )
        
        # 选择字段时加载字段备注
        column_name_dropdown.change(
            fn=load_column_comment,
            inputs=[selected_table_name, column_name_dropdown],
            outputs=[column_comment_input]
        )
        
        # 更新表备注
        update_table_btn.click(
            fn=update_table_comment_and_refresh,
            inputs=[selected_table_name, table_comment_input],
            outputs=[table_comment_input, columns_table, column_name_dropdown, table_stats, operation_status, column_comment_input]
        )
        
        # 更新字段备注
        update_column_btn.click(
            fn=update_column_comment_and_refresh,
            inputs=[selected_table_name, column_name_dropdown, column_comment_input],
            outputs=[table_comment_input, columns_table, column_name_dropdown, table_stats, operation_status, column_name_dropdown, column_comment_input]
        )
        
        # 清空字段备注输入
        clear_column_btn.click(
            fn=lambda: "",
            outputs=[column_comment_input]
        )

def main():
    """主函数"""
    try:
        # 创建应用实例
        gradio_app = GradioChatBI()
        
        # 创建界面
        app = gradio_app.create_interface()
        
        # 启动应用
        app.launch(
            server_name="0.0.0.0",
            server_port=8081,
            share=False,
            debug=True,
            show_error=True
        )
        
    except Exception as e:
        logger.error(f"Gradio 应用启动失败: {e}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main() 
