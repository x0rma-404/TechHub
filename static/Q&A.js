function filterTopics() {
    const term = document.getElementById('searchInput').value.toLowerCase();
    // Həm ana səhifədəki kartları, həm də sual siyahısını eyni vaxtda idarə edir
    const items = document.querySelectorAll('.topic-card, .q-list-item');

    items.forEach(item => {
        const title = item.querySelector('h3').textContent.toLowerCase();
        item.style.display = title.includes(term) ? (item.classList.contains('q-list-item') ? 'flex' : 'block') : 'none';
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const sendBtn = document.getElementById('sendReply');
    if (sendBtn) {
        sendBtn.addEventListener('click', () => {
            alert("Cavab göndərildi!");
            document.getElementById('replyText').value = "";
        });
    }
});