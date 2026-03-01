from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import subprocess
import zipfile
import urllib.request
from typing import List
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

server_state = {"status": 0} 

# 你的 app.py 所在的绝对路径
BASE_DIR = "/var/www/html/app/CorpLink-AI"
WORKSPACE_DIR = os.path.join(BASE_DIR, "temp_uploads")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return "<h1>CorpLink-AI バックエンドが起動しました！</h1>"

@app.get("/status")
async def get_status():
    return {"current_status": server_state["status"]}

@app.post("/upload")
async def upload_files(
    request: Request,
    file: UploadFile = File(...),
    openai_api_key: str = Form(...),       # 接收 API Key
    extract_mode: str = Form(...),         # 接收 数据源模式
    keyword_mode: str = Form(...),         # 接收 关键词模式
    custom_keywords: str = Form(""),       # 接收 自定义关键词（可选）
    db_mode: str = Form(...),              # 接收 数据库模式
    custom_db_url: str = Form("")          # 接收 自定义数据库URL（可选）
):
    if server_state["status"] != 0:
        raise HTTPException(status_code=400, detail="現在、別のタスクが処理中です。")
    
    server_state["status"] = 1
    
    try:
        # 1. 清理并重建沙盒目录
        if os.path.exists(WORKSPACE_DIR):
            shutil.rmtree(WORKSPACE_DIR)
        os.makedirs(WORKSPACE_DIR, exist_ok=True)

        # 2. 从 GitHub 下载整个 main 分支的 ZIP 包
        github_zip_url = "https://github.com/shiameyeung/CorpLink-AI/archive/refs/heads/main.zip"
        local_zip_path = os.path.join(WORKSPACE_DIR, "repo.zip")
        urllib.request.urlretrieve(github_zip_url, local_zip_path)

        # 解压 GitHub 仓库
        with zipfile.ZipFile(local_zip_path, 'r') as zip_ref:
            zip_ref.extractall(WORKSPACE_DIR)
        
        # 解压后会得到一个 'CorpLink-AI-main' 文件夹，把里面的东西全移到 WORKSPACE_DIR 根目录
        extracted_folder = os.path.join(WORKSPACE_DIR, "CorpLink-AI-main")
        for item in os.listdir(extracted_folder):
            shutil.move(os.path.join(extracted_folder, item), WORKSPACE_DIR)
        
        # 清理多余的压缩包和空文件夹
        shutil.rmtree(extracted_folder)
        os.remove(local_zip_path)

        # 3. 处理用户上传的文件
        filename = file.filename.lower()
        if filename.endswith('.zip'):
            # 如果是 zip，先保存为临时文件，再解压到当前工作目录，完美保留层级
            temp_upload_zip = os.path.join(WORKSPACE_DIR, "temp_upload.zip")
            with open(temp_upload_zip, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            with zipfile.ZipFile(temp_upload_zip, 'r') as zip_ref:
                zip_ref.extractall(WORKSPACE_DIR)
                
            os.remove(temp_upload_zip) # 解压后删除临时 zip 文件
            
        elif filename.endswith('.docx') or filename.endswith('.rtf'):
            # 如果是 docx 或 rtf，直接保存在沙盒根目录
            file_path = os.path.join(WORKSPACE_DIR, file.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        else:
            raise HTTPException(status_code=400, detail="サポートされていないファイル形式です。(.zip, .docx, .rtfのみ)")
        
        # 4. 运行 launcher.py 并捕获日志
        venv_python = os.path.join(BASE_DIR, "venv/bin/python")
        
        config_data = {
            "keyword_mode": keyword_mode,
            "extract_mode": extract_mode,
            "ai_level": "3",             # 强制全自动
            "overwrite_existing": "y",   # 强制继续
            "run_ai_autofill": "y",      # 强制AI清洗
            "confirm_standardize": "y"   # 强制不确认直接入库
        }
        
        # 处理自定义关键词 (如果用户选择了 2，则把逗号分隔的字符串转成列表)
        if keyword_mode == "2" and custom_keywords.strip():
            keys_list = [k.strip() for k in custom_keywords.replace("，", ",").split(",") if k.strip()]
            config_data["custom_keywords"] = keys_list

        # 处理自定义数据库 (保护默认地址不暴露给前端)
        if db_mode == "custom" and custom_db_url.strip():
            config_data["mysql_url"] = custom_db_url.strip()
        else:
            config_data["mysql_url"] = "mysql+pymysql://webapp:vE8#kZ9$nQ2!mP5@@127.0.0.1:3306/CorpLink?charset=utf8mb4"
        
        config_file_path = os.path.join(WORKSPACE_DIR, "config.json")
        with open(config_file_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, ensure_ascii=False, indent=4)
        
        # === B. 将 API Key 注入到安全的环境变量中运行 ===
        run_env = os.environ.copy()
        run_env["OPENAI_API_KEY"] = openai_api_key.strip()

        log_file_path = os.path.join(WORKSPACE_DIR, "run.log")
        
        with open(log_file_path, "w", encoding="utf-8") as log_file:
            process = subprocess.run(
                [venv_python, "launcher.py"], 
                cwd=WORKSPACE_DIR, 
                env=run_env,                 # 带着 API KEY 的环境变量去运行！
                stdout=log_file,             
                stderr=subprocess.STDOUT     
            )
            
        if process.returncode != 0:
            with open(log_file_path, "r", encoding="utf-8") as log_file:
                error_lines = log_file.readlines()[-15:]
            error_msg = "".join(error_lines)
            server_state["status"] = 0
            raise HTTPException(status_code=500, detail=f"実行エラー:\n{error_msg}")
        
        server_state["status"] = 2
        return {"message": "処理が完了しました！"}

    except Exception as e:
        server_state["status"] = 0
        raise HTTPException(status_code=500, detail=f"処理に失敗しました: {str(e)}")

@app.get("/download")
async def download_result():
    if server_state["status"] != 2:
        raise HTTPException(status_code=400, detail="処理が完了していません。")
    
    zip_path = os.path.join(BASE_DIR, "CorpLink_Result.zip")
    
    # 仅遍历 temp_uploads 目录下的所有 .csv 文件并打包
    csv_found = False
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(WORKSPACE_DIR):
            for file in files:
                if file.endswith('.csv'):
                    csv_found = True
                    abs_file_path = os.path.join(root, file)
                    rel_file_path = os.path.relpath(abs_file_path, WORKSPACE_DIR)
                    zipf.write(abs_file_path, rel_file_path)

    if not csv_found:
        raise HTTPException(status_code=404, detail="CSVファイルが見つかりませんでした。")

    return FileResponse(zip_path, media_type="application/zip", filename="CorpLink_Result.zip")

@app.post("/cleanup")
async def cleanup_task():
    if server_state["status"] == 1:
         raise HTTPException(status_code=400, detail="タスクが実行中です。")
    
    if os.path.exists(WORKSPACE_DIR):
        shutil.rmtree(WORKSPACE_DIR)
    
    zip_path = os.path.join(BASE_DIR, "CorpLink_Result.zip")
    if os.path.exists(zip_path):
        os.remove(zip_path)
            
    server_state["status"] = 0
    return {"message": "クリーンアップが完了しました。"}