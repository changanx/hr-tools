# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置

使用方法：
    pyinstaller build.spec

输出目录：dist/xo1997-gallery/
"""

import sys
import os
from pathlib import Path

block_cipher = None

# 获取项目根目录（spec 文件所在目录）
project_root = Path(SPECPATH)

# 获取虚拟环境中 PySide6 的路径
pyside6_path = project_root / ".venv" / "Lib" / "site-packages" / "PySide6"

# 如果虚拟环境不存在，尝试从当前 Python 环境获取
if not pyside6_path.exists():
    import PySide6
    pyside6_path = Path(PySide6.__file__).parent

# 收集 PySide6 插件
qt_plugins = [
    'platforms',
    'platformthemes',
    'styles',
    'imageformats',
    'iconengines',
]

binaries = []
for plugin in qt_plugins:
    plugin_path = pyside6_path / "plugins" / plugin
    if plugin_path.exists():
        binaries.append((str(plugin_path), f'PySide6/plugins/{plugin}'))

# 收集 PySide6 动态库
dll_files = [
    'Qt6Core.dll',
    'Qt6Gui.dll',
    'Qt6Widgets.dll',
    'Qt6Svg.dll',
    'Qt6Xml.dll',
    'Qt6Network.dll',
    'Qt6Sql.dll',
]
for dll in dll_files:
    dll_path = pyside6_path / dll
    if dll_path.exists():
        binaries.append((str(dll_path), 'PySide6'))

a = Analysis(
    ['app/main.py'],
    pathex=[],
    binaries=binaries,
    datas=[
        # 包含 .env.example 作为模板
        ('.env.example', '.'),
        # 包含模板文件
        ('data/templates', 'data/templates'),
    ],
    hiddenimports=[
        'app',
        'app.main',
        'app.ui',
        'app.ui._rc.resource',
        'app.view',
        'app.view.main_window',
        'app.view.ai_chat_interface',
        'app.view.ai_settings_interface',
        'app.view.general_settings_interface',
        'app.view.group_chat_interface',
        'app.view.excel_ppt_interface',
        'app.components',
        'app.common',
        'core',
        'core.model_manager',
        'core.excel_processor',
        'core.ppt_generator',
        'core.group_chat_manager',
        'core.tools',
        'data',
        'data.database',
        'data.models',
        'data.repositories',
        # LangChain 相关
        'langchain_openai',
        'langchain_anthropic',
        'langchain_ollama',
        'langchain_core',
        # 其他依赖
        'darkdetect',
        'pandas',
        'openpyxl',
        'pptx',
        'dotenv',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy.f2py',
        'IPython',
        'jupyter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='xo1997-gallery',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 可以添加图标：icon='assets/icon.ico'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='xo1997-gallery',
)
