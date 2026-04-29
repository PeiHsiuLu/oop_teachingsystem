from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_required, current_user # Assuming current_user is available
from functools import wraps # Import wraps
from app.services.word_service import WordService
from app.services.auth_service import AuthService # To validate admin role

word_bp = Blueprint('word', __name__)
word_service = WordService()
auth_service = AuthService() # For role validation

# Helper decorator to ensure the user is an admin
def admin_required(f):
    @wraps(f) # Use functools.wraps to preserve function metadata
    @login_required
    def decorated_function(*args, **kwargs):
        if not auth_service.validate_role(current_user.id, 'admin'):
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

    # For GET request, display the page with all words
    words = word_service.get_all_words()
    return render_template('admin_words.html', words=words)

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