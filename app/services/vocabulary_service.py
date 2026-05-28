import json
from app.models.vocabulary import Vocabulary

class VocabularyService:
    def import_from_json(self, file_stream):
        """讀取上傳的 JSON 檔案，去除 id 後存入 MongoDB"""
        data = json.load(file_stream)
        
        if not isinstance(data, list):
            data = [data]  # 確保資料格式為 list

        imported_count = 0
        for item in data:
            if 'id' in item:
                del item['id']  # 移除 id 欄位
            
            # 將剩餘欄位存入 MongoDB
            vocab = Vocabulary(**item)
            vocab.save()
            imported_count += 1
            
        return imported_count

    def get_all_vocabulary(self):
        return Vocabulary.objects.all()