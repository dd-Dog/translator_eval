@echo off
REM 启动评估API服务器（Windows）

echo 启动翻译评估API服务器...
echo ================================

REM 检查conda环境
if "%CONDA_DEFAULT_ENV%"=="" (
    echo ⚠️  未检测到conda环境，建议使用: conda activate translator_eval
)

REM 启动服务器
python eval_server.py %*

