document.addEventListener("DOMContentLoaded", () => {
    
    const chatMessages = document.getElementById("chat-messages");
    const userInput = document.getElementById("user-input");
    const sendBtn = document.getElementById("send-btn");

    const API_URL = "http://127.0.0.1:5000/chat";

    let currentSessionId = null; 

    // Function to add a text message to the chat window
    function addMessage(sender, message) {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("message");
        messageDiv.classList.add(sender === "user" ? "user-message" : "bot-message");
        
        message = message.replace(/\n/g, "<br>");
        messageDiv.innerHTML = message;
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // --- NEW: Function to add suggestion buttons ---
    function addSuggestionButtons(suggestions) {
        // First, remove any old suggestion buttons
        const oldSuggestions = document.querySelector(".suggestion-container");
        if (oldSuggestions) {
            oldSuggestions.remove();
        }

        // If no new suggestions, do nothing
        if (!suggestions || suggestions.length === 0) {
            return;
        }

        // Create the container for the buttons
        const container = document.createElement("div");
        container.className = "suggestion-container";

        // Create a button for each suggestion
        suggestions.forEach(text => {
            const btn = document.createElement("button");
            btn.className = "suggestion-btn";
            btn.innerText = text;
            
            // --- NEW: When a button is clicked... ---
            btn.onclick = () => {
                // 1. Put the text in the input box (looks nice)
                userInput.value = text;
                // 2. Send the message immediately
                sendMessage();
                // 3. Remove the buttons (sendMessage will do this)
            };
            
            container.appendChild(btn);
        });

        // Add the container to the chat
        chatMessages.appendChild(container);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }


    // Function to handle sending a message
    async function sendMessage() {
        const messageText = userInput.value.trim();
        if (messageText === "") return;

        // --- NEW: Remove any existing buttons when user types ---
        const oldSuggestions = document.querySelector(".suggestion-container");
        if (oldSuggestions) {
            oldSuggestions.remove();
        }

        addMessage("user", messageText);
        userInput.value = ""; // Clear the input box

        try {
            const response = await fetch(API_URL, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ 
                    message: messageText,
                    session_id: currentSessionId || "new"
                }),
            });

            if (!response.ok) {
                throw new Error("Network response was not ok");
            }

            const data = await response.json();
            const botResponse = data.response;
            const suggestions = data.suggestions; // <-- NEW
            
            currentSessionId = data.session_id;

            addMessage("bot", botResponse);
            
            // --- NEW: Add the suggestion buttons ---
            addSuggestionButtons(suggestions); 

        } catch (error) {
            console.error("Error:", error);
            addMessage("bot", "I'm having trouble connecting to my brain. Please try again later.");
        }
    }

    // --- Event Listeners ---
    sendBtn.addEventListener("click", sendMessage);
    userInput.addEventListener("keypress", (event) => {
        if (event.key === "Enter") {
            sendMessage();
        }
    });

    // Add the first welcome message (with suggestions)
    addMessage("bot", "Hello! How can I help you with your banking questions today?");
    // Manually add the first suggestions for 'greet' intent
    addSuggestionButtons(["What's my balance?", "How do I open an account?"]);
});