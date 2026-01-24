const themeToggle = document.getElementById('theme-toggle');
const body = document.body;

// 1. Sayfa yüklendiğinde hafızadaki modu kontrol et
const savedTheme = localStorage.getItem('theme');
if (savedTheme === 'dark') {
    body.classList.add('dark-mode');
}

// 2. Butona tıklandığında modu değiştir
themeToggle.addEventListener('click', () => {

    body.classList.toggle('dark-mode');
    
    // 3. Modu hafızaya kaydet
    if (body.classList.contains('dark-mode')) {
        localStorage.setItem('theme', 'dark');
    } else {
        localStorage.setItem('theme', 'light');
    }

    
});

// --- LOGOUT (Minimal ekleme) ---
document.addEventListener('DOMContentLoaded', () => {
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
            e.preventDefault(); // linkin # davranışını engelle

            // Session/localStorage temizle
            localStorage.removeItem('auth');
            sessionStorage.removeItem('auth');

            // Bildirim
            alert('Çıkış yapıldı!');

            // Ana sayfaya yönlendir
            window.location.href = 'main-menu.html';
        });
    }
});
