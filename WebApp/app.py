from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import subprocess
import zipfile
import urllib.request
import json
import logging
import traceback
# --- 在顶部补充引入包 ---
import pandas as pd
from openai import OpenAI
import math
# ---------------------

# 新增一个专门用于存放过滤结果的文件夹
FILTER_WORKSPACE_DIR = os.path.join(BASE_DIR, "filter_workspace")
os.makedirs(FILTER_WORKSPACE_DIR, exist_ok=True)

# 行业字典
INDUSTRY_DICT = {
    1: "金融・投資機関",
    2: "政府・公共機関",
    3: "ニュース・PRメディア",
    4: "教育・研究機関",
    5: "医療・ライフサイエンス",
    6: "総合商社・大手",
    7: "IT・ネット・通信",
    8: "製造業・メーカー",
    9: "小売・サービス・インフラ",
    10: "その他・分類不能"
}

@app.post("/filter_process")
async def process_matrix_filter(
    file: UploadFile = File(...),
    openai_api_key: str = Form(...),
    exclude_industries: str = Form(...) # 逗号分隔的字符串，例如 "2,3,4"
):
    try:
        # 1. 保存用户上传的 pivot_table
        file_path = os.path.join(FILTER_WORKSPACE_DIR, "pivot_table_uploaded.csv")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 2. 读取 CSV，获取第一行（表头）的组织名
        # index_col=0 表示第一列是行索引
        df = pd.read_csv(file_path, index_col=0)
        org_names = list(df.columns)
        
        # 3. 准备调用 OpenAI 进行批量分类
        client = OpenAI(api_key=openai_api_key)
        exclude_list = [int(x) for x in exclude_industries.split(",")]
        
        # 为了避免超大 Token，这里我们采用简单的批处理（每批 100 个）
        batch_size = 100
        classification_result = {}
        
        for i in range(0, len(org_names), batch_size):
            batch_orgs = org_names[i:i+batch_size]
            prompt = f"""
            You are a business taxonomy expert. 
            Assign each of the following organization names to one of the industry IDs (1 to 10).
            [Categories]
            1: Finance & Investment
            2: Gov & Public Sector
            3: News & PR Media
            4: Education & Research
            5: Healthcare & Life Sciences
            6: Conglomerate / General
            7: IT & Telecom
            8: Manufacturing
            9: Retail, Services & Infra
            10: Other

            Return ONLY a valid JSON object where keys are the exact organization names and values are the integer ID.
            Organizations to classify: {batch_orgs}
            """
            
            response = client.chat.completions.create(
                model="gpt-4o-mini", # 使用 4o-mini 足够便宜且快
                response_format={ "type": "json_object" },
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0
            )
            
            batch_json = json.loads(response.choices[0].message.content)
            classification_result.update(batch_json)
            
        # 4. 构建 organization_list.csv (含判断结果)
        org_list_data = []
        orgs_to_drop = []
        
        for org in org_names:
            ind_id = classification_result.get(org, 10) # 默认10
            ind_name = INDUSTRY_DICT.get(ind_id, "不明")
            status = "排除" if ind_id in exclude_list else "保留"
            
            if status == "排除":
                orgs_to_drop.append(org)
                
            org_list_data.append({
                "Organization": org,
                "Industry_ID": ind_id,
                "Industry_Name": ind_name,
                "Status": status
            })
            
        df_orgs = pd.DataFrame(org_list_data)
        df_orgs.to_csv(os.path.join(FILTER_WORKSPACE_DIR, "organization_list.csv"), index=False, encoding='utf-8-sig')
        
        # 5. Pandas 核心操作：矩阵裁剪
        # 只要行名或列名在排除列表里，一并删去
        # 注意：需要确保要 drop 的项目确实存在于 df 的 index 和 columns 中
        valid_drop_cols = [col for col in orgs_to_drop if col in df.columns]
        valid_drop_rows = [row for row in orgs_to_drop if row in df.index]
        
        df_filtered = df.drop(columns=valid_drop_cols)
        df_filtered = df_filtered.drop(index=valid_drop_rows)
        
        # 保存裁剪后的矩阵
        df_filtered.to_csv(os.path.join(FILTER_WORKSPACE_DIR, "pivot_table_filtered.csv"), encoding='utf-8-sig')
        
        return {"message": f"成功！全 {len(org_names)} 組織中、{len(orgs_to_drop)} 組織を除外しました。"}

    except Exception as e:
        logger.error(f"Filter Process Error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download_filter_result")
async def download_filter_result():
    zip_path = os.path.join(BASE_DIR, "CorpLink_Filtered_Result.zip")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        org_csv = os.path.join(FILTER_WORKSPACE_DIR, "organization_list.csv")
        piv_csv = os.path.join(FILTER_WORKSPACE_DIR, "pivot_table_filtered.csv")
        if os.path.exists(org_csv):
            zipf.write(org_csv, "organization_list.csv")
        if os.path.exists(piv_csv):
            zipf.write(piv_csv, "pivot_table_filtered.csv")
            
    return FileResponse(zip_path, media_type="application/zip", filename="CorpLink_Filtered_Result.zip")

# === 设置带时间戳的后端日志 ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

server_state = {"status": 0} 
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
    openai_api_key: str = Form(...),       
    extract_mode: str = Form(...),         
    keyword_mode: str = Form(...),         
    custom_keywords: str = Form(""),       
    db_mode: str = Form(...),              
    custom_db_url: str = Form("")          
):
    logger.info(f"=== 新しいタスクを受信しました: ファイル名 {file.filename} ===")
    logger.info(f"パラメータ: extract_mode={extract_mode}, keyword_mode={keyword_mode}, db_mode={db_mode}")
    
    if server_state["status"] != 0:
        logger.warning("タスク拒否: 別のタスクが実行中です")
        raise HTTPException(status_code=400, detail="現在、別のタスクが処理中です。")
    
    server_state["status"] = 1
    
    try:
        # 1. 清理并重建沙盒目录
        logger.info("環境と最新コードを準備中...")
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
        logger.info("ユーザーファイルの配置中...")
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
        
        logger.info("設定ファイルを生成中...")
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

       # 将特殊符号进行了转义: # -> %23, $ -> %24, ! -> %21, @ -> %40
        if db_mode == "custom" and custom_db_url.strip():
            config_data["mysql_url"] = custom_db_url.strip()
        else:
            # 修改这里：使用 URL 编码后的密码
            config_data["mysql_url"] = "mysql+pymysql://webapp:vE8%23kZ9%24nQ2%21mP5%40@127.0.0.1:3306/CorpLink?charset=utf8mb4"
        
        config_file_path = os.path.join(WORKSPACE_DIR, "config.json")
        with open(config_file_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, ensure_ascii=False, indent=4)
        
        # === B. 将 API Key 注入到安全的环境变量中运行 ===
        venv_python = os.path.join(BASE_DIR, "venv/bin/python")
        run_env = os.environ.copy()
        run_env["OPENAI_API_KEY"] = openai_api_key.strip()
        
        run_env["PYTHONUNBUFFERED"] = "1"

        log_file_path = os.path.join(WORKSPACE_DIR, "run.log")
        logger.info("サブプロセス (launcher.py) の実行を開始します...")
        
        with open(log_file_path, "w", encoding="utf-8") as log_file:
            process = subprocess.run(
                [venv_python, "-u", "launcher.py"],  # <--- 这里加上 "-u"
                cwd=WORKSPACE_DIR,
                env=run_env,                 
                stdout=log_file,             
                stderr=subprocess.STDOUT     
            )
            
        if process.returncode != 0:
            logger.error(f"launcher.py がエラーコード {process.returncode} で終了しました。")
            with open(log_file_path, "r", encoding="utf-8") as log_file:
                error_lines = log_file.readlines()[-15:]
            error_msg = "".join(error_lines)
            server_state["status"] = 0
            raise HTTPException(status_code=500, detail=f"実行エラー:\n{error_msg}")
        
        logger.info("=== タスクが正常に完了しました ===")
        server_state["status"] = 2
        return {"message": "処理が完了しました！"}

    except HTTPException as he:
        raise he
    except Exception as e:
        # 打印出精准的堆栈报错信息到后台
        logger.error("予期せぬエラーが発生しました:\n" + traceback.format_exc())
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