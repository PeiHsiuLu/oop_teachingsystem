from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from flask_login import login_required, current_user
from app.services.srs_service import SRSManager, SuperMemo2Strategy
from app.repositories.word_repository import WordRepository
from app.services.analytics_service import AnalyticsEngine
from app.models.word import Word, ReviewItem

srs_bp = Blueprint('srs', __name__)

# --- Service Instantiation ---
# In a real app, you'd use a dependency injection container.
# For now, we instantiate them here. The strategy is chosen here.
word_repo = WordRepository()
srs_strategy = SuperMemo2Strategy()
srs_manager = SRSManager(strategy=srs_strategy, word_repository=word_repo)
analytics_engine = AnalyticsEngine()

@srs_bp.route('/review/next', methods=['GET'])
@login_required
def get_next_review_word():
    """Gets the next word for the current user to review and displays it on a page."""
    items_to_review = srs_manager.get_words_for_review(current_user.id, limit=1)
    
    if not items_to_review:
        # No words to review, show a completion page
        return render_template('review_card.html', card=None)

    item = items_to_review[0]
    
    # Normalize the data for the template, whether it's a ReviewItem or a new Word
    if isinstance(item, ReviewItem):
        # It's an existing item, the word data is nested
        card_data = {
            'id': str(item.word.id),
            'word_text': item.word.word_text,
            'definition': item.word.definition,
            'part_of_speech': item.word.part_of_speech
        }
    elif isinstance(item, Word):
        # It's a brand new word for the user
        card_data = {
            'id': str(item.id),
            'word_text': item.word_text,
            'definition': item.definition,
            'part_of_speech': item.part_of_speech
        }
    else:
        # Should not happen, but good to handle
        return render_template('review_card.html', card=None)

    return render_template('review_card.html', card=card_data)

@srs_bp.route('/review', methods=['POST'])
@login_required
def submit_review():
    """Submits the result of a word review from the web form."""
    form_data = request.form
    word_id = form_data.get('word_id')
    # Quality comes from the form as a string, convert to int
    quality_str = form_data.get('quality')

    if not word_id or quality_str is None:
        # Handle error, maybe flash a message and redirect
        return redirect(url_for('srs.get_next_review_word'))

    try:
        quality = int(quality_str)
        srs_manager.process_review_result(current_user.id, word_id, quality)
        
        # Log this event for analytics
        analytics_engine.log_event(current_user.id, 'WORD_REVIEW', {'word_id': word_id, 'user_response_quality': quality})
    except (ValueError, TypeError):
        # Handle cases where quality is not a valid integer or word not found
        return redirect(url_for('srs.get_next_review_word'))

    # Redirect to the next card after submission
    return redirect(url_for('srs.get_next_review_word'))