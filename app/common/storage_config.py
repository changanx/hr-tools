"""
存储配置管理模块
"""
import json
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, asdict

from PySide6.QtCore import QObject, Signal


@dataclass
class StorageConfig:
    """存储配置"""

    data_dir: str = ""
    """数据存储目录路径，为空则使用默认位置"""

    def to_dict(self) -> dict:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "StorageConfig":
        """从字典创建"""
        return cls(
            data_dir=data.get("data_dir", ""),
        )

    @property
    def effective_data_dir(self) -> Path:
        """获取有效的数据目录"""
        if self.data_dir:
            return Path(self.data_dir)
        return Path.home() / ".hr-tools" / "data"


class StorageConfigManager(QObject):
    """存储配置管理器"""

    # 配置变更信号
    config_changed = Signal(StorageConfig)

    # 需要重启应用信号
    restart_required = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._config_dir: Path = Path.home() / ".hr-tools" / "config"
        self._config_file: Path = self._config_dir / "storage.json"
        self._config: StorageConfig = StorageConfig()

        # 加载配置
        self._load_config()

    def _load_config(self) -> None:
        """从文件加载配置"""
        if self._config_file.exists():
            try:
                with open(self._config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._config = StorageConfig.from_dict(data)
            except Exception:
                # 加载失败，使用默认配置
                self._config = StorageConfig()

    def _save_config(self) -> None:
        """保存配置到文件"""
        self._config_dir.mkdir(parents=True, exist_ok=True)
        with open(self._config_file, "w", encoding="utf-8") as f:
            json.dump(self._config.to_dict(), f, indent=2, ensure_ascii=False)

    def get_config(self) -> StorageConfig:
        """获取当前配置"""
        return self._config

    def set_data_dir(self, path: str) -> None:
        """
        设置数据存储目录

        Args:
            path: 目录路径，为空则使用默认位置
        """
        old_dir = self._config.effective_data_dir
        self._config.data_dir = path
        self._save_config()
        self.config_changed.emit(self._config)

        # 如果路径改变，需要重启应用
        new_dir = self._config.effective_data_dir
        if old_dir != new_dir:
            self.restart_required.emit()

    def get_database_path(self) -> Path:
        """获取数据库文件路径"""
        return self._config.effective_data_dir / "hr-tools.db"

    def ensure_data_dir(self) -> Path:
        """确保数据目录存在"""
        data_dir = self._config.effective_data_dir
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir


# 全局存储配置管理器实例
storage_config_manager = StorageConfigManager()
