@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo  xo1997 画廊 - 打包脚本
echo ========================================
echo.

:: 检查虚拟环境
if not exist ".venv\Scripts\python.exe" (
    echo [错误] 未找到虚拟环境，请先运行: uv sync
    pause
    exit /b 1
)

:: 安装打包依赖
echo [1/3] 安装打包依赖...
uv sync --all-extras
if errorlevel 1 (
    echo [错误] 安装依赖失败
    pause
    exit /b 1
)

:: 清理旧的打包文件
echo [2/3] 清理旧的打包文件...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

:: 打包
echo [3/3] 开始打包...
.venv\Scripts\pyinstaller.exe build.spec --noconfirm
if errorlevel 1 (
    echo [错误] 打包失败
    pause
    exit /b 1
)

echo.
echo ========================================
echo  打包完成！
echo  输出目录: dist\xo1997-gallery\
echo ========================================
echo.
echo 使用说明：
echo 1. 将 dist\xo1997-gallery 文件夹复制给用户
echo 2. 用户首次运行需要创建 .env 文件配置 API Key
echo 3. 双击 xo1997-gallery.exe 启动应用
echo.

pause
