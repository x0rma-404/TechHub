let editor;

window.onload = function () {
    editor = CodeMirror.fromTextArea(document.getElementById("code-editor"), {
        lineNumbers: true,
        mode: "go",
        theme: "material-darker",
        indentUnit: 4,
        matchBrackets: true,
        autoCloseBrackets: true
    });

    // Shortcuts
    document.addEventListener('keydown', function (e) {
        if (e.ctrlKey && e.key === 'Enter') {
            runGo();
        }
    });

    document.getElementById('runBtn').disabled = false;
};

function clearConsole() {
    document.getElementById("console").textContent = "";
}

async function runGo() {
    const runBtn = document.getElementById("runBtn");
    const statusBadge = document.getElementById("status-badge");
    const consoleElem = document.getElementById("console");
    const code = editor.getValue();

    runBtn.disabled = true;
    statusBadge.textContent = "Compiling...";
    statusBadge.className = "text-xs font-medium px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-400";
    consoleElem.textContent = "Sending to Godbolt Compiler...";

    try {
        const response = await fetch('/run-go', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code: code })
        });

        const data = await response.json();

        if (data.success) {
            consoleElem.textContent = data.output;
            statusBadge.textContent = "Success";
            statusBadge.className = "text-xs font-medium px-2 py-0.5 rounded-full bg-green-500/20 text-green-400";
        } else {
            consoleElem.textContent = "Error:\n" + (data.error || "Unknown error occurred");
            statusBadge.textContent = "Failed";
            statusBadge.className = "text-xs font-medium px-2 py-0.5 rounded-full bg-red-500/20 text-red-400";
        }
    } catch (err) {
        consoleElem.textContent = "Network Error: " + err.message;
        statusBadge.textContent = "Error";
        statusBadge.style.color = "#ff5252";
    } finally {
        runBtn.disabled = false;
    }
}
