document.addEventListener('DOMContentLoaded', () => {
    // --- CONFIGURATION ---
    // !!! UPDATE THIS TO YOUR CURRENT IP !!!
    // ✅ Change it to this:
    const API_URL = "http://127.0.0.1:5000/chat"; 
    const INACTIVITY_LIMIT = 15 * 60 * 1000; // 15 Minutes

    // --- DOM ELEMENTS ---
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const micBtn = document.getElementById('mic-btn');
    const chatBox = document.getElementById('chat-box');
    const logoutBtn = document.getElementById('logout-btn');
    const muteBtn = document.getElementById('mute-btn');

    // --- STATE ---
    let userId = sessionStorage.getItem('nova_user_id');
    let userName = sessionStorage.getItem('nova_user_name');
    let logoutTimer;
    let isMuted = false;

    // --- 1. INITIALIZATION ---
    if (userId && userName) {
        addMessage(`👋 Welcome back, ${userName}!`, 'bot');
    } else {
        addMessage("👋 Hello! I am Vaulty. (Guest Mode)", 'bot');
    }

    // START THE TIMER (Fixed)
    resetTimer(); 

    // --- 2. VOICE RECOGNITION (Input) ---
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    let recognition;
    
    if (SpeechRecognition) {
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.lang = 'en-US';

        recognition.onstart = () => { 
            micBtn.classList.add('listening'); 
            micBtn.style.backgroundColor = "#ef4444"; // Visual cue red
        };
        recognition.onend = () => { 
            micBtn.classList.remove('listening'); 
            micBtn.style.backgroundColor = ""; // Reset color
        };
        
        recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        userInput.value = transcript;
        // sendMessage(); // <--- Deleted or Commented out
        userInput.focus(); // Keeps cursor in the box so you can edit
        };

        micBtn.onclick = () => { recognition.start(); resetTimer(); };
    } else {
        micBtn.style.display = 'none'; // Hide if not supported
    }

    // --- 3. SPEECH SYNTHESIS (Output) ---
    function speakText(text) {
        if (isMuted) return;
        const cleanText = text.replace(/<[^>]*>?/gm, ''); 
        const utterance = new SpeechSynthesisUtterance(cleanText);
        window.speechSynthesis.cancel();
        window.speechSynthesis.speak(utterance);
    }

    muteBtn.onclick = () => {
        isMuted = !isMuted;
        // Update icon
        muteBtn.innerHTML = isMuted ? '<i class="fas fa-volume-mute"></i>' : '<i class="fas fa-volume-up"></i>';
        if(isMuted) window.speechSynthesis.cancel();
    };

    // --- 4. LOGOUT & TIMER ---
    function logout() {
        sessionStorage.clear();
        window.location.href = 'login.html';
    }
    
    // Attach Logout Click Event
    if(logoutBtn) logoutBtn.addEventListener('click', logout);

    function resetTimer() {
        clearTimeout(logoutTimer);
        logoutTimer = setTimeout(() => {
            alert("Session timed out.");
            logout();
        }, INACTIVITY_LIMIT);
    }

    // Reset timer on interaction
    document.onmousemove = resetTimer;
    document.onkeypress = resetTimer;

    // --- 5. CHAT LOGIC ---
    function addMessage(text, sender) {
        const div = document.createElement('div');
        div.classList.add('message', sender === 'user' ? 'user-message' : 'bot-message');
        div.innerHTML = text.replace(/\n/g, '<br>');
        chatBox.appendChild(div);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function addSuggestions(list) {
        if (!list || list.length === 0) return;
        const div = document.createElement('div');
        div.className = 'suggestion-container';
        list.forEach(item => {
            const btn = document.createElement('button');
            btn.className = 'suggestion-btn';
            btn.innerText = item;
            btn.onclick = () => { userInput.value = item; sendMessage(); div.remove(); };
            div.appendChild(btn);
        });
        chatBox.appendChild(div);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    async function sendMessage() {
        const text = userInput.value.trim();
        if (!text) return;

        // Cleanup old suggestions
        const oldSug = document.querySelectorAll('.suggestion-container');
        oldSug.forEach(el => el.remove());

        addMessage(text, 'user');
        userInput.value = '';
        resetTimer();

        // Loading Bubble
        const loader = document.createElement('div');
        loader.className = 'message bot-message';
        loader.id = 'loading';
        loader.innerHTML = '<i>Typing...</i>';
        chatBox.appendChild(loader);

        try {
            const res = await fetch(API_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text, user_id: userId })
            });

            if (res.status === 401 || res.status === 403) {
                alert("Session expired.");
                logout();
                return;
            }

            const data = await res.json();
            
            // Remove Loader
            if(document.getElementById('loading')) document.getElementById('loading').remove();

            addMessage(data.response, 'bot');
            speakText(data.response);
            addSuggestions(data.suggestions);

        } catch (e) {
            if(document.getElementById('loading')) document.getElementById('loading').remove();
            addMessage("⚠️ Connection Lost.", 'bot');
            console.error(e);
        }
    }

    // Attach Event Listeners
    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => { 
        if (e.key === 'Enter') sendMessage(); 
    });
});