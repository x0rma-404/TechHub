let pyodide = null;
let editor = null;

const PYODIDE_INDEX_URL = 'https://cdn.jsdelivr.net/pyodide/v0.25.0/full/';

// CodeMirror başlatma
window.addEventListener('DOMContentLoaded', () => {
    const textarea = document.getElementById("code-editor");
    if (!textarea) {
        console.error('Code editor textarea not found');
        return;
    }

    editor = CodeMirror.fromTextArea(textarea, {
        lineNumbers: true,
        mode: "python",
        theme: "material-darker",
        indentUnit: 4,
        matchBrackets: true,
        autoCloseBrackets: true,
        lineWrapping: true,
        extraKeys: { 
            "Ctrl-Enter": runCode,
            "Cmd-Enter": runCode 
        }
    });

    // Set editor height to fill container
    editor.setSize(null, "100%");

    init_pyodide();
});

async function init_pyodide() {
    const loadingOverlay = document.getElementById('editor-loading');
    const runBtn = document.getElementById('runBtn');
    const statusBadge = document.getElementById('status-badge');

    if (!loadingOverlay || !runBtn) {
        console.error('Required elements not found');
        return;
    }

    try {
        pyodide = await loadPyodide({ indexURL: PYODIDE_INDEX_URL });
        
        // Smooth fade out
        loadingOverlay.style.transition = 'opacity 0.35s ease';
        loadingOverlay.style.opacity = '0';
        
        setTimeout(() => {
            loadingOverlay.classList.add('hidden');
            loadingOverlay.style.display = 'none';
        }, 350);
        
        runBtn.disabled = false;
        if (statusBadge) {
            statusBadge.textContent = "Ready";
            statusBadge.style.color = "#4caf50";
        }
    } catch (err) {
        console.error('Pyodide load error:', err);
        loadingOverlay.classList.remove('hidden');
        loadingOverlay.style.display = 'grid';
        loadingOverlay.style.opacity = '1';
        loadingOverlay.innerHTML = `
            <div class="text-center">
                <i class='bx bx-error text-4xl text-red-500 mb-3'></i>
                <p class='text-red-400 font-semibold'>Xəta: Pyodide yüklənə bilmədi</p>
                <p class='text-slate-400 text-sm mt-2'>İnternet əlaqənizi yoxlayın və səhifəni yeniləyin</p>
            </div>
        `;
        if (statusBadge) {
            statusBadge.textContent = "Error";
            statusBadge.style.color = "#ff5252";
        }
    }
}

function clearConsole() {
    const consoleElem = document.getElementById("console");
    if (consoleElem) {
        consoleElem.textContent = "Kodu icra etmək üçün 'Run' düyməsini sıxın...";
    }
    const statusBadge = document.getElementById('status-badge');
    if (statusBadge) {
        statusBadge.textContent = "Ready";
        statusBadge.style.color = "#4caf50";
    }
}

async function runCode() {
    if (!pyodide || !editor) {
        console.error('Pyodide or editor not initialized');
        return;
    }

    const code = editor.getValue().trim();
    const consoleElem = document.getElementById('console');
    const runBtn = document.getElementById('runBtn');
    const statusBadge = document.getElementById('status-badge');

    if (!consoleElem || !runBtn || !statusBadge) {
        console.error('Required elements not found');
        return;
    }

    if (!code) {
        consoleElem.textContent = "Xəta: Kod boşdur. Zəhmət olmasa kod daxil edin.";
        statusBadge.textContent = "Error";
        statusBadge.style.color = "#ff9800";
        return;
    }

    runBtn.disabled = true;
    statusBadge.textContent = "Running...";
    statusBadge.style.color = "#ff9800";

    consoleElem.textContent = "İcra edilir...\n";

    const indentedCode = code.split('\n').map(line => '    ' + line).join('\n');
    const wrappedCode = [
        'import sys',
        'from io import StringIO',
        '',
        'sys.stdout = StringIO()',
        'sys.stderr = StringIO()',
        '',
        'try:',
        indentedCode,
        'except Exception as e:',
        '    import traceback',
        '    traceback.print_exc(file=sys.stderr)',
        '',
        'output = sys.stdout.getvalue()',
        'error = sys.stderr.getvalue()',
        'output + error'
    ].join('\n');

    try {
        const result = await pyodide.runPythonAsync(wrappedCode);
        const text = result != null && result !== undefined ? String(result) : "";
        
        if (text.trim()) {
            consoleElem.textContent = text;
        } else {
            consoleElem.textContent = "✓ İcra edildi (Heç bir çıxış yoxdur)";
        }
        
        statusBadge.textContent = "Finished";
        statusBadge.style.color = "#4caf50";
    } catch (err) {
        const errMsg = err && (err.message || err.toString) 
            ? (err.message || err.toString()) 
            : String(err);
        consoleElem.textContent = "⚠ Xəta:\n" + errMsg;
        statusBadge.textContent = "Error";
        statusBadge.style.color = "#ff5252";
    } finally {
        runBtn.disabled = false;
        // Scroll to bottom of console
        consoleElem.scrollTop = consoleElem.scrollHeight;
    }
}