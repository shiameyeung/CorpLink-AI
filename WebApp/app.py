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
    files: List[UploadFile] = File(...),
    paths: str = Form(...) 
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

        # 3. 解析前端传来的路径列表，将用户文件存入沙盒（与代码同级）
        path_list = json.loads(paths)
        for i, file in enumerate(files):
            safe_rel_path = path_list[i].lstrip("/") 
            file_path = os.path.join(WORKSPACE_DIR, safe_rel_path)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        
        # 4. 运行 launcher.py
        # 假设你的虚拟环境直接建在 /var/www/html/app/CorpLink-AI/venv
        venv_python = os.path.join(BASE_DIR, "venv/bin/python")
        
        # 在沙盒目录中自动生成 config.json 供代码读取
        # 你未来可以在前端网页加上复选框，把这些值作为参数传过来。现在先写死一套默认的高效配置：
        config_data = {
            "overwrite_existing": "y",
            "run_ai_autofill": "y",
            "confirm_standardize": "y"
            # 如果你有数据库地址或者 API Key 也可以写在这里
        }
        
        config_file_path = os.path.join(WORKSPACE_DIR, "config.json")
        with open(config_file_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, ensure_ascii=False, indent=4)
        
        # 使用 subprocess 运行，工作目录设为 WORKSPACE_DIR
        subprocess.run([venv_python, "launcher.py"], cwd=WORKSPACE_DIR, check=True)
        
        server_state["status"] = 2
        return {"message": "処理が完了しました！"}

    except subprocess.CalledProcessError as e:
        server_state["status"] = 0
        raise HTTPException(status_code=500, detail="スクリプトの実行中にエラーが発生しました。")
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