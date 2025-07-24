#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Gradio ChatBI 启动脚本
"""

import sys
import os
from loguru import logger

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """启动 Gradio ChatBI 应用"""
    try:
        logger.info("正在启动 ChatBI Gradio 应用...")
        
        # 导入并运行应用
        from gradio_app import main as run_gradio_app
        run_gradio_app()
        
    except KeyboardInterrupt:
        logger.info("应用已停止")
    except Exception as e:
        logger.error(f"应用启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 