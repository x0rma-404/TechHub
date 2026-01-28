let pyodide = null;
let editor = null;

// CodeMirror başlatma
window.onload = () => {
    editor = CodeMirror.fromTextArea(document.getElementById("code-editor"), {
        lineNumbers: true,
        mode: "python",
        theme: "material-darker",
        indentUnit: 4,
        matchBrackets: true,
        autoCloseBrackets: true,
        lineWrapping: true,
        extraKeys: { "Ctrl-Enter": runCode }
    });

    init_pyodide();
};

async function init_pyodide() {
    const loadingOverlay = document.getElementById('editor-loading');
    const runBtn = document.getElementById('runBtn');

    try {
        pyodide = await loadPyodide();
        loadingOverlay.style.opacity = '0';
        setTimeout(() => loadingOverlay.style.display = 'none', 300);
        runBtn.disabled = false;
    } catch (err) {
        console.error(err);
        loadingOverlay.innerHTML = "<p style='color:#ff5252'>Xəta baş verdi. Yenidən cəhd edin.</p>";
    }
}

function clearConsole() {
    document.getElementById("console").textContent = "";
}

async function runCode() {
    if (!pyodide) return;

    const code = editor.getValue();
    const consoleElem = document.getElementById('console');
    const runBtn = document.getElementById('runBtn');
    const statusBadge = document.getElementById('status-badge');

    runBtn.disabled = true;
    statusBadge.textContent = "Running...";
    statusBadge.style.color = "#ff9800";

    consoleElem.textContent = "";

    const wrappedCode = `
import sys
from io import StringIO

# stdout və stderr-i tutmaq üçün
sys.stdout = StringIO()
sys.stderr = StringIO()

try:
${code.split('\n').map(line => '    ' + line).join('\n')}
except Exception as e:
    print(e, file=sys.stderr)

output = sys.stdout.getvalue()
error = sys.stderr.getvalue()
output + error
`;

    try {
        const result = await pyodide.runPythonAsync(wrappedCode);
        consoleElem.textContent = result || "İcra edildi (Heç bir çıxış yoxdur)";
        statusBadge.textContent = "Finished";
        statusBadge.style.color = "#4caf50";
    } catch (err) {
        consoleElem.textContent = err;
        statusBadge.textContent = "Error";
        statusBadge.style.color = "#ff5252";
    } finally {
        runBtn.disabled = false;
    }
}