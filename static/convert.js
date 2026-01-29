const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const fileInfo = document.getElementById('file-info');
const displayFilename = document.getElementById('display-filename');
const displayFilesize = document.getElementById('display-filesize');
const convertBtn = document.getElementById('convert-btn');
const csvOptions = document.getElementById('csv-options');
const statusMsg = document.getElementById('status-msg');
const loader = document.getElementById('loader');
const btnText = document.getElementById('btn-text');

let selectedFile = null;

dropZone.addEventListener('click', () => {
    fileInput.click();
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFile(e.target.files[0]);
    }
});

['dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, e => {
        e.preventDefault();
        e.stopPropagation();
    });
});

dropZone.addEventListener('dragover', () => dropZone.classList.add('dragover'));
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop', (e) => {
    dropZone.classList.remove('dragover');
    if (e.dataTransfer.files.length > 0) {
        handleFile(e.dataTransfer.files[0]);
    }
});

function handleFile(file) {
    const ext = file.name.split('.').pop().toLowerCase();
    if (ext !== 'csv' && ext !== 'json') {
        showStatus('Please select a valid CSV or JSON file.', 'error');
        return;
    }

    selectedFile = file;
    displayFilename.textContent = file.name;
    displayFilesize.textContent = (file.size / 1024).toFixed(2) + ' KB';

    dropZone.style.display = 'none';
    fileInfo.style.display = 'flex';
    convertBtn.disabled = false;

    // Show delimiter options only for CSV conversion (CSV to JSON)
    csvOptions.style.display = ext === 'csv' ? 'block' : 'none';
    showStatus('');
}

function resetFile() {
    selectedFile = null;
    fileInput.value = '';
    dropZone.style.display = 'block';
    fileInfo.style.display = 'none';
    csvOptions.style.display = 'none';
    convertBtn.disabled = true;
    showStatus('');
}

function showStatus(msg, type = '') {
    statusMsg.textContent = msg;
    statusMsg.className = 'status-msg' + (type ? ' status-' + type : '');
}

async function handleConvert() {
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append('file', selectedFile);

    const delimiter = document.getElementById('delimiter').value;
    if (selectedFile.name.endsWith('.csv')) {
        formData.append('delimiter', delimiter === 'tab' ? '\t' : delimiter);
    }

    loader.style.display = 'block';
    btnText.textContent = 'Converting...';
    convertBtn.disabled = true;
    showStatus('');

    try {
        const response = await fetch('/convert', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.error || 'Conversion failed');
        }

        // Download logic
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        const targetExt = selectedFile.name.endsWith('.csv') ? 'json' : 'csv';
        const targetName = selectedFile.name.split('.').slice(0, -1).join('.') + '.' + targetExt;

        a.style.display = 'none';
        a.href = url;
        a.download = targetName;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);

        showStatus('File converted and downloaded successfully!', 'success');
    } catch (err) {
        showStatus(err.message, 'error');
    } finally {
        loader.style.display = 'none';
        btnText.textContent = 'Convert & Download';
        convertBtn.disabled = false;
    }
}
