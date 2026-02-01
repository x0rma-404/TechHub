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

// Real-time symbol replacement
document.getElementById('logicExpression').addEventListener('input', function (e) {
    const input = this;
    let val = input.value;
    const start = input.selectionStart;

    // Logical Replacements
    const replacements = [
        { search: '<=>', replace: '↔' },
        { search: '->', replace: '→' },
        { search: '^', replace: '⊕' },
        // Precomposed characters for common NOT variables (A-Z) to avoid sliding
        { regex: /!A/g, replace: 'Ā' }, { regex: /!B/g, replace: 'B̄' },
        { regex: /!C/g, replace: 'C̄' }, { regex: /!D/g, replace: 'D̄' },
        { regex: /!E/g, replace: 'Ē' }, { regex: /!F/g, replace: 'F̄' },
        { regex: /!G/g, replace: 'Ḡ' }, { regex: /!H/g, replace: 'H̄' },
        { regex: /!I/g, replace: 'Ī' }, { regex: /!J/g, replace: 'J̄' },
        { regex: /!K/g, replace: 'K̄' }, { regex: /!L/g, replace: 'L̄' },
        { regex: /!M/g, replace: 'M̄' }, { regex: /!N/g, replace: 'N̄' },
        { regex: /!O/g, replace: 'Ō' }, { regex: /!P/g, replace: 'P̄' },
        { regex: /!Q/g, replace: 'Q̄' }, { regex: /!R/g, replace: 'R̄' },
        { regex: /!S/g, replace: 'S̄' }, { regex: /!T/g, replace: 'T̄' },
        { regex: /!U/g, replace: 'Ū' }, { regex: /!V/g, replace: 'V̄' },
        { regex: /!W/g, replace: 'W̄' }, { regex: /!X/g, replace: 'X̄' },
        { regex: /!Y/g, replace: 'Ȳ' }, { regex: /!Z/g, replace: 'Z̄' },
        { regex: /!a/g, replace: 'ā' }, { regex: /!b/g, replace: 'b̄' },
        { regex: /!c/g, replace: 'c̄' }, { regex: /!d/g, replace: 'd̄' },
        { regex: /!e/g, replace: 'ē' },
        // Fallback for others with combining overline
        { regex: /!([a-zA-Z0-9])/g, replace: '$1\u0304' }
    ];

    let newVal = val;
    replacements.forEach(r => {
        if (r.regex) {
            newVal = newVal.replace(r.regex, r.replace);
        } else {
            newVal = newVal.split(r.search).join(r.replace);
        }
    });

    if (newVal !== val) {
        const diff = val.length - newVal.length;
        input.value = newVal;
        // Adjust cursor position
        input.selectionStart = input.selectionEnd = start - diff;
    }
});