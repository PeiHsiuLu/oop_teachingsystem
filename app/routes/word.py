import json
import os
from mongoengine import StringField 
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
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
    """Admin: Displays a page to manage words."""

    if request.method == 'POST':
        word_text = request.form.get('word_text', '').strip()
        definition = request.form.get('definition', '').strip()
        part_of_speech = request.form.get('part_of_speech')
        example_sentences_str = request.form.get('example_sentences', '').strip()
        difficulty_level = request.form.get('difficulty_level', 'Unclassified')

        import re

        # 1. 驗證單字是否為英文
        if not re.match(r'^[a-zA-Z\- ]+$', word_text):
            flash("單字欄位僅能包含英文字母、橫線或空格。", "error")
            return redirect(url_for('word.manage_words'))

        # 2. 驗證定義是否包含中文
        if not re.search(r'[\u4e00-\u9fa5]', definition):
            flash("中文定義欄位必須包含中文字元。", "error")
            return redirect(url_for('word.manage_words'))

        # 3. 驗證定義是否包含奇怪的特殊符號
        if not re.match(r'^[\u4e00-\u9fa5a-zA-Z0-9\s，。！？、；：「」『』（）\(\)\[\]"\'\.,\-]+$', definition):
            flash("中文定義欄位包含不允許的特殊符號。", "error")
            return redirect(url_for('word.manage_words'))

        # 4. 驗證例句格式與是否包含單字
        if example_sentences_str:
            if not re.match(r'^[a-zA-Z0-9\s.,:;!?\'"\(\)\-\$%]+$', example_sentences_str):
                flash("英文例句欄位僅能包含英文、數字與基本標點符號。", "error")
                return redirect(url_for('word.manage_words'))

            if word_text.lower() not in example_sentences_str.lower():
                flash(f"英文例句中必須包含單字 '{word_text}'。", "error")
                return redirect(url_for('word.manage_words'))

        example_sentences = [
            s.strip()
            for s in example_sentences_str.split(';')
            if s.strip()
        ] if example_sentences_str else []

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

        return redirect(url_for('word.manage_words'))

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

    if total_pages == 0:
        total_pages = 1

    if page < 1:
        page = 1

    if page > total_pages:
        page = total_pages

    skip = (page - 1) * per_page
    words = query_set.skip(skip).limit(per_page)

    return render_template(
        "admin_words_manage.html",
        words=words,
        total_words=total_words,
        page=page,
        total_pages=total_pages,
        search=search_query
    )

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