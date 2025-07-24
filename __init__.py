"""
ChatBI - 基于 Agently 框架的智能数据查询系统

一个将自然语言转换为 SQL 查询的 AI 应用，支持数据仓库查询和智能分析。

主要功能:
- 自然语言转 SQL
- 智能数据分析
- Web 界面和 API
- 多数据库支持
- 缓存优化
"""

__version__ = "1.0.0"
__author__ = "ChatBI Development Team"
__description__ = "基于 Agently 框架的智能数据查询系统"

# 导入主要模块
from config import Config

# 版本信息
VERSION_INFO = {
    "version": __version__,
    "description": __description__,
    "author": __author__,
    "agently_framework": "3.1.0+",
    "python_version": "3.8+"
} 