let currentFilter = 'categories';
let currentPage = 1;

// Q&A.js içindəki switchTab funksiyasını bu kodla əvəzləyin

function switchTab(tabName) {
    currentFilter = tabName;
    currentPage = 1;
    
    // Düymələrin rəngini/aktivliyini tənzimlə
    document.querySelectorAll('.cat-btn').forEach(btn => btn.classList.remove('active'));
    if(event && event.target) event.target.classList.add('active');

    const catDiv = document.getElementById('tab-categories'); // Statik kartlar (Python və s.)
    const listDiv = document.getElementById('dynamic-list');  // Dinamik suallar
    const loadArea = document.getElementById('load-more-area'); // Daha çox düyməsi

    if (tabName === 'categories') {
        // KATEQORİYALAR TABI: Kartları göstər, siyahını və düyməni gizlət
        catDiv.style.display = 'grid';
        listDiv.style.display = 'none';
        loadArea.classList.add('hidden'); // Kategoriyalarda "Daha çox" olmasın
    } else {
        // DİGƏR TABLAR (Populyar, Cavabsız, Yeni): Kartları gizlət, siyahını göstər
        catDiv.style.display = 'none'; 
        listDiv.style.display = 'flex';
        listDiv.innerHTML = '<p style="text-align:center; padding:20px;">Yüklənir...</p>';
        
        // API-dən sorğuları gətir
        loadQuestions(tabName, 1);
    }
}


function loadQuestions(filter, page) {
    fetch('/api/get_filtered_questions', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ filter: filter, page: page })
    })
    .then(res => res.json())
    .then(data => {
        const listDiv = document.getElementById('dynamic-list');
        if(page === 1) listDiv.innerHTML = '';

        data.data.forEach(q => {
            const div = document.createElement('div');
            div.className = 'q-list-item';
            div.style.cursor = 'pointer';
            div.onclick = () => location.href = `/Q&A/view/${q.id}`;
            
            div.innerHTML = `
                <div style="flex:1;">
                    <h3>${q.title}</h3>
                    <small>${q.author_name} • ${q.category}</small>
                </div>
            `;
            listDiv.appendChild(div);
        });

        const loadMoreBtn = document.getElementById('load-more-area');
        if(data.has_more) loadMoreBtn.classList.remove('hidden');
        else loadMoreBtn.classList.add('hidden');
    });
}