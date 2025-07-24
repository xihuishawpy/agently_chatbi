#!/usr/bin/env python3
"""
Agently API 测试脚本
验证 Agently 框架的基本功能是否正常
"""
import sys
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def test_agently_import():
    """测试 Agently 导入"""
    print("🔍 测试 Agently 导入...")
    try:
        from agently import Agently
        print(f"✅ Agently 导入成功")
        return True
    except ImportError as e:
        print(f"❌ Agently 导入失败: {e}")
        return False

def test_agent_creation():
    """测试 Agent 创建"""
    print("\n🔍 测试 Agent 创建...")
    try:
        from agently import Agently
        
        # 根据 Agently 4.0 文档，直接创建 Agent
        agent = Agently.create_agent()
        print("✅ Agent 创建成功")
        
        # 配置 API 密钥 (如果有)
        api_key = os.getenv('DASHSCOPE_API_KEY')
        if api_key:
            # 设置 DashScope API 密钥
            agent.set_settings("model.DashScope.api_key", api_key)
            print("✅ DashScope API 密钥配置成功")
        
        return agent
    except Exception as e:
        print(f"❌ Agent 创建失败: {e}")
        print(f"错误详情: {str(e)}")
        return None

def test_simple_query(agent):
    """测试简单查询 - 使用 Agently 4.0 正确的调用方式"""
    print("\n🔍 测试简单查询...")
    try:
        # 根据 Agently 4.0 文档，构建链式调用然后获取响应
        (
            agent
            .input("请回答：1+1等于多少？")
        )
        
        # 获取响应
        response = agent.get_response()
        print(f"✅ 查询成功，响应类型: {type(response)}")
        
        # 尝试获取文本内容
        if hasattr(response, 'get_text'):
            text_content = response.get_text()
            print(f"📝 文本响应: {text_content}")
        else:
            print(f"📝 响应内容: {response}")
        
        return True
    except Exception as e:
        print(f"❌ 查询失败: {e}")
        print(f"错误详情: {str(e)}")
        return False

def test_structured_output(agent):
    """测试结构化输出 - 使用 Agently 4.0 的 output 方法"""
    print("\n🔍 测试结构化输出...")
    try:
        # 使用 Agently 4.0 的结构化输出
        (
            agent
            .input("请分析：北京是中国的首都吗？")
            .output({
                "question": (str, "用户提出的问题"),
                "answer": (str, "回答"),
                "confidence": (float, "置信度，0到1之间的数值"),
                "reasoning": (str, "推理过程")
            })
        )
        
        # 获取响应
        response = agent.get_response()
        print(f"✅ 结构化查询成功，响应类型: {type(response)}")
        
        # 获取结构化结果
        if hasattr(response, 'get_result'):
            result = response.get_result()
            print(f"✅ 结构化结果: {result}")
        elif hasattr(response, 'get_text'):
            text_content = response.get_text()
            print(f"📝 文本响应: {text_content}")
        else:
            print(f"📝 响应内容: {response}")
        
        return True
    except Exception as e:
        print(f"❌ 结构化查询失败: {e}")
        return False

def test_role_setting(agent):
    """测试角色设置 - 使用 info 方法"""
    print("\n🔍 测试角色设置...")
    try:
        # 使用 info 方法设置角色信息
        (
            agent
            .info("你是一个专业的数据分析师，精通 SQL 查询")
            .input("请介绍一下自己的能力")
        )
        
        # 获取响应
        response = agent.get_response()
        print(f"✅ 角色设置查询成功，响应类型: {type(response)}")
        
        # 获取响应内容
        if hasattr(response, 'get_text'):
            text_content = response.get_text()
            print(f"📝 响应内容: {text_content}")
        else:
            print(f"📝 响应内容: {response}")
        
        return True
    except Exception as e:
        print(f"❌ 角色设置失败: {e}")
        return False

def test_agent_methods(agent):
    """测试 Agent 可用方法"""
    print("\n🔍 查看 Agent 可用方法...")
    try:
        methods = [method for method in dir(agent) if not method.startswith('_')]
        print(f"✅ Agent 可用方法: {methods}")
        return True
    except Exception as e:
        print(f"❌ 查看方法失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 Agently API 测试开始")
    print("=" * 50)
    
    # 检查环境变量
    api_key = os.getenv('DASHSCOPE_API_KEY')
    if not api_key:
        print("⚠️  警告: 未配置 DASHSCOPE_API_KEY，某些功能可能无法使用")
    else:
        print(f"✅ API 密钥已配置: {api_key[:10]}...")
    
    # 测试导入
    if not test_agently_import():
        print("\n❌ 基础测试失败，请检查 Agently 安装")
        sys.exit(1)
    
    # 测试 Agent 创建
    agent = test_agent_creation()
    if not agent:
        print("\n❌ Agent 创建失败")
        sys.exit(1)
    
    # 查看 Agent 方法
    test_agent_methods(agent)
    
    # 测试各种功能
    if api_key:
        # 测试简单查询
        if test_simple_query(agent):
            print("✅ 简单查询测试通过")
        else:
            print("⚠️  简单查询测试失败")
        
        # 测试结构化输出
        if test_structured_output(agent):
            print("✅ 结构化输出测试通过")
        else:
            print("⚠️  结构化输出测试失败")
        
        # 测试角色设置
        if test_role_setting(agent):
            print("✅ 角色设置测试通过")
        else:
            print("⚠️  角色设置测试失败")
    else:
        print("⚠️  跳过 API 调用测试 (未配置 API 密钥)")
    
    print("\n🎉 Agently API 测试完成！")
    print("\n📋 测试总结:")
    print("- Agently 导入: ✅")
    print("- Agent 创建: ✅") 
    if api_key:
        print("- API 调用: 需要查看上述结果")
    else:
        print("- API 调用: 跳过 (无 API 密钥)")

if __name__ == "__main__":
    main() 