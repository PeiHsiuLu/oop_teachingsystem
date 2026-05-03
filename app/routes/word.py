import json
import os
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
        word_text = request.form.get('word_text')
        definition = request.form.get('definition')
        part_of_speech = request.form.get('part_of_speech')
        example_sentences_str = request.form.get('example_sentences')
        difficulty_level_str = request.form.get('difficulty_level')

        example_sentences = [s.strip() for s in example_sentences_str.split(';') if s.strip()] if example_sentences_str else []
        difficulty_level = int(difficulty_level_str) if difficulty_level_str else 1

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
                    <div class="form-group" style="flex: 1;"><label>詞性 (Part of Speech):</label><input type="text" name="part_of_speech" placeholder="e.g., noun, verb"></div>
                    <div class="form-group" style="flex: 2;"><label>例句 (Example Sentences - 以分號分隔):</label><input type="text" name="example_sentences"></div>
                    <div class="form-group" style="flex: 1;">
                        <label>難度 (1-5):</label>
                        <select name="difficulty_level">
                            <option value="1">1 (Easy)</option>
                            <option value="2">2</option><option value="3">3</option><option value="4">4</option>
                            <option value="5">5 (Hard)</option>
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
        
        <table>
            <tr><th>單字</th><th>定義</th><th>詞性</th><th>難度</th><th>例句</th><th>操作</th></tr>
            {% for w in words %}
            <tr>
                <td><strong>{{ w.word_text }}</strong></td>
                <td>{{ w.definition }}</td>
                <td>{{ w.part_of_speech }}</td>
                <td>{{ w.difficulty_level }}</td>
                <td><em style="color: #555;">{{ w.example_sentences[0] if w.example_sentences else '無' }}</em></td>
                <td><button onclick="deleteWord('{{ w.id }}')" style="background: #d32f2f; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor:pointer;">刪除</button></td>
            </tr>
            {% endfor %}
        </table>
        
        <div class="pagination">{% if page > 1 %}<a href="{{ url_for('word.manage_words', page=page-1, search=search) }}">⬅️ 上一頁</a>{% endif %}<span> 第 {{ page }} 頁 / 共 {{ total_pages }} 頁 </span>{% if page < total_pages %}<a href="{{ url_for('word.manage_words', page=page+1, search=search) }}">下一頁 ➡️</a>{% endif %}</div>
        <script>function deleteWord(id) { if(confirm("確定要刪除這個單字嗎？")) { fetch('/word/admin/words/' + id, { method: 'DELETE' }).then(response => response.json()).then(data => { alert(data.message); location.reload(); }); } }</script>
    </body>
    </html>
    """
    return render_template_string(html_template, words=words, total_words=total_words, page=page, total_pages=total_pages, search=search_query)

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
    
    # 1. 檢查資料庫是否有資料，或者是否為舊版不符合 Model 格式的資料
    first_word = Word.objects.first()
    if not first_word or not first_word.word_text:
        # 清除舊的或格式錯誤的資料
        Word.drop_collection()
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(current_dir, '..', 'word_list.json')
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                word_list = json.load(f)
            
            # 將 CEFR 等級對應到 difficulty_level (1-5)
            level_map = {'A1': 1, 'A2': 2, 'B1': 3, 'B2': 4, 'C1': 5, 'Unclassified': 1}
            words_to_insert = []
            
            for item in word_list:
                diff_level = level_map.get(item.get('level', 'A1'), 1)
                words_to_insert.append(Word(
                    word_text=item.get('word'),
                    definition=item.get('definition'),
                    part_of_speech=item.get('type'),
                    example_sentences=[item.get('example')] if item.get('example') else [],
                    difficulty_level=diff_level
                ))
            
            # 使用 MongoEngine 進行批次寫入，提升效能
            Word.objects.insert(words_to_insert)
        except Exception as e:
            return f"<h1>載入單字時發生錯誤: {e}</h1>"

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
            <div style="margin-top: 10px; color: #555;"><em>📝 例句: "{{ w.example_sentences[0] }}"</em></div>
            {% endif %}
        </div>
        {% else %}
        <h3 style="text-align: center; color: #666;">找不到符合條件的單字。</h3>
        {% endfor %}
        
        <div class="pagination">
            {% if page > 1 %}
            <a href="{{ url_for('word.display_words', page=page-1, search=search) }}">⬅️ 上一頁</a>
            {% endif %}
            <span style="margin: 0 15px;"> 第 {{ page }} 頁 / 共 {{ total_pages }} 頁 </span>
            {% if page < total_pages %}
            <a href="{{ url_for('word.display_words', page=page+1, search=search) }}">下一頁 ➡️</a>
            {% endif %}
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