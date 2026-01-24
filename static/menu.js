/**
 * TechHub - Modern SPA Logic
 * Fix: Veri kalıcılığı ve otomatik yedekleme senkronizasyonu
 */

// --- 1. Utilities ---
const qs = (sel, el = document) => el.querySelector(sel);
const qsa = (sel, el = document) => [...el.querySelectorAll(sel)];

const toast = (msg, type = 'info') => {
    const t = document.createElement('div');
    t.className = 'toast-item fade-in';
    t.innerHTML = `
      <div class="flex items-start gap-3">
        <span class="mt-0.5 h-2.5 w-2.5 rounded-full ${type === 'success' ? 'bg-emerald-400' : type === 'error' ? 'bg-rose-400' : 'bg-indigo-400'}"></span>
        <div class="text-sm">${msg}</div>
      </div>`;
    const wrap = qs('#toaster');
    if (wrap) {
        wrap.appendChild(t);
        setTimeout(() => { t.style.opacity = '0'; t.style.transform = 'translateY(6px)'; }, 3000);
        setTimeout(() => t.remove(), 3500);
    }
};

// --- 2. Storage & Backup ---
// NOTE: "users" are now managed by backend. We only keep a session flag or user info cache.
const storage = {
    // Only used for caching user info for UI to avoid flicker, but mainly rely on API
    getUser() {
        const data = localStorage.getItem('user_cache');
        try { return data ? JSON.parse(data) : null; } catch (e) { return null; }
    },
    setUser(user) {
        localStorage.setItem('user_cache', JSON.stringify(user));
    },
    clearSession() {
        localStorage.removeItem('user_cache');
        sessionStorage.removeItem('user_cache'); // Just in case
    }
};

// JSON İndirme Fonksiyonu (Backend verisi indirmeli, fakat şimdilik devre dışı bırakıyoruz veya sadece frontend önbelleği indiriyoruz)
// Backend'den indirmek için ayrı bir endpoint gerekebilir.
function downloadUsersAsJson() {
    // Demo amaçlı: sadece cache'i indirir ya da boş verir.
    // Gerçek implementasyonda backend'den '/api/export' gibi bir yer çağrılmalı.
    toast('Bu özellik backend modunda devre dışı.', 'info');
}

// --- 3. Authentication ---
const auth = {
    // Check local cache first, but async check backend is better. 
    // For sync UI rendering we use cache, then validate.
    current() { return storage.getUser()?.email || null; },
    getUser() { return storage.getUser(); },

    // Async check to sync session
    async checkSession() {
        try {
            const res = await fetch('/api/user');
            const user = await res.json();
            if (user) {
                storage.setUser(user);
                return user;
            } else {
                storage.clearSession();
                return null;
            }
        } catch (e) {
            console.error(e);
            return null;
        }
    },

    async register({ name, email, password }) {
        const res = await fetch('/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email, password })
        });
        const data = await res.json();

        if (!res.ok) throw new Error(data.message || 'Kayıt başarısız');

        storage.setUser(data.user);
        return data.user;
    },

    async login({ email, password }) {
        const res = await fetch('/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        const data = await res.json();

        if (!res.ok) throw new Error(data.message || 'Giriş başarısız');

        storage.setUser(data.user);
        return data.user;
    },

    async logout() {
        await fetch('/logout');
        storage.clearSession();
        location.hash = '#/home';
        updateHeader();
    }
};

// --- 4. UI & Routing ---
function updateHeader() {
    // We might need to wait for session check? 
    // For now use cache to be fast.
    const user = auth.getUser();
    const btnText = qs('#headerPrimaryBtnText');
    const logoutBtn = qs('#logoutBtn');
    const logoutBtn2 = qs('#logoutBtn2');

    if (user) {
        if (btnText) btnText.textContent = 'Profilim';
        if (logoutBtn) logoutBtn.classList.remove('hidden');
        qs('#headerPrimaryBtn').onclick = () => location.hash = '#/profile';
        if (logoutBtn) logoutBtn.onclick = () => auth.logout();
        if (logoutBtn2) logoutBtn2.onclick = () => auth.logout();
    } else {
        if (btnText) btnText.textContent = 'Başla';
        if (logoutBtn) logoutBtn.classList.add('hidden');
        qs('#headerPrimaryBtn').onclick = () => location.hash = '#/auth';
    }
}

function showView(id) {
    qsa('main section').forEach(s => s.classList.add('hidden'));
    const view = qs('#' + id);
    if (view) view.classList.remove('hidden');
    updateHeader();
}

const routes = {
    home: () => showView('view-home'),
    auth: () => showView('view-auth'),
    profile: async () => {
        // Double check session before showing profile
        if (!auth.current()) {
            // Try explicit check
            const user = await auth.checkSession();
            if (!user) {
                location.hash = '#/auth';
                return;
            }
        }
        showView('view-profile');
        renderProfile();
    }
};

async function navigate() {
    const path = location.hash.slice(2) || 'home';
    if (routes[path]) {
        await routes[path]();
    }
}

// --- 5. Form Bindings ---
function bindAuthUI() {
    const formLogin = qs('#form-login');
    const formRegister = qs('#form-register');

    // Tab geçişleri
    qs('#tab-login').onclick = () => {
        qs('#form-login').classList.remove('hidden');
        qs('#form-register').classList.add('hidden');
        qs('#tab-login').classList.add('tab-active');
        qs('#tab-register').classList.remove('tab-active');
    };
    qs('#tab-register').onclick = () => {
        qs('#form-register').classList.remove('hidden');
        qs('#form-login').classList.add('hidden');
        qs('#tab-register').classList.add('tab-active');
        qs('#tab-login').classList.remove('tab-active');
    };

    formLogin.onsubmit = async (e) => {
        e.preventDefault();
        try {
            await auth.login({
                email: qs('#loginEmail').value,
                password: qs('#loginPassword').value
            });
            toast('Hoş geldiniz!', 'success');
            setTimeout(() => window.location.href = '/dashboard', 1000);
        } catch (e) { toast(e.message, 'error'); }
    };

    formRegister.onsubmit = async (e) => {
        e.preventDefault();
        if (qs('#regPassword').value !== qs('#regPassword2').value) {
            return toast('Şifreler eşleşmiyor!', 'error');
        }
        try {
            await auth.register({
                name: qs('#regName').value,
                email: qs('#regEmail').value,
                password: qs('#regPassword').value
            });
            toast('Kayıt başarılı!', 'success');

            setTimeout(() => window.location.href = '/dashboard', 1500);
        } catch (e) { toast(e.message, 'error'); }
    };
}

function renderProfile() {
    const user = auth.getUser();
    if (!user) return;
    qs('#profileName').textContent = user.name;
    qs('#profileEmail').textContent = user.email;
    if (qs('#avatar')) qs('#avatar').textContent = user.name[0].toUpperCase();
    if (qs('#lastLogin')) qs('#lastLogin').textContent = new Date(user.lastLogin).toLocaleTimeString();

    // Calculate days since reg (mock logic or real)
    const diff = Date.now() - (user.createdAt || Date.now());
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    if (qs('#daysCount')) qs('#daysCount').textContent = days;
    if (qs('#memberSince')) qs('#memberSince').textContent = 'Üyelik: ' + new Date(user.createdAt || Date.now()).toLocaleDateString();
}

// --- Init ---
document.addEventListener('DOMContentLoaded', async () => {
    // Initial session check
    await auth.checkSession();

    bindAuthUI();
    window.onhashchange = navigate;
    navigate();
});
