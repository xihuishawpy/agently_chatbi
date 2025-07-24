#!/usr/bin/env python3
"""
ChatBI 应用快速启动脚本
简化版本，直接启动 Web 服务
"""

import os
import sys

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def main():
    """快速启动函数"""
    print("🚀 启动 ChatBI 应用...")
    
    try:
        # 导入并启动主应用
        from main import main as app_main
        app_main()
    except KeyboardInterrupt:
        print("\n👋 ChatBI 应用已停止")
        sys.exit(0)
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 