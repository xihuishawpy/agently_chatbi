#!/usr/bin/env python3
"""
测试 ChatBI 系统的元数据获取功能
验证表备注和字段备注的获取是否正常工作
"""

from database.db_manager import DatabaseManager
from agents.chatbi_agent import ChatBIAgent
from config import Config
import json

def test_metadata_functionality():
    """测试元数据功能"""
    print("=== ChatBI 元数据功能测试 ===\n")
    
    try:
        # 初始化数据库管理器
        print("1. 连接数据库...")
        db_manager = DatabaseManager()
        
        if not db_manager.engine:
            print("❌ 数据库连接失败")
            return
        
        print("✅ 数据库连接成功")
        
        # 测试获取表名
        print("\n2. 获取表列表...")
        tables = db_manager.get_table_names()
        print(f"✅ 发现 {len(tables)} 个表: {', '.join(tables[:5])}{'...' if len(tables) > 5 else ''}")
        
        # 测试获取表结构（包含备注）
        print("\n3. 测试元数据获取功能...")
        if tables:
            table_name = tables[0]
            print(f"正在分析表: {table_name}")
            
            schema = db_manager.get_table_schema(table_name)
            
            if schema:
                print(f"✅ 表结构获取成功")
                print(f"  - 表名: {schema['table_name']}")
                print(f"  - 表备注: {schema.get('table_comment', '未设置') or '未设置'}")
                print(f"  - 字段数量: {len(schema['columns'])}")
                
                # 显示前几个字段的备注信息
                print("\n字段信息（前5个）:")
                for i, col in enumerate(schema['columns'][:5]):
                    comment = col.get('comment', '') or '未设置'
                    print(f"  {i+1}. {col['name']} ({col['type']}) - 备注: {comment}")
                
            else:
                print("❌ 表结构获取失败")
        
        # 测试元数据完整性报告
        print("\n4. 生成元数据完整性报告...")
        report = db_manager.get_metadata_completeness_report()
        
        if report:
            print("✅ 元数据报告生成成功")
            summary = report.get('summary', {})
            print(f"  - 总表数: {report.get('total_tables', 0)}")
            print(f"  - 有备注的表: {report.get('tables_with_comments', 0)}")
            print(f"  - 表备注覆盖率: {summary.get('table_comment_coverage', 0)}%")
            print(f"  - 字段备注覆盖率: {summary.get('field_comment_coverage', 0)}%")
            print(f"  - 总体评分: {summary.get('overall_score', 0)}%")
            
            if report.get('recommendations'):
                print("\n建议:")
                for rec in report['recommendations']:
                    print(f"  - {rec}")
        else:
            print("❌ 元数据报告生成失败")
        
        # 测试 ChatBI Agent
        print("\n5. 测试 ChatBI Agent...")
        try:
            agent = ChatBIAgent(db_manager)
            print("✅ ChatBI Agent 初始化成功")
            
            # 测试获取数据库元数据报告
            metadata_report = agent.get_database_metadata_report()
            if metadata_report and 'ai_analysis' in metadata_report:
                ai_analysis = metadata_report['ai_analysis']
                print(f"  - AI 评估质量等级: {ai_analysis.get('quality_level', '未知')}")
                print(f"  - AI 建议: {ai_analysis.get('advice', '无建议')}")
            
        except Exception as e:
            print(f"❌ ChatBI Agent 测试失败: {e}")
        
        print("\n=== 测试完成 ===")
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

def show_sample_sql_creation():
    """展示为表添加备注的示例SQL"""
    print("\n=== 如何为数据库添加备注信息 ===\n")
    
    print("MySQL 示例:")
    print("-- 为表添加备注")
    print("ALTER TABLE users COMMENT = '用户信息表，存储系统用户的基本信息';")
    print()
    print("-- 为字段添加备注")
    print("ALTER TABLE users MODIFY COLUMN user_id INT NOT NULL AUTO_INCREMENT COMMENT '用户唯一标识';")
    print("ALTER TABLE users MODIFY COLUMN username VARCHAR(50) NOT NULL COMMENT '用户登录名';")
    print("ALTER TABLE users MODIFY COLUMN email VARCHAR(100) COMMENT '用户邮箱地址';")
    print("ALTER TABLE users MODIFY COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '账户创建时间';")
    print()
    
    print("PostgreSQL 示例:")
    print("-- 为表添加备注")
    print("COMMENT ON TABLE users IS '用户信息表，存储系统用户的基本信息';")
    print()
    print("-- 为字段添加备注")
    print("COMMENT ON COLUMN users.user_id IS '用户唯一标识';")
    print("COMMENT ON COLUMN users.username IS '用户登录名';")
    print("COMMENT ON COLUMN users.email IS '用户邮箱地址';")
    print("COMMENT ON COLUMN users.created_at IS '账户创建时间';")
    print()

if __name__ == "__main__":
    # 验证配置
    if not Config.validate_config():
        print("❌ 配置验证失败，请检查 .env 文件")
        exit(1)
    
    # 运行测试
    test_metadata_functionality()
    
    # 显示示例 SQL
    show_sample_sql_creation() 