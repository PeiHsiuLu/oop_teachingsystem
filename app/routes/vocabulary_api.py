from flask import Blueprint, request, jsonify, render_template
from flask_login import current_user
from datetime import datetime, timedelta

from app.utils.decorators import role_required
from app.services.vocabulary_service import VocabularyService
from app.repositories.vocabulary_repository import VocabularyRepository
from app.models.vocabulary import Word

vocabulary_bp = Blueprint('vocabulary_bp', __name__)
vocab_service = VocabularyService()
vocab_repo = VocabularyRepository()

# ==========================================
# Student Endpoints (UC3_1 & UC3_2)
# ==========================================

@vocabulary_bp.route('/student/vocabulary', methods=['GET'])
@role_required('Student')
def student_vocabulary_page():
    """Renders the frontend page for the vocabulary review session."""
    return render_template('student_vocabulary.html')

@vocabulary_bp.route('/api/vocabulary/review', methods=['GET'])
@role_required('Student')
def get_review_session():
    """Fetches words due for review and dynamically generates sentences for them."""
    words = vocab_repo.get_words_due_for_review(current_user.id)
    
    review_data = []
    for w in words:
        sentence = vocab_service.generate_dynamic_sentence(w.word)
        review_data.append({
            'word': w.word,
            'definition': w.definition,
            'example_sentence': sentence
        })
        
    return jsonify(review_data), 200

@vocabulary_bp.route('/api/vocabulary/review', methods=['POST'])
@role_required('Student')
def submit_word_review():
    """Submits the student's performance rating and updates the SRS intervals."""
    data = request.json
    success = vocab_service.process_review(
        user_id=current_user.id, 
        word_str=data.get('word'), 
        performance_rating=data.get('rating')
    )
    
    if success:
        return jsonify({'message': 'Review recorded successfully'}), 200
    return jsonify({'error': 'Word not found or update failed'}), 400

# ==========================================
# Admin Endpoints (UC3_3 & UC3_4)
# ==========================================

@vocabulary_bp.route('/api/admin/vocabulary/rules', methods=['POST'])
@role_required('Admin')
def set_generation_rules():
    """UC3_4: 設定例句生成規則. Admins set global rules for sentence generation."""
    data = request.json
    # Admin logic to save rules (e.g., target CEFR level, tone) into the database would go here.
    return jsonify({'message': 'Sentence generation rules successfully updated'}), 200

# ==========================================
# Utility Endpoints
# ==========================================

@vocabulary_bp.route('/api/vocabulary/seed', methods=['GET'])
@role_required('Student')
def seed_test_data():
    """Seeds the database with test vocabulary words for the current student."""
    from app.models.vocabulary import VocabularyBank
    
    bank = vocab_repo.get_user_bank(current_user.id)
    if not bank:
        bank = VocabularyBank(user_id=current_user.id)
        
    test_words_data = [
        {"word": "Ephemeral", "definition": "Lasting for a very short time.", "category": "Adjective"},
        {"word": "Ubiquitous", "definition": "Present, appearing, or found everywhere.", "category": "Adjective"},
        {"word": "Pragmatic", "definition": "Dealing with things sensibly and realistically.", "category": "Adjective"}
    ]
    
    existing_words = {w.word for w in bank.list_of_words}
    new_words_added = 0

    for data in test_words_data:
        if data['word'] not in existing_words:
            word_obj = Word(**data, next_review_date=datetime.utcnow() - timedelta(days=1))
            bank.list_of_words.append(word_obj)
            new_words_added += 1

    if new_words_added > 0:
        bank.save()
        return jsonify({'message': f'{new_words_added} new test words seeded! Refresh your dashboard to see them.'}), 200
    else:
        return jsonify({'message': 'Test words have already been added to your vocabulary bank.'}), 200
        