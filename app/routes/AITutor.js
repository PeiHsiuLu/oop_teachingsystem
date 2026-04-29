import React, { useState, useEffect, useRef } from 'react';

// --- Component-level Styles ---
const styles = {
    chatWindow: {
        maxWidth: '600px',
        margin: '2rem auto',
        border: '1px solid #ccc',
        borderRadius: '8px',
        display: 'flex',
        flexDirection: 'column',
        height: '70vh',
    },
    messagesContainer: {
        flex: 1,
        padding: '1rem',
        overflowY: 'auto',
        backgroundColor: '#f9f9f9',
    },
    message: {
        marginBottom: '1rem',
        padding: '0.5rem 1rem',
        borderRadius: '18px',
        maxWidth: '75%',
    },
    systemMessage: {
        backgroundColor: '#e9ecef',
        alignSelf: 'flex-start',
    },
    userMessage: {
        backgroundColor: '#007bff',
        color: 'white',
        alignSelf: 'flex-end',
        marginLeft: 'auto',
    },
    optionsContainer: {
        padding: '1rem',
        borderTop: '1px solid #ccc',
        display: 'flex',
        flexWrap: 'wrap',
        gap: '0.5rem',
    },
    optionButton: {
        padding: '0.5rem 1rem',
        border: '1px solid #007bff',
        backgroundColor: 'white',
        color: '#007bff',
        borderRadius: '18px',
        cursor: 'pointer',
    },
};

const AITutor = ({ scenarioId }) => {
    // --- State Management ---
    const [messages, setMessages] = useState([]); // Holds the list of chat messages
    const [currentNode, setCurrentNode] = useState(null); // Holds the current dialogue node from the backend
    const messagesEndRef = useRef(null); // Used to auto-scroll to the latest message

    // --- Auto-scrolling Logic ---
    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(scrollToBottom, [messages]);

    // --- Data Fetching & Side Effects ---
    // Fetches the starting node of the dialogue scenario
    useEffect(() => {
        const startDialogue = async () => {
            // ASSUMED BACKEND ENDPOINT: GET /dialogue/start/{scenario_id}
            const response = await fetch(`/dialogue/start/${scenarioId}`);
            const startNode = await response.json();
            setCurrentNode(startNode);
            setMessages([{ speaker: 'system', text: startNode.text }]);
        };
        startDialogue();
    }, [scenarioId]); // Re-run if the scenarioId prop changes

    // --- Event Handlers ---
    const handleOptionSelect = async (option) => {
        // 1. Add user's choice to the chat display
        const userMessage = { speaker: 'user', text: option.text };
        setMessages(prev => [...prev, userMessage]);

        // 2. Send choice to backend to get the next node
        // ASSUMED BACKEND ENDPOINT: POST /dialogue/next
        const response = await fetch('/dialogue/next', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                scenario_id: currentNode.scenario_id,
                current_node_id: currentNode.node_id,
                chosen_option_text: option.text,
            }),
        });
        const nextNode = await response.json();

        // 3. Update the current node and add the system's response to the chat
        setCurrentNode(nextNode);
        const systemMessage = { speaker: 'system', text: nextNode.text };
        setMessages(prev => [...prev, userMessage, systemMessage]);
    };

    return (
        <div style={styles.chatWindow}>
            <div style={styles.messagesContainer}>
                {messages.map((msg, index) => (
                    <div key={index} style={{...styles.message, ...(msg.speaker === 'system' ? styles.systemMessage : styles.userMessage)}}>
                        {msg.text}
                    </div>
                ))}
                <div ref={messagesEndRef} />
            </div>
            <div style={styles.optionsContainer}>
                {currentNode?.options.map((opt, index) => (
                    <button key={index} style={styles.optionButton} onClick={() => handleOptionSelect(opt)}>
                        {opt.text}
                    </button>
                ))}
            </div>
        </div>
    );
};

export default AITutor;