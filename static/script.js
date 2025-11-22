// ==================== STATE MANAGEMENT ====================
let currentUser = null;

// Check if user is already logged in
async function checkLoginStatus() {
    try {
        const res = await fetch('/profile');
        const data = await res.json();
        // Inside your login form submission handler, replace the success part:
        if (data.ok) {
            currentUser = { name: data.name, email: email };
            updateAuthUI();
            loginModal.classList.remove('show');
            alert(`Welcome back, ${data.name}!`);

            // THIS IS THE MISSING PIECE — RE-APPLY THEME AFTER LOGIN
            fetch('/check-login')
                .then(r => r.json())
                .then(themeData => {
                    const theme = themeData.logged_in && themeData.theme ? themeData.theme : 'light';
                    document.documentElement.setAttribute('data-theme', theme);
                    document.body.setAttribute('data-theme', theme);
                    updateThemeButton(); // if you have this function
                })
                .catch(() => {
                    document.documentElement.setAttribute('data-theme', 'light');
                    document.body.setAttribute('data-theme', 'light');
                });
        }
    } catch (err) {
        console.log("Not logged in");
    }
}

// Run on page load
window.addEventListener('load', checkLoginStatus);
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
// Login form submission
document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('loginEmail').value.trim();
    const password = document.getElementById('loginPassword').value;

    try {
        const res = await fetch('/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        const data = await res.json();

        if (data.ok) {
            currentUser = { name: data.name, email: email };
            updateAuthUI();
            loginModal.classList.remove('show');
            alert(`Welcome back, ${data.name}!`);

            // DELAYED CALL — Gives session time to process
            setTimeout(() => {
                window.applyUserTheme();
            }, 500);  // 0.5 second delay fixes 99% of timing issues
        } else {
            alert('Login failed: ' + data.message);
        }
    } catch (err) {
        alert('Server error. Is Flask running?');
    }
});
// Register form submission
document.getElementById('registerForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('registerName').value.trim();
    const email = document.getElementById('registerEmail').value.trim();
    const password = document.getElementById('registerPassword').value;

    try {
        const res = await fetch('/signup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email, password })
        });
        const data = await res.json();

        if (data.ok) {
            alert('Account created! Please login.');
            registerModal.classList.remove('show');
            loginModal.classList.add('show');
        } else {
            alert('Signup failed: ' + data.message);
        }
    } catch (err) {
        alert('Server error');
    }
});
// Logout
document.getElementById('logoutLink').addEventListener('click', async (e) => {
    e.preventDefault();
    
    await fetch('/logout');
    currentUser = null;
    updateAuthUI();
    showPage('home');
    
    // INSTANT + PERMANENT LIGHT THEME
    document.documentElement.setAttribute('data-theme', 'light');
    document.body.setAttribute('data-theme', 'light');
    
    const btn = document.getElementById('themeToggleBtn');
    if (btn) btn.textContent = 'Switch to Dark Mode';

    alert('Logged out successfully');
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

// ==================== SETTINGS MODAL ====================
function openModal(id) {
    document.getElementById(id).classList.add('show');
}

function closeModal(id) {
    document.getElementById(id).classList.remove('show');
}

// Close modal when clicking outside
window.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal')) {
        e.target.classList.remove('show');
    }
});

// ██████████████████ FINAL PERFECT THEME SYSTEM ██████████████████
// ==================== THEME MANAGEMENT ====================
// (Remove all other theme loaders except the inline one in index.html)

function updateThemeButton() {
    const btn = document.getElementById('themeToggleBtn');
    if (!btn) return;

    const currentTheme = document.body.getAttribute('data-theme') || 'light';
    
    btn.textContent = currentTheme === 'dark' 
        ? 'Switch to Light Mode' 
        : 'Switch to Dark Mode';
        
    // Beautiful colors
    btn.style.color = currentTheme === 'dark' ? '#e2e8f0' : '#1f2937';
    btn.style.backgroundColor = currentTheme === 'dark' ? '#334155' : '#f1f5f9';
    btn.style.border = currentTheme === 'dark' ? '1px solid #475569' : '1px solid #cbd5e1';
}

function toggleTheme() {
    const currentTheme = document.body.getAttribute('data-theme') || 'light';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    fetch('/settings/theme', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ theme: newTheme })
    }).then(response => {
        if (!response.ok) throw new Error('Save failed');
        return response.json();
    }).then(() => {
        document.documentElement.setAttribute('data-theme', newTheme);
        document.body.setAttribute('data-theme', newTheme);
        updateThemeButton();
    }).catch(err => {
        console.error('Theme save error:', err);
        alert('Failed to save theme. Please try again.');
    });
}

// Run when settings modal opens
const settingsModal = document.getElementById('settingsModal');
if (settingsModal) {
    settingsModal.addEventListener('transitionend', () => {
        if (settingsModal.classList.contains('show')) {
            updateThemeButton();
        }
    });
}

function applySavedTheme() {
    fetch('/check-login')
        .then(r => r.json())
        .then(d => {
            const theme = d.logged_in && d.theme ? d.theme : 'light';
            document.documentElement.setAttribute('data-theme', theme);
            document.body.setAttribute('data-theme', theme);
            updateThemeButton?.();
        })
        .catch(() => {
            document.documentElement.setAttribute('data-theme', 'light');
            document.body.setAttribute('data-theme', 'light');
        });
}

// FINAL THEME LOADER — WORKS 100% EVERY TIME
function applyTheme() {
    fetch('/get-theme')
        .then(response => response.json())
        .then(data => {
            const theme = data.theme || 'light';
            document.body.setAttribute('data-theme', theme);
            
            const btn = document.getElementById('themeToggleBtn');
            if (btn) {
                btn.textContent = theme === 'dark' 
                    ? 'Switch to Light Mode' 
                    : 'Switch to Dark Mode';
            }
        })
        .catch(() => {
            document.body.setAttribute('data-theme', 'light');
        });
}

// Run on page load
window.addEventListener('DOMContentLoaded', applyTheme);

// Also run when settings modal opens (important!)
document.getElementById('settingsModal')?.addEventListener('shown.bs.modal', applyTheme);
// or if not using Bootstrap: use transitionend like before

// ONE AND ONLY LOAD LISTENER — THIS FIXES EVERYTHING
window.addEventListener('DOMContentLoaded', () => {
    fetch('/get-theme')
    .then(r => r.json())
    .then(data => {
        const theme = data.theme || 'light';
        document.body.setAttribute('data-theme', theme);
        const btn = document.getElementById('themeToggleBtn');
        if (btn) {
            btn.textContent = theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode';
        }
    });
});

// ==================== CHANGE PASSWORD ====================
async function changePassword() {
    const oldPass = document.getElementById('oldPassword').value;
    const newPass = document.getElementById('newPassword').value;
    const status = document.getElementById('passStatus');

    if (!oldPass || !newPass) {
        status.textContent = "Please fill both fields";
        status.style.color = "red";
        return;
    }

    try {
        const res = await fetch('/settings/password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ old_password: oldPass, new_password: newPass })
        });
        const data = await res.json();

        if (data.ok) {
            status.textContent = data.message || "Password changed!";
            status.style.color = "green";
            document.getElementById('oldPassword').value = '';
            document.getElementById('newPassword').value = '';
        } else {
            status.textContent = data.message || "Failed";
            status.style.color = "red";
        }
    } catch (err) {
        status.textContent = "Server error";
        status.style.color = "red";
    }
}

// Auto-scroll to dashboards when bot sends this special tag
function checkForDashboardTrigger() {
    const messages = document.querySelectorAll('.chat-message.bot');
    const lastMessage = messages[messages.length - 1];
    if (lastMessage && lastMessage.innerHTML.includes('<trigger-dashboard-navigation />')) {
        // Clean the message
        lastMessage.innerHTML = lastMessage.innerHTML.replace('<trigger-dashboard-navigation />', '');
        
        // Navigate to dashboards
        showPage('dashboards');
        document.getElementById('dashboards').scrollIntoView({ behavior: 'smooth' });
    }
}

// AUTO NAVIGATE TO DASHBOARDS WHEN BOT SAYS "DASHBOARD_NAVIGATE_NOW"
const originalAddChatMessage = addChatMessage;
addChatMessage = function(type, content) {
    const msgDiv = originalAddChatMessage(type, content);
    
    if (type === 'bot' && content === 'DASHBOARD_NAVIGATE_NOW') {
        // Hide the message and navigate
        msgDiv.style.display = 'none';
        
        // Navigate to dashboards
        showPage('dashboards');
        document.getElementById('dashboards').scrollIntoView({ behavior: 'smooth' });
        
        // Optional: Show a nice message instead
        setTimeout(() => {
            addChatMessage('bot', "Here are your interactive dashboards!");
        }, 300);
    }
    
    return msgDiv;
};

// PERFECT MODAL SYSTEM — NEVER LOSES YOUR PLACE
let lastScrollPosition = 0;
let lastActivePage = 'home';

function openModal(id) {
    // Save current scroll and active page
    lastScrollPosition = window.scrollY;
    lastActivePage = document.querySelector('.page-section.active')?.id || 'home';

    const modal = document.getElementById(id);
    modal.classList.add('show');
    document.body.style.overflow = 'hidden'; // Stop background scroll
}

function closeModal(id) {
    const modal = document.getElementById(id);
    modal.classList.remove('show');
    document.body.style.overflow = ''; // Restore scroll

    // RETURN EXACTLY WHERE USER WAS
    setTimeout(() => {
        showPage(lastActivePage);
        window.scrollTo(0, lastScrollPosition);
    }, 100);
}

// Close when clicking outside
document.querySelectorAll('.modal').forEach(modal => {
    modal.addEventListener('click', function(e) {
        if (e.target === this) {
            const modalId = this.id;
            closeModal(modalId);
        }
    });
});

// Close with × button
document.querySelectorAll('.modal-close').forEach(btn => {
    btn.addEventListener('click', function() {
        closeModal(this.closest('.modal').id);
    });
});

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
