"""
Web 应用模块

包含 Flask Web 应用、API 接口、前端界面等
"""

from .app import create_app, socketio

__all__ = ['create_app', 'socketio'] 