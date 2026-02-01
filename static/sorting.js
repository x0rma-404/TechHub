document.addEventListener('DOMContentLoaded', () => {

    // ─── State ────────────────────────────────────────────────────────
    let array = [];
    let colorMap = {};       // index -> color state
    let running = false;
    let comparisons = 0;
    let swaps = 0;
    let selectedAlgo = 'bubble';

    // ─── Canvas ───────────────────────────────────────────────────────
    const canvas = document.getElementById('sortCanvas');
    const ctx = canvas.getContext('2d');

    function resizeCanvas() {
        canvas.width = canvas.offsetWidth * window.devicePixelRatio;
        canvas.height = canvas.offsetHeight * window.devicePixelRatio;
        ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
    }
    resizeCanvas();
    window.addEventListener('resize', () => { resizeCanvas(); draw(); });

    // ─── Colors ───────────────────────────────────────────────────────
    const COLORS = {
        normal: '#6366f1',
        compare: '#f59e0b',
        swap: '#ef4444',
        sorted: '#10b981'
    };

    // ─── Speed ────────────────────────────────────────────────────────
    function getDelay() {
        const speed = parseInt(document.getElementById('speedSlider').value);
        // speed 1 = slow (200ms), speed 100 = fast (2ms)
        return Math.max(2, 202 - speed * 2);
    }

    function sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // ─── Generate Array ───────────────────────────────────────────────
    function generateArray() {
        const size = parseInt(document.getElementById('sizeSlider').value);
        array = [];
        colorMap = {};
        for (let i = 0; i < size; i++) {
            array.push(Math.floor(Math.random() * 90) + 10); // 10-99
        }
        draw();
    }

    // ─── Draw ─────────────────────────────────────────────────────────
    function draw() {
        const W = canvas.offsetWidth;
        const H = canvas.offsetHeight;
        ctx.clearRect(0, 0, W, H);

        if (array.length === 0) return;

        const barW = (W - (array.length + 1) * 2) / array.length;
        const maxVal = 99;
        const padTop = 24;
        const barMaxH = H - padTop - 8;

        array.forEach((val, i) => {
            const barH = (val / maxVal) * barMaxH;
            const x = 2 + i * (barW + 2);
            const y = H - 8 - barH;

            // Determine color
            let color = COLORS.normal;
            if (colorMap[i] === 'compare') color = COLORS.compare;
            else if (colorMap[i] === 'swap') color = COLORS.swap;
            else if (colorMap[i] === 'sorted') color = COLORS.sorted;

            // Bar shadow
            ctx.fillStyle = 'rgba(0,0,0,0.25)';
            ctx.beginPath();
            ctx.roundRect(x + 1, y + 2, barW, barH, 3);
            ctx.fill();

            // Bar
            ctx.fillStyle = color;
            ctx.beginPath();
            ctx.roundRect(x, y, barW, barH, 3);
            ctx.fill();

            // Value label (only if bars are wide enough)
            if (barW >= 16) {
                ctx.fillStyle = '#e2e8f0';
                ctx.font = 'bold ' + Math.min(11, barW - 4) + 'px monospace';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'top';
                ctx.fillText(String(val), x + barW / 2, y + 4);
            }
        });
    }

    // ─── Stats Update ────────────────────────────────────────────────
    function updateStats() {
        document.getElementById('statComparisons').textContent = comparisons;
        document.getElementById('statSwaps').textContent = swaps;
    }

    function setStatus(text) {
        document.getElementById('statStatus').textContent = text;
    }

    // ─── Complexity Info ──────────────────────────────────────────────
    const COMPLEXITY = {
        bubble: { best: 'O(n)', avg: 'O(n²)', worst: 'O(n²)', space: 'O(1)' },
        selection: { best: 'O(n²)', avg: 'O(n²)', worst: 'O(n²)', space: 'O(1)' },
        insertion: { best: 'O(n)', avg: 'O(n²)', worst: 'O(n²)', space: 'O(1)' },
        merge: { best: 'O(n log n)', avg: 'O(n log n)', worst: 'O(n log n)', space: 'O(n)' },
        quick: { best: 'O(n log n)', avg: 'O(n log n)', worst: 'O(n²)', space: 'O(log n)' }
    };

    const ALGO_NAMES = {
        bubble: 'Bubble', selection: 'Selection', insertion: 'Insertion', merge: 'Merge', quick: 'Quick'
    };

    function updateComplexity() {
        const c = COMPLEXITY[selectedAlgo];
        document.getElementById('complexBest').textContent = c.best;
        document.getElementById('complexAvg').textContent = c.avg;
        document.getElementById('complexWorst').textContent = c.worst;
        document.getElementById('complexSpace').textContent = c.space;
        document.getElementById('statAlgo').textContent = ALGO_NAMES[selectedAlgo];
    }

    // ─── Highlight helpers ────────────────────────────────────────────
    async function highlightCompare(i, j) {
        colorMap[i] = 'compare';
        colorMap[j] = 'compare';
        draw();
        await sleep(getDelay());
    }

    async function highlightSwap(i, j) {
        colorMap[i] = 'swap';
        colorMap[j] = 'swap';
        draw();
        await sleep(getDelay());
        // do the swap
        [array[i], array[j]] = [array[j], array[i]];
        swaps++;
        updateStats();
        colorMap[i] = 'normal';
        colorMap[j] = 'normal';
        draw();
        await sleep(getDelay());
    }

    function markSorted(i) {
        colorMap[i] = 'sorted';
    }

    function resetColors() {
        colorMap = {};
        array.forEach((_, i) => colorMap[i] = 'normal');
    }

    // ─── BUBBLE SORT ──────────────────────────────────────────────────
    async function bubbleSort() {
        const n = array.length;
        for (let i = 0; i < n - 1; i++) {
            for (let j = 0; j < n - 1 - i; j++) {
                if (!running) return;
                comparisons++;
                updateStats();
                await highlightCompare(j, j + 1);
                if (array[j] > array[j + 1]) {
                    await highlightSwap(j, j + 1);
                }
                colorMap[j] = 'normal';
                colorMap[j + 1] = 'normal';
            }
            markSorted(n - 1 - i);
            draw();
        }
        markSorted(0);
        draw();
    }

    // ─── SELECTION SORT ───────────────────────────────────────────────
    async function selectionSort() {
        const n = array.length;
        for (let i = 0; i < n - 1; i++) {
            if (!running) return;
            let minIdx = i;
            colorMap[minIdx] = 'compare';
            draw();
            for (let j = i + 1; j < n; j++) {
                if (!running) return;
                comparisons++;
                updateStats();
                colorMap[j] = 'compare';
                draw();
                await sleep(getDelay());
                if (array[j] < array[minIdx]) {
                    colorMap[minIdx] = 'normal';
                    minIdx = j;
                    colorMap[minIdx] = 'compare';
                } else {
                    colorMap[j] = 'normal';
                }
            }
            if (minIdx !== i) {
                await highlightSwap(i, minIdx);
            }
            resetColors();
            // mark sorted so far
            for (let k = 0; k <= i; k++) markSorted(k);
            draw();
        }
        markSorted(n - 1);
        draw();
    }

    // ─── INSERTION SORT ───────────────────────────────────────────────
    async function insertionSort() {
        const n = array.length;
        markSorted(0);
        draw();
        for (let i = 1; i < n; i++) {
            if (!running) return;
            let j = i;
            colorMap[j] = 'compare';
            draw();
            while (j > 0) {
                if (!running) return;
                comparisons++;
                updateStats();
                colorMap[j] = 'compare';
                colorMap[j - 1] = 'compare';
                draw();
                await sleep(getDelay());
                if (array[j] < array[j - 1]) {
                    await highlightSwap(j, j - 1);
                    j--;
                } else {
                    break;
                }
                colorMap[j + 1] = 'normal';
            }
            resetColors();
            for (let k = 0; k <= i; k++) markSorted(k);
            draw();
        }
    }

    // ─── MERGE SORT ───────────────────────────────────────────────────
    async function mergeSort() {
        await mergeSortHelper(0, array.length - 1);
        // mark all sorted
        resetColors();
        array.forEach((_, i) => markSorted(i));
        draw();
    }

    async function mergeSortHelper(left, right) {
        if (!running || left >= right) return;
        const mid = Math.floor((left + right) / 2);
        await mergeSortHelper(left, mid);
        await mergeSortHelper(mid + 1, right);
        await merge(left, mid, right);
    }

    async function merge(left, mid, right) {
        // highlight the range being merged
        for (let i = left; i <= right; i++) colorMap[i] = 'compare';
        draw();
        await sleep(getDelay());

        const leftArr = array.slice(left, mid + 1);
        const rightArr = array.slice(mid + 1, right + 1);
        let i = 0, j = 0, k = left;

        while (i < leftArr.length && j < rightArr.length) {
            if (!running) return;
            comparisons++;
            updateStats();
            if (leftArr[i] <= rightArr[j]) {
                array[k] = leftArr[i];
                i++;
            } else {
                array[k] = rightArr[j];
                j++;
                swaps++;
                updateStats();
            }
            colorMap[k] = 'swap';
            draw();
            await sleep(getDelay());
            k++;
        }

        while (i < leftArr.length) {
            if (!running) return;
            array[k] = leftArr[i];
            colorMap[k] = 'swap';
            draw();
            await sleep(getDelay());
            i++; k++;
        }

        while (j < rightArr.length) {
            if (!running) return;
            array[k] = rightArr[j];
            colorMap[k] = 'swap';
            draw();
            await sleep(getDelay());
            j++; k++;
        }

        // mark merged range as sorted-ish (normal for now, final green at end)
        for (let x = left; x <= right; x++) colorMap[x] = 'normal';
        draw();
    }

    // ─── QUICK SORT ───────────────────────────────────────────────────
    async function quickSort() {
        await quickSortHelper(0, array.length - 1);
        // mark all sorted
        resetColors();
        array.forEach((_, i) => markSorted(i));
        draw();
    }

    async function quickSortHelper(low, high) {
        if (!running || low >= high) return;
        const pivotIdx = await partition(low, high);
        markSorted(pivotIdx);
        draw();
        await quickSortHelper(low, pivotIdx - 1);
        await quickSortHelper(pivotIdx + 1, high);
    }

    async function partition(low, high) {
        const pivot = array[high];
        colorMap[high] = 'compare'; // highlight pivot
        draw();
        await sleep(getDelay());

        let i = low - 1;
        for (let j = low; j < high; j++) {
            if (!running) return low;
            comparisons++;
            updateStats();
            colorMap[j] = 'compare';
            draw();
            await sleep(getDelay());

            if (array[j] < pivot) {
                i++;
                await highlightSwap(i, j);
            }
            colorMap[j] = 'normal';
        }

        // swap pivot into place
        colorMap[high] = 'swap';
        colorMap[i + 1] = 'swap';
        draw();
        await sleep(getDelay());
        [array[i + 1], array[high]] = [array[high], array[i + 1]];
        swaps++;
        updateStats();
        colorMap[high] = 'normal';
        colorMap[i + 1] = 'normal';
        draw();
        await sleep(getDelay());

        return i + 1;
    }

    // ─── Algorithm Runner ─────────────────────────────────────────────
    const ALGORITHMS = {
        bubble: bubbleSort,
        selection: selectionSort,
        insertion: insertionSort,
        merge: mergeSort,
        quick: quickSort
    };

    async function startSorting() {
        if (running) return;
        running = true;
        comparisons = 0;
        swaps = 0;
        resetColors();
        updateStats();
        setStatus('Çalışır...');
        draw();

        document.getElementById('startBtn').disabled = true;
        document.getElementById('startBtn').style.opacity = '0.5';

        await ALGORITHMS[selectedAlgo]();

        running = false;
        document.getElementById('startBtn').disabled = false;
        document.getElementById('startBtn').style.opacity = '1';

        if (isSorted()) {
            setStatus('Tamamlandı ✓');
            // final green animation
            resetColors();
            array.forEach((_, i) => markSorted(i));
            draw();
        } else {
            setStatus('Dayandırıldı');
        }
    }

    function isSorted() {
        for (let i = 1; i < array.length; i++) {
            if (array[i] < array[i - 1]) return false;
        }
        return true;
    }

    // ─── Reset (keep same array, reset colors) ───────────────────────
    function resetArray() {
        running = false;
        comparisons = 0;
        swaps = 0;
        resetColors();
        updateStats();
        setStatus('Hazır');
        draw();
        document.getElementById('startBtn').disabled = false;
        document.getElementById('startBtn').style.opacity = '1';
    }

    // ─── Event Listeners ──────────────────────────────────────────────
    document.getElementById('startBtn').addEventListener('click', startSorting);

    document.getElementById('resetBtn').addEventListener('click', () => {
        // regenerate same-size array (fresh random)
        running = false;
        generateArray();
        comparisons = 0;
        swaps = 0;
        updateStats();
        setStatus('Hazır');
        document.getElementById('startBtn').disabled = false;
        document.getElementById('startBtn').style.opacity = '1';
    });

    document.getElementById('newArrayBtn').addEventListener('click', () => {
        running = false;
        generateArray();
        comparisons = 0;
        swaps = 0;
        updateStats();
        setStatus('Hazır');
        document.getElementById('startBtn').disabled = false;
        document.getElementById('startBtn').style.opacity = '1';
    });

    document.getElementById('sizeSlider').addEventListener('input', () => {
        if (running) return;
        generateArray();
    });

    // Algorithm buttons
    document.querySelectorAll('.algo-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            if (running) return;
            document.querySelectorAll('.algo-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            selectedAlgo = btn.dataset.algo;
            updateComplexity();
            // reset when switching algo
            generateArray();
            comparisons = 0;
            swaps = 0;
            updateStats();
            setStatus('Hazır');
        });
    });

    // ─── Init ─────────────────────────────────────────────────────────
    generateArray();
    updateComplexity();

}); // end DOMContentLoaded