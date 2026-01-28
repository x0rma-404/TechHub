var quill;
// Default olaraq əsas suala cavab veririk
let replyContext = { id: null, name: '{{ question.author_name }}' };

document.addEventListener('DOMContentLoaded', function () {
    // Point 4: Şrift ölçüsü (size) əlavə olundu
    var toolbarOptions = [
        [{ 'size': ['small', false, 'large', 'huge'] }], // Şrift ölçüləri
        ['bold', 'italic', 'underline', 'strike'],
        [{ 'list': 'ordered' }, { 'list': 'bullet' }],
        [{ 'color': [] }, { 'background': [] }],
        ['link', 'image', 'code-block']
    ];

    quill = new Quill('#editor-container', {
        modules: { toolbar: toolbarOptions },
        theme: 'snow',
        placeholder: 'Cavabınızı bura yazın...'
    });

    // Point 3: Səhifə açılan kimi default "Suala cavab verilir" göstər
    updateReplyBadge();

    // Şəkil yükləmə handler
    quill.getModule('toolbar').addHandler('image', selectLocalImage);
});

// Vizual göstərici funksiyası
function updateReplyBadge() {
    const tagArea = document.getElementById('reply-tag-area');
    const nameSpan = document.getElementById('reply-target-name');

    tagArea.style.display = 'block'; // Həmişə görünür

    if (replyContext.id === null) {
        // Əsas sual
        nameSpan.innerHTML = `Sualın özünə cavab verilir: <strong>${replyContext.name}</strong>`;
        // Ləğv et düyməsini gizlədə bilərik, çünki bu default haldır
        document.querySelector('.fa-times').style.display = 'none';
    } else {
        // Konkret şəxs
        nameSpan.innerHTML = `Cavab verilir: <strong>${replyContext.name}</strong>`;
        document.querySelector('.fa-times').style.display = 'inline-block';
    }
}

function setReply(id, name, type) {
    // Editora sürüşdür
    document.querySelector('.reply-section').scrollIntoView({ behavior: 'smooth' });
    quill.focus();

    if (type === 'main') {
        cancelReply();
        return;
    }

    replyContext = { id: id, name: name };
    updateReplyBadge();
}

function cancelReply() {
    // Sıfırla (Main suala qayıt)
    replyContext = { id: null, name: '{{ question.author_name }}' };
    updateReplyBadge();
}

// Göndərmə funksiyası
function submitAnswer(questionId) {
    const content = quill.root.innerHTML;
    const plainText = quill.getText().trim();

    if (!plainText && !content.includes('<img')) {
        alert("Boş cavab göndərmək olmaz!");
        return;
    }

    fetch('/api/add_answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            question_id: questionId,
            text: content,
            reply_to: replyContext.id ? replyContext : null // Backend məntiqinə uyğun
        })
    })
        .then(res => res.json())
        .then(data => {
            if (data.success) location.reload();
            else alert("Xəta baş verdi.");
        });
}

// Şəkil funksiyaları olduğu kimi qalır...
function selectLocalImage() {
    const input = document.createElement('input');
    input.setAttribute('type', 'file');
    input.setAttribute('accept', 'image/*');
    input.click();
    input.onchange = () => {
        const file = input.files[0];
        if (/^image\//.test(file.type)) saveToServer(file);
    };
}

function saveToServer(file) {
    const fd = new FormData();
    fd.append('image', file);
    fetch('/api/upload_image', { method: 'POST', body: fd })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const range = quill.getSelection();
                quill.insertEmbed(range.index, 'image', data.url);
            }
        });
}

// Silmə funksiyası (olduğu kimi)
function deleteAnswer(qId, ansId) {
    if (!confirm("Silmək istəyirsiniz?")) return;
    fetch('/api/delete_answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question_id: qId, answer_id: ansId })
    })
        .then(res => res.json())
        .then(data => {
            if (data.success) document.getElementById('ans-' + ansId).remove();
        });
}
