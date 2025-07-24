#!/usr/bin/env python3
"""
测试 SQL 查询功能
"""
import os
from dotenv import load_dotenv
from database.db_manager import DatabaseManager
from agents.chatbi_agent import ChatBIAgent
from loguru import logger

# 加载环境变量
load_dotenv()

def test_show_tables():
    """测试查看所有表的功能"""
    print("\n🔍 测试查看所有表...")
    try:
        # 创建数据库管理器实例
        db_manager = DatabaseManager()
        
        # 创建 ChatBI Agent 实例
        agent = ChatBIAgent(db_manager)
        
        # 测试查询
        query = "查看数据库中的所有表"
        success, result = agent.natural_language_to_sql(query)
        
        # 打印结果
        print(f"查询成功: {success}")
        if success:
            print("\n生成的SQL信息:")
            print(f"SQL: {result.get('sql', '无')}")
            print(f"解释: {result.get('explanation', '无')}")
            print(f"置信度: {result.get('confidence', 0)}")
            print(f"使用的表: {result.get('tables_used', [])}")
            print(f"查询类型: {result.get('query_type', '无')}")
            
            # 执行SQL
            sql = result.get('sql')
            if sql:
                success, query_result = db_manager.execute_query(sql)
                if success:
                    print("\n查询结果:")
                    print(f"列: {query_result.get('columns', [])}")
                    print(f"数据: {query_result.get('data', [])}")
                    print(f"行数: {query_result.get('row_count', 0)}")
                else:
                    print(f"\n❌ SQL执行失败: {query_result}")
        else:
            print(f"\n❌ SQL生成失败: {result.get('error', '未知错误')}")
            
        return True
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        return False

def test_agent_response_methods():
    """测试Agent响应的不同方法"""
    print("\n🔍 测试Agent响应方法...")
    try:
        # 创建数据库管理器实例
        db_manager = DatabaseManager()
        
        # 创建 ChatBI Agent 实例
        agent = ChatBIAgent(db_manager)
        
        # 获取SQL Agent
        sql_agent = agent.sql_agent
        
        # 构建简单的测试查询
        (
            sql_agent
            .input("生成一个简单的测试查询: SELECT 'Hello World' as message")
            .output({
                "sql": (str, "生成的SQL查询语句"),
                "explanation": (str, "查询逻辑的中文解释")
            })
        )
        
        # 获取响应
        response = sql_agent.get_response()
        
        print(f"响应对象类型: {type(response)}")
        print(f"响应对象: {response}")
        
        # 测试不同的方法
        print("\n测试 get_text() 方法:")
        try:
            text_response = response.get_text()
            print(f"get_text() 成功: {text_response}")
        except Exception as e:
            print(f"get_text() 失败: {e}")
        
        print("\n测试 get_result() 方法:")
        try:
            result_response = response.get_result()
            print(f"get_result() 成功: {result_response}")
        except Exception as e:
            print(f"get_result() 失败: {e}")
        
        # 检查响应对象的属性
        print(f"\n响应对象的属性: {dir(response)}")
        
        return True
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 SQL查询测试开始")
    print("=" * 50)
    
    # 检查环境变量
    api_key = os.getenv('DASHSCOPE_API_KEY')
    if not api_key:
        print("⚠️  警告: 未配置 DASHSCOPE_API_KEY")
        return
    
    # 运行响应方法测试
    if test_agent_response_methods():
        print("\n✅ Agent响应方法测试完成")
    else:
        print("\n❌ Agent响应方法测试失败")
    
    # 运行查询测试
    if test_show_tables():
        print("\n✅ 查看表测试完成")
    else:
        print("\n❌ 查看表测试失败")
    
    print("\n🎉 SQL查询测试完成！")

if __name__ == "__main__":
    main()