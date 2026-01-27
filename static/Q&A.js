function filterTopics() {
    const term = document.getElementById('searchInput').value.toLowerCase();
    // Həm ana səhifədəki kartları, həm də sual siyahısını eyni vaxtda idarə edir
    const items = document.querySelectorAll('.topic-card, .q-list-item');

    items.forEach(item => {
        const title = item.querySelector('h3').textContent.toLowerCase();
        item.style.display = title.includes(term) ? (item.classList.contains('q-list-item') ? 'flex' : 'block') : 'none';
    });
}

// Q&A.js içində sendReply hadisəsini yenilə
document.addEventListener('DOMContentLoaded', () => {
    const sendBtn = document.getElementById('sendReply');
    if (sendBtn) {
        sendBtn.addEventListener('click', () => {
            const text = document.getElementById('replyText').value;
            
            fetch('/api/add_answer', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    category: 'python', // Hansı bölmədə olduğunu dinamik almalısan
                    question_id: 1, 
                    text: text
                })
            })
            .then(res => res.json())
            .then(data => {
                if(data.success) {
                    alert(`Cavab qəbul edildi! Yeni rolun: ${data.new_role}`);
                    location.reload(); // Səhifəni yenilə ki, yeni rol görünsün
                }
            });
        });
    }
});

function openQuestionModal() {
    document.getElementById('questionModal').style.display = 'block';
}

function closeQuestionModal() {
    document.getElementById('questionModal').style.display = 'none';
}

function submitQuestion(category) {
    const title = document.getElementById('newTitle').value;
    const content = document.getElementById('newContent').value;

    if(!title || !content) return alert("Xanaları doldurun!");

    fetch('/api/new_question', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            title: title,
            content: content,
            category: category,
            tags: [] 
        })
    })
    .then(res => res.json())
    .then(data => {
        if(data.success) {
            alert("Sual yaradıldı!");
            location.reload();
        }
    });
}