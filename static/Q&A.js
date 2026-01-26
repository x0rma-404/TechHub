// Axtarış filtri
document.getElementById('searchInput').addEventListener('input', function(e) {
    const term = e.target.value.toLowerCase();
    const cards = document.querySelectorAll('.topic-card');

    cards.forEach(card => {
        const title = card.querySelector('h3').textContent.toLowerCase();
        card.style.display = title.includes(term) ? 'block' : 'none';
    });
});

// Kateqoriya keçidləri
function navigate(cat) {
    console.log("Seçildi: " + cat);
    // Real keçid üçün: window.location.href = cat + ".html";
    
    document.querySelectorAll('.cat-btn').forEach(b => b.classList.remove('active'));
    event.target.classList.add('active');
}