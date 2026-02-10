"""
配置管理器 - 管理config.yml的读取、验证、热重载
"""

import os
import yaml
import time
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class ConfigChangeHandler(FileSystemEventHandler):
    """配置文件变更处理器"""
    
    def __init__(self, callback):
        self.callback = callback
    
    def on_modified(self, event):
        if event.src_path.endswith('config.yml'):
            self.callback()


class ConfigManager:
    """配置管理器（单例模式）"""
    
    _instance = None
    _config: Dict[str, Any] = {}
    _file_path: str = "./config.yml"
    _last_modified: float = 0
    _observer: Optional[Observer] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(self._file_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
                self._last_modified = os.path.getmtime(self._file_path)
                return self._config
        except FileNotFoundError:
            raise FileNotFoundError(f"配置文件不存在: {self._file_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"YAML解析错误: {e}")
    
    def reload_config(self) -> bool:
        """热重载配置"""
        try:
            current_mtime = os.path.getmtime(self._file_path)
            if current_mtime > self._last_modified:
                self.load_config()
                return True
            return False
        except Exception as e:
            print(f"配置重载失败: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项（支持点号路径）
        例如: get("ai-gateway.virtual_models.demo1.small.api_key")
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> bool:
        """设置配置项并保存到文件"""
        try:
            keys = key.split('.')
            config = self._config
            
            # 遍历到倒数第二层
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            
            # 设置值
            config[keys[-1]] = value
            
            # 保存到文件
            with open(self._file_path, 'w', encoding='utf-8') as f:
                yaml.dump(self._config, f, allow_unicode=True, sort_keys=False)
            
            return True
        except Exception as e:
            print(f"设置配置失败: {e}")
            return False
    
    def watch_config(self, callback=None):
        """监听配置文件变化"""
        if self._observer is None:
            handler = ConfigChangeHandler(callback or self.reload_config)
            self._observer = Observer()
            self._observer.schedule(
                handler, 
                path=os.path.dirname(self._file_path) or '.', 
                recursive=False
            )
            self._observer.start()
    
    def stop_watching(self):
        """停止监听"""
        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None
    
    @property
    def config(self) -> Dict[str, Any]:
        """获取完整配置"""
        return self._config
    
    def get_raw_yaml(self) -> str:
        """获取原始YAML内容"""
        try:
            with open(self._file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return ""
    
    def load_from_yaml(self, yaml_content: str) -> bool:
        """从YAML字符串加载配置"""
        try:
            self._config = yaml.safe_load(yaml_content)
            return True
        except yaml.YAMLError as e:
            print(f"YAML解析错误: {e}")
            return False
    
    def save_config(self) -> bool:
        """保存配置到文件"""
        try:
            with open(self._file_path, 'w', encoding='utf-8') as f:
                yaml.dump(self._config, f, allow_unicode=True, sort_keys=False)
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False


# 全局配置管理器实例
config_manager = ConfigManager()
