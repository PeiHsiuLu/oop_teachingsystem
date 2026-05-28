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
    保留原有的單字，僅新增不存在的單字與詞性組合。
    """
    from app import create_app
    from app.models.word import Word

    # 建立 Flask App 以載入 config.py 中的 Atlas 設定
    app = create_app()
    
    with app.app_context():
        print("Connecting to MongoDB Atlas via Flask...")

        if not os.path.exists(json_filepath):
            print(f"Error: 找不到檔案 {json_filepath}")
            return
            
        print(f"Reading data from {json_filepath}...")
        with open(json_filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print("Formatting and importing words to Atlas...")
        
        # 取得目前資料庫中已有的 (單字, 詞性) 組合
        existing_entries = set(
            (w.word_text, w.part_of_speech) for w in Word.objects.only('word_text', 'part_of_speech')
        )
        
        words_to_insert = []
        for item in data:
            word_text = item.get('word')
            if not word_text: 
                continue
                
            entry_key = (word_text, item.get('type', ''))
            if entry_key in existing_entries:
                continue

            example_en = item.get('example_en', '')
            examples = [example_en] if example_en else []
            
            words_to_insert.append(Word(
                word_text=word_text,
                definition=item.get('definition'),
                part_of_speech=item.get('type'),
                example_sentences=examples,
                difficulty_level=item.get('level', 'Unclassified')
            ))
            existing_entries.add(entry_key)
        
        if words_to_insert:
            Word.objects.insert(words_to_insert)
            print(f"✅ 成功！已新增 {len(words_to_insert)} 筆單字進 MongoDB Atlas (已略過重複)。")
        else:
            print("✅ JSON 檔案中的單字皆已存在於資料庫中，無新增資料。")

if __name__ == "__main__":
    json_path = os.path.join(current_dir, 'final_result.json')
    import_words_to_db(json_path)