const terminalInput = document.getElementById('terminalInput');
const outputArea = document.getElementById('outputArea');
const terminalBody = document.getElementById('terminalBody');
const terminal = document.getElementById('terminal');
const promptPath = document.querySelector('.prompt-path');

// Keep focus on input
terminal.addEventListener('click', () => terminalInput.focus());

function formatLS(output) {
    if (!output) return '';
    return output.split(' ').map(item => {
        if (item.endsWith('/')) {
            return `<span class="dir-link">${item}</span>`;
        }
        return `<span class="file-link">${item}</span>`;
    }).join('  ');
}

terminalInput.addEventListener('keydown', async (e) => {
    if (e.key === 'Enter') {
        const command = terminalInput.value.trim();
        if (!command) return;

        // Add command to output
        const cmdLine = document.createElement('div');
        cmdLine.className = 'command-line';
        const currentPath = promptPath.textContent;
        cmdLine.innerHTML = `<span class="prompt-symbol">user@techhub</span>:<span class="prompt-path">${currentPath}</span>$ <span class="highlight-cmd">${command}</span>`;
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

            if (data.output === "__exit__") {
                const exitLine = document.createElement('div');
                exitLine.className = 'output-line';
                exitLine.textContent = 'Session closed. Redirecting...';
                outputArea.appendChild(exitLine);
                setTimeout(() => window.location.href = '/tools', 1000);
                return;
            }

            // Update prompt path
            if (data.path) {
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
