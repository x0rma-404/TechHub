const terminalInput = document.getElementById('terminalInput');
const outputArea = document.getElementById('outputArea');
const terminalBody = document.getElementById('terminalBody');
const terminal = document.getElementById('terminal');
const promptPath = document.querySelector('.prompt-path');

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Keep focus on input when clicking anywhere in terminal
if (terminal) {
    terminal.addEventListener('click', () => terminalInput.focus());
}

function formatLS(output) {
    if (!output) return '';
    return output.split(' ').filter(Boolean).map(item => {
        const safe = escapeHtml(item);
        if (item.endsWith('/')) {
            return `<span class="dir-link">${safe}</span>`;
        }
        return `<span class="file-link">${safe}</span>`;
    }).join('  ');
}

// Nano Editor Logic
const nanoEditor = document.getElementById('nanoEditor');
const nanoTextArea = document.getElementById('nanoTextArea');
const nanoFilename = document.getElementById('nanoFilename');
const promptLine = document.getElementById('promptLine');
let currentNanoFile = null;

function openNano(data) {
    currentNanoFile = data.full_path;
    nanoFilename.textContent = `File: ${data.filename}`;
    nanoTextArea.value = data.content;
    nanoEditor.classList.remove('hidden');
    promptLine.classList.add('hidden');
    nanoTextArea.focus();
}

async function saveNano() {
    if (!currentNanoFile) return;
    try {
        await fetch('/linux-sim/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                full_path: currentNanoFile,
                content: nanoTextArea.value
            })
        });
        showNanoMessage(`Saved ${currentNanoFile.split('/').pop()}`);
    } catch (error) {
        showNanoMessage('Error saving file');
    }
}

function closeNano() {
    nanoEditor.classList.add('hidden');
    promptLine.classList.remove('hidden');
    terminalInput.focus();
    currentNanoFile = null;
}

function showNanoMessage(msg) {
    const originalText = nanoFilename.textContent;
    nanoFilename.textContent = msg;
    setTimeout(() => {
        if (currentNanoFile) nanoFilename.textContent = originalText;
    }, 2000);
}

// Handle Nano Keyboard Shortcuts
nanoTextArea.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 'o') {
        e.preventDefault();
        saveNano();
    } else if (e.ctrlKey && e.key === 'x') {
        e.preventDefault();
        closeNano();
    }
});

terminalInput.addEventListener('keydown', async (e) => {
    if (e.key === 'Enter') {
        const command = terminalInput.value.trim();
        if (!command) return;

        // Add command to output
        const cmdLine = document.createElement('div');
        cmdLine.className = 'command-line';
        const currentPath = promptPath ? promptPath.textContent : '~';
        cmdLine.innerHTML = `<span class="prompt-symbol text-cyan-400">user@techhub</span>:<span class="prompt-path text-blue-400">${escapeHtml(currentPath)}</span>$ <span class="highlight-cmd text-green-400">${escapeHtml(command)}</span>`;
        outputArea.appendChild(cmdLine);

        terminalInput.value = '';

        // Handle local commands
        if (command.toLowerCase() === 'clear') {
            outputArea.innerHTML = '';
            return;
        }

        try {
            const response = await fetch('/linux-sim', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ command: command })
            });

            const data = await response.json();

            // Handle Nano Interactive Mode
            if (data.__nano_edit__) {
                openNano(data);
                return;
            }

            if (data.output === "__exit__") {
                const exitLine = document.createElement('div');
                exitLine.className = 'output-line';
                exitLine.textContent = 'Session closed. Redirecting...';
                outputArea.appendChild(exitLine);
                setTimeout(() => window.location.href = '/tools', 1000);
                return;
            }

            // Update prompt path
            if (data.path && promptPath) {
                promptPath.textContent = data.path === '/home/user' ? '~' : data.path.replace('/home/user', '~');
            }

            if (data.output) {
                const outputLine = document.createElement('div');
                outputLine.className = 'output-line';

                if (command.startsWith('ls')) {
                    outputLine.innerHTML = formatLS(data.output);
                } else if (data.output.toLowerCase().includes('error') || data.output.includes('not found')) {
                    outputLine.className = 'output-line error-text';
                    outputLine.textContent = data.output;
                } else {
                    outputLine.textContent = data.output;
                }
                outputArea.appendChild(outputLine);
            }

        } catch (error) {
            const errorLine = document.createElement('div');
            errorLine.className = 'output-line error-text';
            errorLine.textContent = 'Error: Could not connect to the simulator server.';
            outputArea.appendChild(errorLine);
        }

        // Scroll to bottom
        terminalBody.scrollTop = terminalBody.scrollHeight;
    }
});

// Initial focus
window.onload = () => {
    terminalInput.focus();
};
