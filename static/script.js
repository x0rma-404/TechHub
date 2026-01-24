const themeToggle = document.getElementById('theme-toggle');

// 1. Sayfa yüklendiğinde hafızadaki modu kontrol et (Tıklama öncesi durum)
const savedTheme = localStorage.getItem('theme');
if (savedTheme === 'dark') {
    document.documentElement.classList.add('dark-mode');
}

// 2. Butona tıklandığında modu değiştir
themeToggle.addEventListener('click', () => {
    // Artik body değil, html etiketine (documentElement) ekleyip çıkarıyoruz
    document.documentElement.classList.toggle('dark-mode');

    // 3. Modu hafızaya kaydet
    if (document.documentElement.classList.contains('dark-mode')) {
        localStorage.setItem('theme', 'dark');
    } else {
        localStorage.setItem('theme', 'light');
    }
});

// LOGOUT KISMI (Aynı kalabilir)
document.addEventListener('DOMContentLoaded', () => {
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            fetch('/logout').then(() => {
                window.location.href = '/';
            });
        });
    }
});