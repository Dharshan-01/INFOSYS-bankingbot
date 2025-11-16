document.addEventListener("DOMContentLoaded", () => {
    
    const chatMessages = document.getElementById("chat-messages");
    const userInput = document.getElementById("user-input");
    const sendBtn = document.getElementById("send-btn");

    const API_URL = "http://127.0.0.1:5000/chat";

    // --- NEW: Session Management ---
    // This variable will store our session ID
    let currentSessionId = null; 

    // Function to add a message to the chat window
    function addMessage(sender, message) {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("message");
        messageDiv.classList.add(sender === "user" ? "user-message" : "bot-message");
        
        message = message.replace(/\n/g, "<br>");
        messageDiv.innerHTML = message;
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Function to handle sending a message
    async function sendMessage() {
        const messageText = userInput.value.trim();
        if (messageText === "") return;

        addMessage("user", messageText);
        userInput.value = ""; // Clear the input box

        try {
            // --- NEW: Send the session_id with the message ---
            const response = await fetch(API_URL, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                // If currentSessionId is null, we send 'new'
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
            
            // --- NEW: Always get the session_id back and save it ---
            currentSessionId = data.session_id;

            addMessage("bot", botResponse);

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

    // Add the first welcome message
    addMessage("bot", "Hello! How can I help you with your banking questions today?");
});