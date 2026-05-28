import json
import os
import sys

# 將專案根目錄加入系統路徑，確保可以順利載入 app 模組
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

def import_words_to_db(json_filepath):
    """
    讀取 JSON 檔案，並透過 Flask 應用程式的設定 (包含 Atlas 連線) 將單字寫入資料庫
    """
    # 1. 繞過 Flask 啟動檢查，直接用 PyMongo 清除舊的、有衝突的索引
    from pymongo import MongoClient
    from dotenv import load_dotenv
    
    load_dotenv(os.path.join(parent_dir, '..', '.env'))
    mongo_uri = os.getenv("MONGO_URI")
    if mongo_uri:
        print("Step 1: Cleaning up old collections directly via PyMongo...")
        client = MongoClient(mongo_uri)
        db = client['test'] # 因為 MONGO_URI 沒指定名字，預設存在 test 資料庫
        db.words.drop()
        print("Old 'words' collection dropped successfully.")

    # 2. 確定資料庫乾淨後，再載入 Flask 與 MongoEngine
    from app import create_app
    from app.models.word import Word

    # 建立 Flask App 以載入 config.py 中的 Atlas 設定
    app = create_app()
    
    with app.app_context():
        print("Step 2: Connecting to MongoDB Atlas via Flask...")

        if not os.path.exists(json_filepath):
            print(f"Error: 找不到檔案 {json_filepath}")
            return
            
        print(f"Reading data from {json_filepath}...")
        with open(json_filepath, 'r', encoding='utf-8') as f:
            word_list = json.load(f)

        print("Formatting and importing words to Atlas...")
        words_to_insert = []
        for item in word_list:
            example_en = item.get('example_en', '')
            example_zh = item.get('example_zh', '')
            examples = [f"{example_en} ({example_zh})"] if example_en else []
            
            words_to_insert.append(Word(
                word_text=item.get('word'),
                definition=item.get('definition'),
                part_of_speech=item.get('type'),
                example_sentences=examples,
                difficulty_level=item.get('level', 'Unclassified')
            ))
        
        Word.objects.insert(words_to_insert)
        print(f"Success! {len(words_to_insert)} words have been imported to MongoDB Atlas.")

if __name__ == "__main__":
    json_path = os.path.join(current_dir, 'final_result.json')
    import_words_to_db(json_path)