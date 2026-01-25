    document.getElementById('evaluateBtn').addEventListener('click', async () => {
        const expression = document.getElementById('logicExpression').value;
        if (!expression) return;

        const resultsDiv = document.getElementById('results');
        const errorDiv = document.getElementById('errorMessage');
        const loadingDiv = document.getElementById('loading');

        resultsDiv.style.display = 'none';
        errorDiv.style.display = 'none';
        loadingDiv.style.display = 'block';

        try {
            const response = await fetch('/api/logic/evaluate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ expression })
            });

            const data = await response.json();

            if (data.success) {
                document.getElementById('simplifiedText').textContent = data.simplified;

                const tableHead = document.getElementById('tableHead');
                const tableBody = document.getElementById('tableBody');

                tableHead.innerHTML = '<tr>' + data.headers.map(h => `<th>${h}</th>`).join('') + '</tr>';
                tableBody.innerHTML = data.rows.map(row =>
                    `<tr>${row.map(val => `<td style="color: ${val ? '#2ecc71' : '#e74c3c'}">${val}</td>`).join('')}</tr>`
                ).join('');

                resultsDiv.style.display = 'block';
            } else {
                errorDiv.textContent = data.message;
                errorDiv.style.display = 'block';
            }
        } catch (error) {
            errorDiv.textContent = 'Server ilə əlaqə kəsildi.';
            errorDiv.style.display = 'block';
        } finally {
            loadingDiv.style.display = 'none';
        }
    });

    // Enter key support
    document.getElementById('logicExpression').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            document.getElementById('evaluateBtn').click();
        }
    });