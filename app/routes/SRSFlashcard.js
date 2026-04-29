import React, { useState, useEffect } from 'react';

// --- Component-level Styles (CSS-in-JS) ---
const styles = {
    container: {
        maxWidth: '500px',
        margin: '2rem auto',
        padding: '2rem',
        backgroundColor: '#fff',
        borderRadius: '8px',
        boxShadow: '0 4px 8px rgba(0,0,0,0.1)',
        textAlign: 'center',
    },
    card: {
        backgroundColor: '#f8f9fa',
        border: '1px solid #dee2e6',
        borderRadius: '8px',
        padding: '3rem 1rem',
        minHeight: '150px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        cursor: 'pointer',
        marginBottom: '1.5rem',
    },
    wordText: {
        fontSize: '2.5rem',
        fontWeight: 'bold',
        color: '#212529',
    },
    definition: {
        fontSize: '1.2rem',
        color: '#495057',
    },
    buttonGroup: {
        display: 'flex',
        justifyContent: 'space-around',
        marginTop: '1rem',
    },
    button: {
        padding: '0.75rem 1.5rem',
        fontSize: '1rem',
        border: 'none',
        borderRadius: '0.25rem',
        cursor: 'pointer',
        color: '#fff',
    },
};

const SRSFlashcard = () => {
    // --- State Management ---
    const [card, setCard] = useState(null); // Holds the current word/review item data
    const [isFlipped, setIsFlipped] = useState(false); // Manages the card's front/back state
    const [isLoading, setIsLoading] = useState(true); // Manages loading state

    // --- Data Fetching Logic ---
    const fetchNextWord = async () => {
        setIsLoading(true);
        setIsFlipped(false); // Reset card to front-facing
        try {
            // This corresponds to your `@srs_bp.route('/review/next', methods=['GET'])`
            const response = await fetch('/srs/review/next');
            if (!response.ok) throw new Error('Failed to fetch next word.');
            const data = await response.json();
            
            // The backend returns either a ReviewItem or a Word. We need to normalize it.
            // A ReviewItem has a 'word' field, a new Word does not.
            const wordData = data.word ? data.word : data;
            setCard({ ...wordData, _id: wordData._id.$oid }); // Normalize the ObjectId

        } catch (error) {
            console.error("Error fetching word:", error);
            setCard(null); // Clear card on error
        } finally {
            setIsLoading(false);
        }
    };

    // --- Side Effect Hook ---
    // Runs once when the component first mounts to fetch the initial card.
    useEffect(() => {
        fetchNextWord();
    }, []); // Empty dependency array means this runs only once.

    // --- Event Handlers ---
    const handleReviewSubmit = async (quality) => {
        if (!card) return;

        // This corresponds to your `@srs_bp.route('/review', methods=['POST'])`
        await fetch('/srs/review', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                word_id: card._id,
                quality: quality, // 0-5 rating from the buttons
            }),
        });

        // After submitting the result, automatically fetch the next word.
        fetchNextWord();
    };

    if (isLoading) return <div style={styles.container}>Loading your next word...</div>;
    if (!card) return <div style={styles.container}>Congratulations! No more words to review for now.</div>;

    // --- Render Logic ---
    return (
        <div style={styles.container}>
            <h2>單字複習 (Vocabulary Review)</h2>
            <div style={styles.card} onClick={() => setIsFlipped(!isFlipped)}>
                {!isFlipped ? (
                    <div style={styles.wordText}>{card.word_text}</div>
                ) : (
                    <div>
                        <div style={styles.wordText}>{card.word_text}</div>
                        <p style={styles.definition}>{card.definition}</p>
                        <small>{card.part_of_speech}</small>
                    </div>
                )}
            </div>

            {!isFlipped ? (
                <button style={{...styles.button, backgroundColor: '#007bff'}} onClick={() => setIsFlipped(true)}>Show Answer</button>
            ) : (
                <div style={styles.buttonGroup}>
                    <button style={{...styles.button, backgroundColor: '#dc3545'}} onClick={() => handleReviewSubmit(1)}>Forgot (不記得)</button>
                    <button style={{...styles.button, backgroundColor: '#ffc107'}} onClick={() => handleReviewSubmit(3)}>Hard (困難)</button>
                    <button style={{...styles.button, backgroundColor: '#28a745'}} onClick={() => handleReviewSubmit(5)}>Easy (簡單)</button>
                </div>
            )}
        </div>
    );
};

export default SRSFlashcard;