// static/matrix.js

class MatrixCalculator {
    constructor() {
        this.matrixA = [];
        this.matrixB = [];
        this.currentOperation = null;
        this.init();
    }

    init() {
        // Generate buttons
        document.getElementById('generateA').addEventListener('click', () => this.generateMatrix('A'));
        document.getElementById('generateB').addEventListener('click', () => this.generateMatrix('B'));

        // Operation buttons
        document.querySelectorAll('.operation-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const operation = e.target.dataset.op;
                this.handleOperation(operation);
            });
        });

        // Scalar operations
        document.getElementById('applyScalar').addEventListener('click', () => this.applyScalar());
        document.getElementById('cancelScalar').addEventListener('click', () => this.hideScalarInput());

        // Power operations
        document.getElementById('applyPower').addEventListener('click', () => this.applyPower());
        document.getElementById('cancelPower').addEventListener('click', () => this.hidePowerInput());

        // Example buttons
        document.querySelectorAll('.example-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const example = e.target.dataset.example;
                this.loadExample(example);
            });
        });

        // Copy result
        document.getElementById('copyResult').addEventListener('click', () => this.copyResult());

        // Initialize with 2x2 matrices
        this.generateMatrix('A');
        this.generateMatrix('B');
    }

    generateMatrix(which) {
        const rows = parseInt(document.getElementById(`rows${which}`).value);
        const cols = parseInt(document.getElementById(`cols${which}`).value);

        if (rows < 1 || rows > 10 || cols < 1 || cols > 10) {
            this.showError('Sətir və sütun sayı 1-10 arasında olmalıdır');
            return;
        }

        const container = document.getElementById(`matrix${which}`);
        container.innerHTML = '';

        const matrix = [];
        for (let i = 0; i < rows; i++) {
            const row = [];
            const rowDiv = document.createElement('div');
            rowDiv.className = 'matrix-row';

            for (let j = 0; j < cols; j++) {
                const input = document.createElement('input');
                input.type = 'number';
                input.className = 'matrix-cell';
                input.value = '0';
                input.step = '0.1';
                input.dataset.row = i;
                input.dataset.col = j;

                input.addEventListener('input', (e) => {
                    this[`matrix${which}`][i][j] = parseFloat(e.target.value) || 0;
                });

                rowDiv.appendChild(input);
                row.push(0);
            }

            container.appendChild(rowDiv);
            matrix.push(row);
        }

        this[`matrix${which}`] = matrix;
        this.hideError();
    }

    readMatrix(which) {
        const container = document.getElementById(`matrix${which}`);
        const rows = container.querySelectorAll('.matrix-row');
        const matrix = [];

        rows.forEach(row => {
            const cells = row.querySelectorAll('.matrix-cell');
            const rowData = [];
            cells.forEach(cell => {
                rowData.push(parseFloat(cell.value) || 0);
            });
            matrix.push(rowData);
        });

        return matrix;
    }

    handleOperation(operation) {
        this.hideError();
        this.hideResults();

        const matrixA = this.readMatrix('A');
        const matrixB = this.readMatrix('B');

        if (operation === 'scalar-a') {
            this.showScalarInput();
            this.currentOperation = 'scalar-a';
            return;
        }

        if (operation === 'power-a') {
            this.showPowerInput();
            this.currentOperation = 'power-a';
            return;
        }

        this.showLoading();

        setTimeout(() => {
            try {
                let result, operationName, steps = null;

                switch (operation) {
                    case 'add':
                        result = this.addMatrices(matrixA, matrixB);
                        operationName = 'A + B';
                        break;
                    case 'subtract':
                        result = this.subtractMatrices(matrixA, matrixB);
                        operationName = 'A - B';
                        break;
                    case 'multiply':
                        result = this.multiplyMatrices(matrixA, matrixB);
                        operationName = 'A × B';
                        break;
                    case 'transpose-a':
                        result = this.transpose(matrixA);
                        operationName = 'Aᵀ (Transponə)';
                        break;
                    case 'transpose-b':
                        result = this.transpose(matrixB);
                        operationName = 'Bᵀ (Transponə)';
                        break;
                    case 'determinant-a':
                        result = this.determinant(matrixA);
                        operationName = 'det(A)';
                        steps = this.determinantSteps(matrixA);
                        break;
                    case 'determinant-b':
                        result = this.determinant(matrixB);
                        operationName = 'det(B)';
                        steps = this.determinantSteps(matrixB);
                        break;
                    case 'inverse-a':
                        result = this.inverse(matrixA);
                        operationName = 'A⁻¹ (Tərs matris)';
                        break;
                    case 'inverse-b':
                        result = this.inverse(matrixB);
                        operationName = 'B⁻¹ (Tərs matris)';
                        break;
                    case 'trace-a':
                        result = this.trace(matrixA);
                        operationName = 'Trace(A)';
                        break;
                    default:
                        throw new Error('Naməlum əməliyyat');
                }

                this.hideLoading();
                this.displayResult(result, operationName, steps);

            } catch (error) {
                this.hideLoading();
                this.showError(error.message);
            }
        }, 300);
    }

    addMatrices(a, b) {
        if (a.length !== b.length || a[0].length !== b[0].length) {
            throw new Error('Matrislərin ölçüləri eyni olmalıdır');
        }

        return a.map((row, i) =>
            row.map((val, j) => val + b[i][j])
        );
    }

    subtractMatrices(a, b) {
        if (a.length !== b.length || a[0].length !== b[0].length) {
            throw new Error('Matrislərin ölçüləri eyni olmalıdır');
        }

        return a.map((row, i) =>
            row.map((val, j) => val - b[i][j])
        );
    }

    multiplyMatrices(a, b) {
        if (a[0].length !== b.length) {
            throw new Error('A-nın sütun sayı B-nin sətir sayına bərabər olmalıdır');
        }

        const result = [];
        for (let i = 0; i < a.length; i++) {
            result[i] = [];
            for (let j = 0; j < b[0].length; j++) {
                let sum = 0;
                for (let k = 0; k < a[0].length; k++) {
                    sum += a[i][k] * b[k][j];
                }
                result[i][j] = sum;
            }
        }
        return result;
    }

    transpose(matrix) {
        return matrix[0].map((_, colIndex) =>
            matrix.map(row => row[colIndex])
        );
    }

    determinant(matrix) {
        const n = matrix.length;

        if (n !== matrix[0].length) {
            throw new Error('Determinant yalnız kvadrat matrislər üçün hesablana bilər');
        }

        if (n === 1) return matrix[0][0];
        if (n === 2) return matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0];

        let det = 0;
        for (let j = 0; j < n; j++) {
            det += Math.pow(-1, j) * matrix[0][j] * this.determinant(this.getMinor(matrix, 0, j));
        }
        return det;
    }

    getMinor(matrix, row, col) {
        return matrix
            .filter((_, i) => i !== row)
            .map(r => r.filter((_, j) => j !== col));
    }

    inverse(matrix) {
        const n = matrix.length;

        if (n !== matrix[0].length) {
            throw new Error('Tərs matris yalnız kvadrat matrislər üçün hesablana bilər');
        }

        const det = this.determinant(matrix);

        if (Math.abs(det) < 1e-10) {
            throw new Error('Matrisin determinantı sıfırdır, tərs matris yoxdur');
        }

        if (n === 1) return [[1 / matrix[0][0]]];

        if (n === 2) {
            return [
                [matrix[1][1] / det, -matrix[0][1] / det],
                [-matrix[1][0] / det, matrix[0][0] / det]
            ];
        }

        // Gauss-Jordan elimination
        const augmented = matrix.map((row, i) =>
            [...row, ...Array(n).fill(0).map((_, j) => i === j ? 1 : 0)]
        );

        for (let i = 0; i < n; i++) {
            let maxRow = i;
            for (let k = i + 1; k < n; k++) {
                if (Math.abs(augmented[k][i]) > Math.abs(augmented[maxRow][i])) {
                    maxRow = k;
                }
            }
            [augmented[i], augmented[maxRow]] = [augmented[maxRow], augmented[i]];

            const pivot = augmented[i][i];
            for (let j = 0; j < 2 * n; j++) {
                augmented[i][j] /= pivot;
            }

            for (let k = 0; k < n; k++) {
                if (k !== i) {
                    const factor = augmented[k][i];
                    for (let j = 0; j < 2 * n; j++) {
                        augmented[k][j] -= factor * augmented[i][j];
                    }
                }
            }
        }

        return augmented.map(row => row.slice(n));
    }

    trace(matrix) {
        if (matrix.length !== matrix[0].length) {
            throw new Error('Trace yalnız kvadrat matrislər üçün hesablana bilər');
        }

        return matrix.reduce((sum, row, i) => sum + row[i], 0);
    }

    scalarMultiply(matrix, scalar) {
        return matrix.map(row => row.map(val => val * scalar));
    }

    matrixPower(matrix, power) {
        if (matrix.length !== matrix[0].length) {
            throw new Error('Qüvvətə yüksəltmək yalnız kvadrat matrislər üçün mümkündür');
        }

        if (power === 0) {
            return matrix.map((row, i) =>
                row.map((_, j) => i === j ? 1 : 0)
            );
        }

        let result = matrix;
        for (let i = 1; i < power; i++) {
            result = this.multiplyMatrices(result, matrix);
        }
        return result;
    }

    determinantSteps(matrix) {
        const n = matrix.length;
        if (n === 2) {
            return [
                `det(A) = (${matrix[0][0]}) × (${matrix[1][1]}) - (${matrix[0][1]}) × (${matrix[1][0]})`,
                `det(A) = ${matrix[0][0] * matrix[1][1]} - ${matrix[0][1] * matrix[1][0]}`,
                `det(A) = ${this.determinant(matrix)}`
            ];
        }
        return null;
    }

    showScalarInput() {
        document.getElementById('scalarInput').classList.remove('hidden');
        document.getElementById('scalarValue').focus();
    }

    hideScalarInput() {
        document.getElementById('scalarInput').classList.add('hidden');
        document.getElementById('scalarValue').value = '';
    }

    showPowerInput() {
        document.getElementById('powerInput').classList.remove('hidden');
        document.getElementById('powerValue').focus();
    }

    hidePowerInput() {
        document.getElementById('powerInput').classList.add('hidden');
        document.getElementById('powerValue').value = '';
    }

    applyScalar() {
        const scalar = parseFloat(document.getElementById('scalarValue').value);

        if (isNaN(scalar)) {
            this.showError('Düzgün skalar dəyər daxil edin');
            return;
        }

        const matrixA = this.readMatrix('A');
        this.hideScalarInput();
        this.showLoading();

        setTimeout(() => {
            try {
                const result = this.scalarMultiply(matrixA, scalar);
                this.hideLoading();
                this.displayResult(result, `${scalar} × A`);
            } catch (error) {
                this.hideLoading();
                this.showError(error.message);
            }
        }, 300);
    }

    applyPower() {
        const power = parseInt(document.getElementById('powerValue').value);

        if (isNaN(power) || power < 0) {
            this.showError('Düzgün qüvvət dəyəri daxil edin (0 və ya müsbət tam ədəd)');
            return;
        }

        const matrixA = this.readMatrix('A');
        this.hidePowerInput();
        this.showLoading();

        setTimeout(() => {
            try {
                const result = this.matrixPower(matrixA, power);
                this.hideLoading();
                this.displayResult(result, `A^${power}`);
            } catch (error) {
                this.hideLoading();
                this.showError(error.message);
            }
        }, 300);
    }

    displayResult(result, operationName, steps = null) {
        document.getElementById('results').classList.remove('hidden');
        document.getElementById('operationName').textContent = operationName;

        if (typeof result === 'number') {
            // Scalar result
            document.getElementById('resultMatrix').classList.add('hidden');
            document.getElementById('resultScalar').classList.remove('hidden');
            document.getElementById('scalarResult').textContent = result.toFixed(4);
        } else {
            // Matrix result
            document.getElementById('resultScalar').classList.add('hidden');
            document.getElementById('resultMatrix').classList.remove('hidden');

            const container = document.getElementById('resultMatrix');
            container.innerHTML = '';

            result.forEach(row => {
                const rowDiv = document.createElement('div');
                rowDiv.className = 'matrix-row';

                row.forEach(val => {
                    const cell = document.createElement('div');
                    cell.className = 'result-cell';
                    cell.textContent = val.toFixed(2);
                    rowDiv.appendChild(cell);
                });

                container.appendChild(rowDiv);
            });
        }

        // Display steps if available
        if (steps) {
            document.getElementById('stepsContainer').classList.remove('hidden');
            const stepsDiv = document.getElementById('steps');
            stepsDiv.innerHTML = '';

            steps.forEach((step, i) => {
                const stepDiv = document.createElement('div');
                stepDiv.className = 'step-item';
                stepDiv.innerHTML = `<span class="step-number">Addım ${i + 1}</span> ${step}`;
                stepsDiv.appendChild(stepDiv);
            });
        } else {
            document.getElementById('stepsContainer').classList.add('hidden');
        }
    }

    loadExample(example) {
        let matrixA, matrixB;

        switch (example) {
            case 'identity':
                matrixA = [[1, 0], [0, 1]];
                matrixB = [[1, 0], [0, 1]];
                break;
            case 'zero':
                matrixA = [[0, 0], [0, 0]];
                matrixB = [[0, 0], [0, 0]];
                break;
            case 'random':
                matrixA = this.generateRandomMatrix(3, 3);
                matrixB = this.generateRandomMatrix(3, 3);
                document.getElementById('rowsA').value = 3;
                document.getElementById('colsA').value = 3;
                document.getElementById('rowsB').value = 3;
                document.getElementById('colsB').value = 3;
                break;
        }

        this.fillMatrix('A', matrixA);
        this.fillMatrix('B', matrixB);
    }

    generateRandomMatrix(rows, cols) {
        const matrix = [];
        for (let i = 0; i < rows; i++) {
            const row = [];
            for (let j = 0; j < cols; j++) {
                row.push(Math.floor(Math.random() * 20) - 10);
            }
            matrix.push(row);
        }
        return matrix;
    }

    fillMatrix(which, data) {
        if (data.length !== this[`matrix${which}`].length ||
            data[0].length !== this[`matrix${which}`][0].length) {
            document.getElementById(`rows${which}`).value = data.length;
            document.getElementById(`cols${which}`).value = data[0].length;
            this.generateMatrix(which);
        }

        const container = document.getElementById(`matrix${which}`);
        const inputs = container.querySelectorAll('.matrix-cell');

        data.forEach((row, i) => {
            row.forEach((val, j) => {
                const index = i * data[0].length + j;
                inputs[index].value = val;
            });
        });

        this[`matrix${which}`] = data;
    }

    copyResult() {
        const result = this.readMatrix('A'); // Placeholder
        // Copy logic here
        alert('Nəticə kopyalandı!');
    }

    showLoading() {
        document.getElementById('loading').classList.remove('hidden');
    }

    hideLoading() {
        document.getElementById('loading').classList.add('hidden');
    }

    showError(message) {
        const errorDiv = document.getElementById('errorMessage');
        document.getElementById('errorText').textContent = message;
        errorDiv.classList.remove('hidden');
    }

    hideError() {
        document.getElementById('errorMessage').classList.add('hidden');
    }

    hideResults() {
        document.getElementById('results').classList.add('hidden');
    }
}

// Initialize calculator when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new MatrixCalculator();
});