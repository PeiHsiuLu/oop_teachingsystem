import json
import os
from mongoengine import StringField 
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, render_template_string
from flask_login import login_required, current_user # Assuming current_user is available
from functools import wraps # Import wraps
from app.services.word_service import WordService
from app.services.auth_service import AuthService # To validate admin role
from app.models.word import Word

word_bp = Blueprint('word', __name__)
word_service = WordService()
auth_service = AuthService() # For role validation

# Helper decorator to ensure the user is an admin
def admin_required(f):
    @wraps(f) # Use functools.wraps to preserve function metadata
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role != 'admin':
            return jsonify({"message": "Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated_function

# --- Admin Endpoints for Words ---
@word_bp.route('/admin/words/manage', methods=['GET', 'POST'])
@admin_required
def manage_words():
    """Admin: Displays a page to manage words (list and add)."""

    if request.method == 'POST':
        # Handle form submission for adding a new word
        word_text = request.form.get('word_text', '').strip()
        definition = request.form.get('definition', '').strip()
        part_of_speech = request.form.get('part_of_speech')
        example_sentences_str = request.form.get('example_sentences', '').strip()
        difficulty_level = request.form.get('difficulty_level', 'Unclassified')

        # --- 後端驗證機制 ---
        import re
        # 1. 驗證單字是否為英文
        if not re.match(r'^[a-zA-Z\- ]+$', word_text):
            flash("單字欄位僅能包含英文字母、橫線或空格。", "error")
            return redirect(url_for('word.manage_words'))

        # 2. 驗證定義是否包含中文
        if not re.search(r'[\u4e00-\u9fa5]', definition):
            flash("中文定義欄位必須包含中文字元。", "error")
            return redirect(url_for('word.manage_words'))
            
        # 2-1. 驗證定義是否包含奇怪的特殊符號 (僅允許中英數與基本標點)
        if not re.match(r'^[\u4e00-\u9fa5a-zA-Z0-9\s，。！？、；：「」『』（）\(\)\[\]"\'\.,\-]+$', definition):
            flash("中文定義欄位包含不允許的特殊符號。", "error")
            return redirect(url_for('word.manage_words'))

        # 3. 驗證例句格式與是否包含單字
        if example_sentences_str:
            # 限制只能是英文、數字、空白與常見標點符號
            if not re.match(r'^[a-zA-Z0-9\s.,:;!?\'"\(\)\-\$%]+$', example_sentences_str):
                flash("英文例句欄位僅能包含英文、數字與基本標點符號 (如 6:00)。", "error")
                return redirect(url_for('word.manage_words'))
            if word_text.lower() not in example_sentences_str.lower():
                flash(f"英文例句中必須包含單字 '{word_text}'。", "error")
                return redirect(url_for('word.manage_words'))
        # --- 驗證結束 ---

        example_sentences = [s.strip() for s in example_sentences_str.split(';') if s.strip()] if example_sentences_str else []

        try:
            word_service.add_word(
                word_text=word_text,
                definition=definition,
                part_of_speech=part_of_speech,
                example_sentences=example_sentences,
                difficulty_level=difficulty_level
            )
            flash(f"Word '{word_text}' added successfully!", "success")
        except ValueError as e:
            flash(str(e), "error")
        except Exception as e:
            flash(f"An error occurred: {e}", "error")
        
        return redirect(url_for('word.manage_words')) # Redirect to refresh the page

    # 搜尋與分頁邏輯
    search_query = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    if search_query:
        query_set = Word.objects(word_text__icontains=search_query)
    else:
        query_set = Word.objects
        
    total_words = query_set.count()
    total_pages = (total_words + per_page - 1) // per_page
    if total_pages == 0: total_pages = 1
    
    skip = (page - 1) * per_page
    words = query_set.skip(skip).limit(per_page)
    
    html_template = """
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <title>管理單字庫</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; background-color: #f4f7f6; color: #333; }
            .form-container { background: #fff; padding: 25px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 30px; border-top: 5px solid #0277bd; }
            .form-group { margin-bottom: 15px; }
            .form-group label { display: block; font-weight: bold; margin-bottom: 5px; color: #555; }
            .form-group input, .form-group select { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
            .btn { background-color: #0277bd; color: white; padding: 10px 20px; font-size: 1.1em; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; }
            .btn:hover { background-color: #01579b; }
            table { width: 100%; border-collapse: collapse; background: #fff; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
            th, td { padding: 12px; border: 1px solid #e0e0e0; text-align: left; }
            th { background-color: #0277bd; color: white; }
            .flash-messages { color: #d32f2f; font-weight: bold; margin-bottom: 15px; background: #ffcdd2; padding: 10px; border-radius: 4px;}
            .search-form { margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center;}
            .search-form input[type="text"] { padding: 10px; font-size: 1em; width: 250px; border: 1px solid #ccc; border-radius: 4px; }
            .search-form button { padding: 10px 15px; font-size: 1em; background-color: #0277bd; color: white; border: none; border-radius: 4px; cursor: pointer; }
            .search-form .clear-btn { padding: 9px 15px; text-decoration: none; background-color: #e0e0e0; color: #333; border-radius: 4px; margin-left: 5px; }
            .pagination { margin-top: 30px; text-align: center; font-size: 1.2em; padding-bottom: 50px; }
            .pagination a { padding: 8px 15px; background: #0277bd; color: white; text-decoration: none; border-radius: 4px; margin: 0 5px; }
            /* 編輯 Modal 樣式 */
            .modal { display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.5); }
            .modal-content { background-color: #fff; margin: 5% auto; padding: 25px; border-radius: 8px; width: 80%; max-width: 800px; border-top: 5px solid #f57c00; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
            .close { color: #aaa; float: right; font-size: 28px; font-weight: bold; cursor: pointer; }
            .close:hover { color: black; }
        </style>
    </head>
    <body>
        <a href="{{ url_for('dashboard.index') }}" style="text-decoration: none; color: #0277bd; font-weight: bold;">⬅️ 回到儀表板 (Back to Dashboard)</a>
        <h1 style="color: #0277bd;">⚙️ 管理單字庫 (Admin)</h1>
        
        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            <div class="flash-messages">
              {% for category, message in messages %}
                <p style="margin:0;">{{ message }}</p>
              {% endfor %}
            </div>
          {% endif %}
        {% endwith %}

        <div class="form-container">
            <h3 style="margin-top:0;">➕ 新增單字</h3>
            <form method="POST" action="{{ url_for('word.manage_words') }}">
                <div style="display: flex; gap: 15px;">
                    <div class="form-group" style="flex: 1;"><label>單字 (Word):</label><input type="text" name="word_text" required></div>
                    <div class="form-group" style="flex: 2;"><label>中文定義 (Definition):</label><input type="text" name="definition" required></div>
                </div>
                <div style="display: flex; gap: 15px;">
                    <div class="form-group" style="flex: 1;">
                        <label>詞性 (Part of Speech):</label>
                        <select name="part_of_speech">
                            <option value="noun">noun (名詞)</option>
                            <option value="verb">verb (動詞)</option>
                            <option value="auxiliary verb">auxiliary verb (助動詞)</option>
                            <option value="modal verb">modal verb (情態動詞)</option>
                            <option value="adjective">adjective (形容詞)</option>
                            <option value="adverb">adverb (副詞)</option>
                            <option value="preposition">preposition (介系詞)</option>
                            <option value="conjunction">conjunction (連接詞)</option>
                            <option value="pronoun">pronoun (代名詞)</option>
                            <option value="determiner">determiner (限定詞)</option>
                            <option value="indefinite article">indefinite article (不定冠詞)</option>
                            <option value="definite article">definite article (定冠詞)</option>
                            <option value="exclamation">exclamation (感嘆詞)</option>
                            <option value="number">number (數詞)</option>
                            <option value="other">other (其他)</option>
                        </select>
                    </div>
                    <div class="form-group" style="flex: 2;"><label>英文例句 (Example Sentences):</label><input type="text" name="example_sentences"></div>
                    <div class="form-group" style="flex: 1;">
                        <label>難度 (CEFR):</label>
                        <select name="difficulty_level">
                            <option value="A1">A1</option>
                            <option value="A2">A2</option>
                            <option value="B1">B1</option>
                            <option value="B2">B2</option>
                            <option value="C1">C1</option>
                            <option value="C2">C2</option>
                            <option value="Unclassified">Unclassified</option>
                        </select>
                    </div>
                </div>
                <button type="submit" class="btn">新增單字 (Add Word)</button>
            </form>
        </div>

        <div style="display: flex; justify-content: space-between; align-items: flex-end;">
            <h3>📋 系統單字列表 (Total: {{ total_words }})</h3>
            <div class="search-form">
                <form method="GET" action="{{ url_for('word.manage_words') }}">
                    <input type="text" name="search" placeholder="搜尋單字..." value="{{ search }}">
                    <button type="submit">搜尋</button>
                    <a href="{{ url_for('word.manage_words') }}" class="clear-btn">清除</a>
                </form>
            </div>
        </div>
        
        {% if total_words > 0 %}
        <table>
            <tr><th>單字</th><th>定義</th><th>詞性</th><th>難度</th><th>英文例句</th><th>操作</th></tr>
            {% for w in words %}
            <tr>
                <td><strong>{{ w.word_text }}</strong></td>
                <td>{{ w.definition }}</td>
                <td>{{ w.part_of_speech }}</td>
                <td>{{ w.difficulty_level }}</td>
                <td><em style="color: #555;">{{ w.example_sentences[0] if w.example_sentences else '無' }}</em></td>
                <td>
                    <div style="display: flex; gap: 12px;">
                        <button data-id="{{ w.id }}" data-word="{{ w.word_text }}" data-def="{{ w.definition }}" data-pos="{{ w.part_of_speech }}" data-diff="{{ w.difficulty_level }}" data-ex="{{ w.example_sentences[0] if w.example_sentences else '' }}" onclick="openEditModal(this)" style="background: #f57c00; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor:pointer;">編輯</button>
                        <button onclick="deleteWord('{{ w.id }}')" style="background: #d32f2f; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor:pointer;">刪除</button>
                    </div>
                </td>
            </tr>
            {% endfor %}
        </table>
        {% else %}
        <div style="text-align: center; padding: 40px; background: #fff; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-top: 20px;">
            <h3 style="color: #666; margin: 0;">{% if search %}找不到符合條件的單字。{% else %}目前尚未有任何單字在資料庫內{% endif %}</h3>
        </div>
        {% endif %}
        
        <!-- 編輯單字 Modal -->
        <div id="editModal" class="modal">
            <div class="modal-content">
                <span class="close" onclick="closeEditModal()">&times;</span>
                <h3 style="margin-top:0; color: #f57c00;">✏️ 編輯單字</h3>
                <input type="hidden" id="edit_id">
                <div style="display: flex; gap: 15px; margin-bottom: 15px;">
                    <div class="form-group" style="flex: 1;"><label>單字 (Word):</label><input type="text" id="edit_word_text" required></div>
                    <div class="form-group" style="flex: 2;"><label>中文定義 (Definition):</label><input type="text" id="edit_definition" required></div>
                </div>
                <div style="display: flex; gap: 15px; margin-bottom: 15px;">
                    <div class="form-group" style="flex: 1;">
                        <label>詞性 (Part of Speech):</label>
                        <select id="edit_part_of_speech">
                            <option value="noun">noun (名詞)</option>
                            <option value="verb">verb (動詞)</option>
                            <option value="auxiliary verb">auxiliary verb (助動詞)</option>
                            <option value="modal verb">modal verb (情態動詞)</option>
                            <option value="adjective">adjective (形容詞)</option>
                            <option value="adverb">adverb (副詞)</option>
                            <option value="preposition">preposition (介系詞)</option>
                            <option value="conjunction">conjunction (連接詞)</option>
                            <option value="pronoun">pronoun (代名詞)</option>
                            <option value="determiner">determiner (限定詞)</option>
                            <option value="indefinite article">indefinite article (不定冠詞)</option>
                            <option value="definite article">definite article (定冠詞)</option>
                            <option value="exclamation">exclamation (感嘆詞)</option>
                            <option value="number">number (數詞)</option>
                            <option value="other">other (其他)</option>
                        </select>
                    </div>
                    <div class="form-group" style="flex: 2;"><label>英文例句 (Example Sentences):</label><input type="text" id="edit_example_sentences"></div>
                    <div class="form-group" style="flex: 1;">
                        <label>難度 (CEFR):</label>
                        <select id="edit_difficulty_level">
                            <option value="A1">A1</option>
                            <option value="A2">A2</option>
                            <option value="B1">B1</option>
                            <option value="B2">B2</option>
                            <option value="C1">C1</option>
                            <option value="C2">C2</option>
                            <option value="Unclassified">Unclassified</option>
                        </select>
                    </div>
                </div>
                <button onclick="submitEdit()" class="btn" style="background-color: #f57c00;">更新單字 (Update Word)</button>
            </div>
        </div>

        <div class="pagination">
            {% if page > 1 %}<a href="{{ url_for('word.manage_words', page=page-1, search=search) }}">⬅️ 上一頁</a>{% endif %}
            <span style="margin: 0 15px;"> 第 {{ page }} 頁 / 共 {{ total_pages }} 頁 </span>
            {% if page < total_pages %}<a href="{{ url_for('word.manage_words', page=page+1, search=search) }}">下一頁 ➡️</a>{% endif %}
            <form method="GET" action="{{ url_for('word.manage_words') }}" style="display: inline-block; margin-left: 20px;">
                {% if search %}<input type="hidden" name="search" value="{{ search }}">{% endif %}
                跳至第 <input type="number" name="page" min="1" max="{{ total_pages }}" value="{{ page }}" style="width: 60px; padding: 5px; text-align: center; border: 1px solid #ccc; border-radius: 4px;"> 頁
                <button type="submit" style="padding: 5px 15px; font-size: 0.9em; background-color: #0277bd; color: white; border: none; border-radius: 4px; cursor: pointer;">跳轉</button>
            </form>
        </div>
        <script>
            function deleteWord(id) {
                if(confirm("確定要刪除這個單字嗎？")) {
                    fetch('/word/admin/words/' + id, { method: 'DELETE' })
                        .then(response => response.json())
                        .then(data => {
                            alert(data.message);
                            location.reload();
                        });
                }
            }

            function openEditModal(btn) {
                document.getElementById('edit_id').value = btn.getAttribute('data-id');
                document.getElementById('edit_word_text').value = btn.getAttribute('data-word');
                document.getElementById('edit_definition').value = btn.getAttribute('data-def');
                document.getElementById('edit_part_of_speech').value = btn.getAttribute('data-pos');
                document.getElementById('edit_difficulty_level').value = btn.getAttribute('data-diff');
                document.getElementById('edit_example_sentences').value = btn.getAttribute('data-ex');
                document.getElementById('editModal').style.display = "block";
            }

            function closeEditModal() {
                document.getElementById('editModal').style.display = "none";
            }

            // 點擊 Modal 外部關閉
            window.onclick = function(event) {
                if (event.target == document.getElementById('editModal')) {
                    closeEditModal();
                }
            }

            function submitEdit() {
                const id = document.getElementById('edit_id').value;
                const wordInput = document.getElementById('edit_word_text').value.trim();
                const definitionInput = document.getElementById('edit_definition').value.trim();
                const posInput = document.getElementById('edit_part_of_speech').value;
                const diffInput = document.getElementById('edit_difficulty_level').value;
                const exampleInput = document.getElementById('edit_example_sentences').value.trim();

                const englishRegex = /^[a-zA-Z\- ]+$/;
                const chineseRegex = /[\u4e00-\u9fa5]/;
                const definitionFormatRegex = /^[\u4e00-\u9fa5a-zA-Z0-9\s，。！？、；：「」『』（）\(\)\[\]"\'\.,\-]+$/;
                const exampleFormatRegex = /^[a-zA-Z0-9\s.,:;!?\'"\(\)\-\$%]+$/;

                if (!englishRegex.test(wordInput)) {
                    alert('「單字」欄位僅能輸入英文字母。');
                    return;
                } else if (!chineseRegex.test(definitionInput)) {
                    alert('「中文定義」欄位必須包含中文字。');
                    return;
                } else if (!definitionFormatRegex.test(definitionInput)) {
                    alert('「中文定義」欄位包含不允許的特殊符號。');
                    return;
                } else if (exampleInput) {
                    if (!exampleFormatRegex.test(exampleInput)) {
                        alert('「英文例句」欄位僅能包含英文、數字與基本標點符號 (如 6:00)。');
                        return;
                    } else if (wordInput && !exampleInput.toLowerCase().includes(wordInput.toLowerCase())) {
                        alert('「英文例句」中必須包含您正在編輯的單字。');
                        return;
                    }
                }

                const data = {
                    word_text: wordInput,
                    definition: definitionInput,
                    part_of_speech: posInput,
                    difficulty_level: diffInput,
                    example_sentences: exampleInput ? [exampleInput] : []
                };

                fetch('/word/admin/words/' + id, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                })
                .then(response => response.json())
                .then(data => {
                    if(data.message === "Word updated successfully") {
                        alert("更新成功！");
                        location.reload();
                    } else {
                        alert("更新失敗：" + (data.error || data.message));
                    }
                })
                .catch(err => {
                    console.error(err);
                    alert("發生錯誤，請稍後再試。");
                });
            }

            // 前端即時驗證
            document.querySelector('form[action="{{ url_for('word.manage_words') }}"]').addEventListener('submit', function(event) {
                let isValid = true;
                const wordInput = document.querySelector('input[name="word_text"]');
                const definitionInput = document.querySelector('input[name="definition"]');
                const exampleInput = document.querySelector('input[name="example_sentences"]');
                
                const englishRegex = /^[a-zA-Z\- ]+$/;
                const chineseRegex = /[\u4e00-\u9fa5]/;
                const definitionFormatRegex = /^[\u4e00-\u9fa5a-zA-Z0-9\s，。！？、；：「」『』（）\(\)\[\]"\'\.,\-]+$/;
                const exampleFormatRegex = /^[a-zA-Z0-9\s.,:;!?\'"\(\)\-\$%]+$/;

                if (!englishRegex.test(wordInput.value.trim())) {
                    alert('「單字」欄位僅能輸入英文字母。');
                    isValid = false;
                } else if (!chineseRegex.test(definitionInput.value)) {
                    alert('「中文定義」欄位必須包含中文字。');
                    isValid = false;
                } else if (!definitionFormatRegex.test(definitionInput.value)) {
                    alert('「中文定義」欄位包含不允許的特殊符號。');
                    isValid = false;
                } else if (exampleInput.value) {
                    if (!exampleFormatRegex.test(exampleInput.value)) {
                        alert('「英文例句」欄位僅能包含英文、數字與基本標點符號 (如 6:00)。');
                        isValid = false;
                    } else if (wordInput.value.trim() && !exampleInput.value.toLowerCase().includes(wordInput.value.trim().toLowerCase())) {
                        alert('「英文例句」中必須包含您正在新增的單字。');
                        isValid = false;
                    }
                }

                if (!isValid) {
                    event.preventDefault(); // 如果驗證失敗，則停止表單提交
                }
            });
        </script>
    </body>
    </html>
    """
    return render_template_string(html_template, words=words, total_words=total_words, page=page, total_pages=total_pages, search=search_query)

@word_bp.route('/admin/words/import-local', methods=['POST'])
@admin_required
def import_local_json():
    """Admin: 直接讀取專案內的 final_result.json 單字資料"""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(current_dir, '..', 'final_result.json')
        
        if not os.path.exists(json_path):
            flash(f"找不到檔案：{json_path}", "error")
            return redirect(url_for('word.manage_words'))
            
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        words_to_insert = []
        
        for item in data:
            if not item.get('word'):
                continue
            diff_level = item.get('level', 'Unclassified')
            
            example_en = item.get('example_en', '')
            examples = [example_en] if example_en else [] # 依需求僅儲存英文例句

            words_to_insert.append(Word(
                word_text=item.get('word'),
                definition=item.get('definition', ''),
                part_of_speech=item.get('type', ''),
                example_sentences=examples,
                difficulty_level=diff_level
            ))
        
        if words_to_insert:
            Word.objects.insert(words_to_insert) # 批次寫入資料庫
            flash(f"成功從本機匯入 {len(words_to_insert)} 筆單字！", "success")
        else:
            flash("JSON 檔案中沒有有效的單字。", "error")
    except Exception as e:
        flash(f"匯入失敗：{str(e)}", "error")
        
    return redirect(url_for('word.manage_words'))

@word_bp.route('/admin/words/import', methods=['POST'])
@admin_required
def import_json():
    """Admin: 匯入 final_result.json 單字資料"""
    if 'file' not in request.files:
        flash("沒有選擇檔案！", "error")
        return redirect(url_for('word.manage_words'))
        
    file = request.files['file']
    if file.filename == '':
        flash("未選擇檔案！", "error")
        return redirect(url_for('word.manage_words'))
        
    if file and file.filename.endswith('.json'):
        try:
            # 強制使用 utf-8 解碼讀取，避免舊版 Flask 的 file object 造成 JSON 解析錯誤
            data = json.loads(file.read().decode('utf-8'))
            words_to_insert = []
            
            for item in data:
                # 略過 id / new_id，僅讀取有用的資訊
                if not item.get('word'):
                    continue
                diff_level = item.get('level', 'Unclassified')
                
                # 僅讀取英文例句
                example_en = item.get('example_en', '')
                examples = [example_en] if example_en else []

                words_to_insert.append(Word(
                    word_text=item.get('word'),
                    definition=item.get('definition', ''),
                    part_of_speech=item.get('type', ''),
                    example_sentences=examples,
                    difficulty_level=diff_level
                ))
            
            if words_to_insert:
                Word.objects.insert(words_to_insert) # 批次寫入資料庫
                flash(f"成功匯入 {len(words_to_insert)} 筆單字！", "success")
            else:
                flash("JSON 檔案中沒有有效的單字。", "error")
        except Exception as e:
            flash(f"匯入失敗：{str(e)}", "error")
    else:
        flash("請上傳正確的 JSON 格式檔案！", "error")
        
    return redirect(url_for('word.manage_words'))

# The existing API endpoints for words (GET all, PUT, DELETE) will remain as JSON endpoints.
# If you want to integrate them into the admin_words.html, you'd use client-side JavaScript
# to call these JSON endpoints from the rendered page.

@word_bp.route('/admin/words', methods=['GET'])
@admin_required
def get_all_words():
    """Admin: Retrieves all words in the database."""
    words = word_service.get_all_words()
    return jsonify([word.to_mongo().to_dict() for word in words]), 200

@word_bp.route('/admin/words/<word_id>', methods=['PUT'])
@admin_required
def update_word(word_id):
    """Admin: Updates an existing word."""
    data = request.get_json()
    try:
        word = word_service.update_word(word_id, **data)
        return jsonify({"message": "Word updated successfully", "word_id": str(word.id)}), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 404
    except Exception as e:
        return jsonify({"message": "An error occurred", "error": str(e)}), 500

@word_bp.route('/', methods=['GET'])
@word_bp.route('/display', methods=['GET'])
def display_words():
    """公開頁面：自動匯入單字庫並展示總數與單字預覽"""

    # 2. 搜尋與分頁邏輯
    search_query = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 50 # 每頁顯示 50 筆單字
    
    if search_query:
        # 使用 icontains 進行不區分大小寫的模糊搜尋
        query_set = Word.objects(word_text__icontains=search_query)
    else:
        query_set = Word.objects
        
    total_words = query_set.count()
    total_pages = (total_words + per_page - 1) // per_page
    if total_pages == 0: total_pages = 1
    
    skip = (page - 1) * per_page
    words = query_set.skip(skip).limit(per_page)

    # 3. 渲染 HTML 頁面 (加入搜尋與分頁介面)
    html_template = """
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <title>系統單字庫</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; color: #333; background-color: #f4f7f6; }
            .stats-box { background-color: #e3f2fd; padding: 30px; border-radius: 8px; margin-bottom: 30px; text-align: center; border: 1px solid #bbdefb; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
            .stats-box h1 { margin-top: 0; color: #0277bd; font-size: 2.2em; }
            .stats-box h2 { font-size: 3.5em; margin: 10px 0; color: #01579b; font-weight: bold; }
            .search-form { text-align: center; margin-bottom: 30px; }
            .search-form input[type="text"] { padding: 12px; font-size: 1.1em; width: 300px; border: 1px solid #ccc; border-radius: 4px; }
            .search-form button { padding: 12px 20px; font-size: 1.1em; background-color: #0277bd; color: white; border: none; border-radius: 4px; cursor: pointer; }
            .search-form .clear-btn { padding: 11px 15px; text-decoration: none; background-color: #e0e0e0; color: #333; border-radius: 4px; margin-left: 5px; }
            .word-card { border: 1px solid #e0e0e0; padding: 20px; margin-bottom: 15px; border-radius: 8px; background-color: #fff; box-shadow: 0 2px 5px rgba(0,0,0,0.05); border-left: 5px solid #0277bd; }
            .word-title { font-size: 1.5em; font-weight: bold; color: #d32f2f; margin-bottom: 8px; text-transform: capitalize; }
            .word-meta { color: #666; font-size: 0.95em; margin-bottom: 12px; font-weight: 500; display: flex; gap: 15px;}
            .word-meta span { background: #eee; padding: 3px 8px; border-radius: 4px; }
            .pagination { text-align: center; margin-top: 40px; font-size: 1.2em; padding-bottom: 50px; }
            .pagination a { text-decoration: none; background-color: #0277bd; color: white; padding: 10px 20px; border-radius: 4px; margin: 0 10px; }
        </style>
    </head>
    <body>
        <div style="margin-bottom: 20px;">
            <a href="{{ url_for('dashboard.index') }}" style="text-decoration: none; color: #0277bd; font-weight: bold; font-size: 1.1em;">⬅️ 回到儀表板 (Back to Dashboard)</a>
        </div>
        <div class="stats-box">
            <h1>📚 系統單字庫已連線</h1>
            <p>目前符合條件的單字總數：</p>
            <h2>{{ count }}</h2>
        </div>
        
        <div class="search-form">
            <form method="GET" action="{{ url_for('word.display_words') }}">
                <input type="text" name="search" placeholder="搜尋單字 (例如: apple)..." value="{{ search }}">
                <button type="submit">搜尋</button>
                <a href="{{ url_for('word.display_words') }}" class="clear-btn">清除</a>
            </form>
        </div>
        
        {% for w in words %}
        <div class="word-card">
            <div class="word-title">{{ w.word_text }}</div>
            <div class="word-meta">
                <span>詞性: {{ w.part_of_speech }}</span> 
                <span>難度等級: {{ w.difficulty_level }}</span>
            </div>
            <div><strong>中文定義:</strong> {{ w.definition }}</div>
            {% if w.example_sentences %}
            <div style="margin-top: 10px; color: #555;"><em>📝 英文例句: "{{ w.example_sentences[0] }}"</em></div>
            {% endif %}
        </div>
        {% else %}
        <h3 style="text-align: center; color: #666;">{% if search %}找不到符合條件的單字。{% else %}目前尚未有任何單字在資料庫內{% endif %}</h3>
        {% endfor %}
        
        <div class="pagination">
            {% if page > 1 %}
            <a href="{{ url_for('word.display_words', page=page-1, search=search) }}">⬅️ 上一頁</a>
            {% endif %}
            <span style="margin: 0 15px;"> 第 {{ page }} 頁 / 共 {{ total_pages }} 頁 </span>
            {% if page < total_pages %}
            <a href="{{ url_for('word.display_words', page=page+1, search=search) }}">下一頁 ➡️</a>
            {% endif %}
            <form method="GET" action="{{ url_for('word.display_words') }}" style="display: inline-block; margin-left: 20px;">
                {% if search %}<input type="hidden" name="search" value="{{ search }}">{% endif %}
                跳至第 <input type="number" name="page" min="1" max="{{ total_pages }}" value="{{ page }}" style="width: 60px; padding: 5px; text-align: center; border: 1px solid #ccc; border-radius: 4px;"> 頁
                <button type="submit" style="padding: 5px 15px; font-size: 0.9em; background-color: #0277bd; color: white; border: none; border-radius: 4px; cursor: pointer;">跳轉</button>
            </form>
        </div>
    </body>
    </html>
    """
    
    return render_template_string(html_template, count=total_words, words=words, page=page, total_pages=total_pages, search=search_query)

@word_bp.route('/admin/words/<word_id>', methods=['DELETE'])
@admin_required
def delete_word(word_id):
    """Admin: Deletes a word by ID."""
    try:
        word_service.delete_word(word_id)
        return jsonify({"message": "Word deleted successfully"}), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 404
    except Exception as e:
        return jsonify({"message": "An error occurred", "error": str(e)}), 500

# --- Admin Endpoints for Sentence Rules ---
@word_bp.route('/admin/rules', methods=['POST'])
@admin_required
def add_rule():
    """Admin: Adds a new sentence generation rule."""
    data = request.get_json()
    try:
        rule = word_service.add_sentence_rule(
            rule_name=data['rule_name'],
            pattern=data['pattern'],
            keywords=data.get('keywords'),
            difficulty_level=data.get('difficulty_level', 1)
        )
        return jsonify({"message": "Rule added successfully", "rule_id": str(rule.id)}), 201
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": "An error occurred", "error": str(e)}), 500

@word_bp.route('/admin/rules', methods=['GET'])
@admin_required
def get_all_rules():
    """Admin: Retrieves all sentence generation rules."""
    rules = word_service.get_all_sentence_rules()
    return jsonify([rule.to_mongo().to_dict() for rule in rules]), 200

@word_bp.route('/admin/rules/<rule_id>', methods=['PUT'])
@admin_required
def update_rule(rule_id):
    """Admin: Updates an existing sentence generation rule."""
    data = request.get_json()
    try:
        rule = word_service.update_sentence_rule(rule_id, **data)
        return jsonify({"message": "Rule updated successfully", "rule_id": str(rule.id)}), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 404
    except Exception as e:
        return jsonify({"message": "An error occurred", "error": str(e)}), 500

@word_bp.route('/admin/rules/<rule_id>', methods=['DELETE'])
@admin_required
def delete_rule(rule_id):
    """Admin: Deletes a sentence generation rule by ID."""
    try:
        word_service.delete_sentence_rule(rule_id)
        return jsonify({"message": "Rule deleted successfully"}), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 404
    except Exception as e:
        return jsonify({"message": "An error occurred", "error": str(e)}), 500