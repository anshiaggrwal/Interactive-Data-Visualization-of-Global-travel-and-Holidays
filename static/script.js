// ==================== STATE MANAGEMENT ====================
let currentUser = null;

// ==================== PAGE NAVIGATION ====================
function showPage(pageId) {
    // Hide all sections
    document.querySelectorAll('.page-section').forEach(section => {
        section.classList.remove('active');
    });
    
    // Show selected section
    const targetSection = document.getElementById(pageId);
    if (targetSection) {
        targetSection.classList.add('active');
    }
    
    // Update nav active state
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === `#${pageId}`) {
            link.classList.add('active');
        }
    });
    
    // Scroll to top
    window.scrollTo(0, 0);
}

// Handle navigation clicks
document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        const pageId = link.getAttribute('href').substring(1);
        showPage(pageId);
    });
});

// ==================== AUTHENTICATION ====================
const loginModal = document.getElementById('loginModal');
const registerModal = document.getElementById('registerModal');
const loginBtn = document.getElementById('loginBtn');
const profileMenu = document.getElementById('profileMenu');
const profileBtn = document.getElementById('profileBtn');
const profileDropdown = document.getElementById('profileDropdown');

// Show login modal on page load after 2 seconds
setTimeout(() => {
    if (!currentUser) {
        loginModal.classList.add('show');
    }
}, 2000);

// Login button click
loginBtn.addEventListener('click', () => {
    loginModal.classList.add('show');
});

// Close modals
document.getElementById('closeLogin').addEventListener('click', () => {
    loginModal.classList.remove('show');
});

document.getElementById('closeRegister').addEventListener('click', () => {
    registerModal.classList.remove('show');
});

// Switch between login and register
document.getElementById('switchToRegister').addEventListener('click', (e) => {
    e.preventDefault();
    loginModal.classList.remove('show');
    registerModal.classList.add('show');
});

document.getElementById('switchToLogin').addEventListener('click', (e) => {
    e.preventDefault();
    registerModal.classList.remove('show');
    loginModal.classList.add('show');
});

// Close modal on outside click
window.addEventListener('click', (e) => {
    if (e.target === loginModal) {
        loginModal.classList.remove('show');
    }
    if (e.target === registerModal) {
        registerModal.classList.remove('show');
    }
});

// Login form submission
document.getElementById('loginForm').addEventListener('submit', (e) => {
    e.preventDefault();
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;
    
    // In production, validate with backend
    currentUser = {
        name: email.split('@')[0],
        email: email
    };
    
    updateAuthUI();
    loginModal.classList.remove('show');
    
    // Show success message
    alert('Login successful! Welcome back.');
});

// Register form submission
document.getElementById('registerForm').addEventListener('submit', (e) => {
    e.preventDefault();
    const name = document.getElementById('registerName').value;
    const email = document.getElementById('registerEmail').value;
    const password = document.getElementById('registerPassword').value;
    
    // In production, send to backend
    currentUser = {
        name: name,
        email: email
    };
    
    updateAuthUI();
    registerModal.classList.remove('show');
    
    // Show success message
    alert('Account created successfully! Welcome to TravelInsights AI.');
});

// Logout
document.getElementById('logoutLink').addEventListener('click', (e) => {
    e.preventDefault();
    currentUser = null;
    updateAuthUI();
    showPage('home');
    alert('Logged out successfully.');
});

// Update UI based on auth state
function updateAuthUI() {
    if (currentUser) {
        loginBtn.style.display = 'none';
        profileMenu.style.display = 'block';
        document.getElementById('profileName').textContent = currentUser.name;
        
        // Update profile form
        document.getElementById('profileFullName').value = currentUser.name || '';
        document.getElementById('profileEmail').value = currentUser.email || '';
    } else {
        loginBtn.style.display = 'block';
        profileMenu.style.display = 'none';
    }
}

// Profile dropdown toggle
profileBtn.addEventListener('click', () => {
    profileDropdown.classList.toggle('show');
});

// Close dropdown when clicking outside
document.addEventListener('click', (e) => {
    if (!profileMenu.contains(e.target)) {
        profileDropdown.classList.remove('show');
    }
});

// Profile dropdown navigation
profileDropdown.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', (e) => {
        if (link.id !== 'logoutLink') {
            e.preventDefault();
            const pageId = link.getAttribute('href').substring(1);
            showPage(pageId);
            profileDropdown.classList.remove('show');
        }
    });
});

// ==================== PROFILE FORM ====================
document.getElementById('profileForm').addEventListener('submit', (e) => {
    e.preventDefault();
    
    const name = document.getElementById('profileFullName').value;
    const email = document.getElementById('profileEmail').value;
    const org = document.getElementById('profileOrg').value;
    const role = document.getElementById('profileRole').value;
    
    // In production, send to backend
    if (currentUser) {
        currentUser.name = name;
        currentUser.email = email;
        currentUser.org = org;
        currentUser.role = role;
        
        updateAuthUI();
    }
    
    const statusMsg = document.getElementById('profileStatus');
    statusMsg.textContent = '✓ Profile updated successfully!';
    statusMsg.className = 'status-message success show';
    
    setTimeout(() => {
        statusMsg.classList.remove('show');
    }, 3000);
});

// ==================== FEEDBACK FORM ====================
document.getElementById('feedbackForm').addEventListener('submit', (e) => {
    e.preventDefault();
    
    const type = document.getElementById('feedbackType').value;
    const subject = document.getElementById('feedbackSubject').value;
    const message = document.getElementById('feedbackMessage').value;
    
    // In production, send to backend
    console.log('Feedback submitted:', { type, subject, message });
    
    const statusMsg = document.getElementById('feedbackStatus');
    statusMsg.textContent = '✓ Thank you for your feedback! We will review it shortly.';
    statusMsg.className = 'status-message success show';
    
    // Reset form
    e.target.reset();
    
    setTimeout(() => {
        statusMsg.classList.remove('show');
    }, 3000);
});

// ==================== QUIZ ====================
document.getElementById('quizForm').addEventListener('submit', (e) => {
    e.preventDefault();
    
    const answers = {
        q1: 'b',
        q2: 'b',
        q3: 'a'
    };
    
    let score = 0;
    Object.keys(answers).forEach(q => {
        const selected = document.querySelector(`input[name="${q}"]:checked`);
        if (selected && selected.value === answers[q]) {
            score++;
        }
    });
    
    const resultDiv = document.getElementById('quizResult');
    resultDiv.textContent = `You scored ${score} out of 3!`;
    
    if (score === 3) {
        resultDiv.textContent += ' 🎉 Excellent! You have great knowledge of tourism analytics.';
        resultDiv.className = 'quiz-result success show';
    } else {
        resultDiv.textContent += ' Keep learning and try again!';
        resultDiv.className = 'quiz-result partial show';
    }
});

// ==================== CHATBOT - FINAL 100% WORKING VERSION ====================
const chatbotFloat = document.getElementById('chatbotFloat');
const chatbotPopup = document.getElementById('chatbotPopup');
const closeChatbot = document.getElementById('closeChatbot');
const chatbotMessages = document.getElementById('chatbotMessages');
const chatbotInput = document.getElementById('chatbotInput');
const chatbotCategory = document.getElementById('chatbotCategory');
const chatbotSend = document.getElementById('chatbotSend');

// Open chatbot
chatbotFloat.addEventListener('click', () => {
    chatbotPopup.classList.add('show');
    if (chatbotMessages.children.length === 0) {
        addChatMessage('bot', `👋 Hello! I'm <b>Tara</b>, your travel assistant.<br><br>Select a category and ask me anything!`);
    }
});

// Close chatbot
closeChatbot.addEventListener('click', () => {
    chatbotPopup.classList.remove('show');
});

// Send message
chatbotSend.addEventListener('click', sendChatMessage);
chatbotInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendChatMessage();
    }
});

// Optional category selection message (will disappear when you send)
chatbotCategory.addEventListener('change', () => {
    if (chatbotCategory.value) {
        const text = chatbotCategory.options[chatbotCategory.selectedIndex].text;
        addChatMessage('bot', `✓ Selected: <b>${text}</b><br>Now ask your question!`).classList.add('temp-msg');
    }
});

async function sendChatMessage() {
    const message = chatbotInput.value.trim();
    const category = chatbotCategory.value;

    if (!message) return;
    if (!category) {
        addChatMessage('bot', '⚠️ Please select a category first.');
        return;
    }

    // Remove previous "Selected category" message
    document.querySelectorAll('.temp-msg').forEach(el => el.remove());

    // Show your question
    addChatMessage('user', message);
    chatbotInput.value = '';

    // Show thinking
    const thinking = addChatMessage('bot', 'Thinking<span class="dots">...</span>');

    try {
        const res = await fetch('http://localhost:5000/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: message, category })
        });
        const data = await res.json();

        thinking.remove();

        if (data.ok) {
            data.results.forEach(r => addChatMessage('bot', r));
        } else {
            addChatMessage('bot', `⚠️ ${data.message}`);
        }
    } catch (err) {
        thinking.remove();
        addChatMessage('bot', '⚠️ Server error. Is Flask running?');
    }
}

function addChatMessage(type, content) {
    const div = document.createElement('div');
    div.className = `chat-message ${type}`;
    div.innerHTML = content;
    chatbotMessages.appendChild(div);
    chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
    return div;
}

// Beautiful dots animation
document.head.insertAdjacentHTML('beforeend', `
<style>
.temp-msg { opacity: 0.8; font-size: 0.9em; }
.dots { display: inline-block; }
.dots { animation: dots 1.5s infinite; }
@keyframes dots {
    0%, 100% { opacity: 0.4; }
    50% { opacity: 1; }
}
</style>
`);
// ==================== INITIAL STATE ====================
// Show home page by default
showPage('home');

// Add loading animation style
const style = document.createElement('style');
style.textContent = `
    .loading-dots {
        display: inline-block;
        animation: blink 1.4s infinite;
    }
    @keyframes blink {
        0%, 20% { opacity: 1; }
        50% { opacity: 0.3; }
        100% { opacity: 1; }
    }
`;
document.head.appendChild(style);
document.querySelectorAll('.tab-button').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.tab-button').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById(btn.dataset.tab).classList.add('active');
    });
});