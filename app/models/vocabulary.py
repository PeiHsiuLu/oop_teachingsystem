from mongoengine import DynamicDocument

# 為了相容 vocabulary_api.py 等舊有路由的匯入，在此提供 Word 模型。
# 優先嘗試從 app.models.word 載入，若該檔案不存在則自動動態建立相容模型。
try:
    from app.models.word import Word
except ImportError:
    class Word(DynamicDocument):
        """自動備用的 Word 模型，相容任何欄位"""
        meta = {'collection': 'words'}


class VocabularyBank(DynamicDocument):
    """
    為了解決 srs_manager 匯入錯誤而保留的 VocabularyBank。
    使用 DynamicDocument 確保即使不知道原始欄位也能正常載入並相容。
    """
    meta = {'collection': 'vocabulary_bank'}

class Vocabulary(DynamicDocument):
    """
    使用 DynamicDocument 可以動態接收來自 JSON 的各種欄位，
    不需要事先定義好所有 Schema，方便直接匯入 JSON 的結構。
    """
    meta = {'collection': 'vocabulary'}