// Search filtering function
function filterTopics() {
    const term = document.getElementById('searchInput').value.toLowerCase();
    const cards = document.querySelectorAll('.topic-card');

    cards.forEach(card => {
        const title = card.querySelector('h3').textContent.toLowerCase();
        const desc = card.querySelector('p').textContent.toLowerCase();
        card.style.display = (title.includes(term) || desc.includes(term)) ? 'block' : 'none';
    });
}

// Category filtering and UI logic
document.addEventListener('DOMContentLoaded', () => {
    const catButtons = document.querySelectorAll('.cat-btn');

    catButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            // Only handle if it's a button with data-filter (exclude anchor buttons)
            if (e.target.tagName === 'A') return;

            const filter = e.target.getAttribute('data-filter');
            if (!filter) return;

            // Update UI
            catButtons.forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');

            // Filtering logic (placeholder: for now we just show/hide cards based on content)
            console.log("Filtering by category:", filter);
            // In a real app, this would fetch data or filter existing cards more specifically
        });
    });
});