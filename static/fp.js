// Mode switching
let currentMode = 'decimal'; // 'decimal' or 'binary'

document.getElementById('modeDecimal').addEventListener('click', () => {
    currentMode = 'decimal';
    document.getElementById('modeDecimal').classList.add('bg-indigo-500', 'text-white');
    document.getElementById('modeDecimal').classList.remove('text-slate-400');
    document.getElementById('modeBinary').classList.remove('bg-indigo-500', 'text-white');
    document.getElementById('modeBinary').classList.add('text-slate-400');
    document.getElementById('decimalMode').classList.remove('hidden');
    document.getElementById('binaryMode').classList.add('hidden');
    document.getElementById('results').classList.add('hidden');
    document.getElementById('binaryResult').classList.add('hidden');
    document.getElementById('errorMessage').classList.add('hidden');
});

document.getElementById('modeBinary').addEventListener('click', () => {
    currentMode = 'binary';
    document.getElementById('modeBinary').classList.add('bg-indigo-500', 'text-white');
    document.getElementById('modeBinary').classList.remove('text-slate-400');
    document.getElementById('modeDecimal').classList.remove('bg-indigo-500', 'text-white');
    document.getElementById('modeDecimal').classList.add('text-slate-400');
    document.getElementById('binaryMode').classList.remove('hidden');
    document.getElementById('decimalMode').classList.add('hidden');
    document.getElementById('results').classList.add('hidden');
    document.getElementById('binaryResult').classList.add('hidden');
    document.getElementById('errorMessage').classList.add('hidden');
});

function setExample(value) {
    currentMode = 'decimal';
    document.getElementById('modeDecimal').click();
    document.getElementById('floatingInput').value = value;
}

function setBinaryExample(value) {
    currentMode = 'binary';
    document.getElementById('modeBinary').click();
    document.getElementById('binaryInput2').value = value;
}

// Decimal to Binary conversion
document.getElementById('evaluateBtn').addEventListener('click', async () => {
    const input = document.getElementById('floatingInput').value.trim();
    const resultsDiv = document.getElementById('results');
    const loadingDiv = document.getElementById('loading');
    const simplifiedText = document.getElementById('simplifiedText');
    const errorMessage = document.getElementById('errorMessage');
    const detailsSection = document.getElementById('detailsSection');
    const binaryResult = document.getElementById('binaryResult');

    binaryResult.classList.add('hidden');

    if (!input) {
        errorMessage.querySelector('p').textContent = 'Please enter a number';
        errorMessage.classList.remove('hidden');
        return;
    }

    // Show loading
    loadingDiv.classList.remove('hidden');
    resultsDiv.classList.add('hidden');
    errorMessage.classList.add('hidden');

    try {
        const response = await fetch('/api/evaluate-floating', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ number: input })
        });

        const data = await response.json();

        if (data.success) {
            // Display binary with colors
            const binaryDisplay = data.binary || data.raw_binary || 'N/A';

            // Parse and color the binary
            let binaryClean = binaryDisplay.replace(/\s/g, ''); // Remove spaces
            if (binaryClean.length === 8) {
                // Split into: sign (1), exponent (3), mantissa (4)
                const sign = binaryClean[0];
                const exponent = binaryClean.substring(1, 4);
                const mantissa = binaryClean.substring(4, 8);

                simplifiedText.innerHTML =
                    `<span style="color: #f87171; font-weight: bold; font-size: 1.5em;">${sign}</span>` +
                    `<span style="color: #64748b; margin: 0 4px;"> </span>` +
                    `<span style="color: #4ade80; font-weight: bold; font-size: 1.5em;">${exponent}</span>` +
                    `<span style="color: #64748b; margin: 0 4px;"> </span>` +
                    `<span style="color: #60a5fa; font-weight: bold; font-size: 1.5em;">${mantissa}</span>`;
            } else {
                simplifiedText.innerHTML = `<span style="color: #a5b4fc;">${binaryDisplay}</span>`;
            }

            // Check if we have detailed data (new format)
            if (data.details) {
                // Set binary input for reverse conversion
                document.getElementById('binaryInput').value = data.raw_binary || data.binary.replace(/\s/g, '');

                // Display breakdown
                document.getElementById('signBit').textContent = data.details.sign === 'Positive' ? '0' : '1';
                document.getElementById('signMeaning').textContent = data.details.sign;
                document.getElementById('exponentBits').textContent = data.details.exponent_bits;
                document.getElementById('exponentValue').textContent = `Value: ${data.details.exponent_value} (biased: ${parseInt(data.details.exponent_bits, 2)})`;
                document.getElementById('mantissaBits').textContent = data.details.mantissa;

                // Display details
                document.getElementById('decimalBinary').textContent = data.details.decimal_binary;
                document.getElementById('actualExponent').textContent = data.details.exponent_value;

                // Show details section
                detailsSection.classList.remove('hidden');
            } else {
                // Old format - hide details section
                detailsSection.classList.add('hidden');
            }

            resultsDiv.classList.remove('hidden');
        } else {
            errorMessage.querySelector('p').textContent = data.message || 'Conversion failed';
            errorMessage.classList.remove('hidden');
        }
    } catch (error) {
        errorMessage.querySelector('p').textContent = 'Error: ' + error.message;
        errorMessage.classList.remove('hidden');
    } finally {
        loadingDiv.classList.add('hidden');
    }
});

// Binary to Decimal conversion (main mode)
document.getElementById('reverseBtn2').addEventListener('click', async () => {
    const binary = document.getElementById('binaryInput2').value.trim();
    const binaryResult = document.getElementById('binaryResult');
    const decimalValue = document.getElementById('decimalValue');
    const errorMessage = document.getElementById('errorMessage');
    const loadingDiv = document.getElementById('loading');
    const resultsDiv = document.getElementById('results');

    resultsDiv.classList.add('hidden');

    if (!binary) {
        errorMessage.querySelector('p').textContent = 'Please enter an 8-bit binary number';
        errorMessage.classList.remove('hidden');
        return;
    }

    errorMessage.classList.add('hidden');
    loadingDiv.classList.remove('hidden');
    binaryResult.classList.add('hidden');

    try {
        const response = await fetch('/api/floating-to-decimal', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ binary: binary })
        });

        const data = await response.json();

        if (data.success) {
            decimalValue.textContent = data.decimal;

            // Display input binary with colors
            const binaryClean = binary.replace(/\s/g, '');
            if (binaryClean.length === 8) {
                const sign = binaryClean[0];
                const exponent = binaryClean.substring(1, 4);
                const mantissa = binaryClean.substring(4, 8);

                document.getElementById('inputBinaryColored').innerHTML =
                    `<span style="color: #f87171; font-weight: bold;">${sign}</span>` +
                    `<span style="color: #64748b; margin: 0 4px;"> </span>` +
                    `<span style="color: #4ade80; font-weight: bold;">${exponent}</span>` +
                    `<span style="color: #64748b; margin: 0 4px;"> </span>` +
                    `<span style="color: #60a5fa; font-weight: bold;">${mantissa}</span>`;
            }

            binaryResult.classList.remove('hidden');
        } else {
            errorMessage.querySelector('p').textContent = data.message || 'Conversion failed';
            errorMessage.classList.remove('hidden');
        }
    } catch (error) {
        errorMessage.querySelector('p').textContent = 'Error: ' + error.message;
        errorMessage.classList.remove('hidden');
    } finally {
        loadingDiv.classList.add('hidden');
    }
});

// Reverse conversion in details section
document.getElementById('reverseBtn').addEventListener('click', async () => {
    const binary = document.getElementById('binaryInput').value.trim();
    const reverseResult = document.getElementById('reverseResult');
    const errorMessage = document.getElementById('errorMessage');

    if (!binary) {
        errorMessage.querySelector('p').textContent = 'Please enter an 8-bit binary number';
        errorMessage.classList.remove('hidden');
        return;
    }

    errorMessage.classList.add('hidden');

    try {
        const response = await fetch('/api/floating-to-decimal', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ binary: binary })
        });

        const data = await response.json();

        if (data.success) {
            document.getElementById('reverseDecimal').textContent = data.decimal;
            reverseResult.classList.remove('hidden');
        } else {
            errorMessage.querySelector('p').textContent = data.message || 'Reverse conversion failed';
            errorMessage.classList.remove('hidden');
        }
    } catch (error) {
        errorMessage.querySelector('p').textContent = 'Error: ' + error.message;
        errorMessage.classList.remove('hidden');
    }
});

// Allow Enter key to trigger conversion
document.getElementById('floatingInput').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        document.getElementById('evaluateBtn').click();
    }
});

document.getElementById('binaryInput2').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        document.getElementById('reverseBtn2').click();
    }
});

document.getElementById('binaryInput').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        document.getElementById('reverseBtn').click();
    }
});
