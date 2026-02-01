// ─── State ────────────────────────────────────────────────────────
let tree = null;
let highlightPath = [];
let highlightFound = null;

// ─── Node Class ───────────────────────────────────────────────────
class Node {
    constructor(value) {
        this.value = value;
        this.left = null;
        this.right = null;
    }
}

// ─── BST Logic ────────────────────────────────────────────────────
function insert(root, value) {
    if (!root) return new Node(value);
    if (value < root.value) root.left = insert(root.left, value);
    else if (value > root.value) root.right = insert(root.right, value);
    return root;
}

function findMin(node) {
    while (node.left) node = node.left;
    return node;
}

function deleteNode(root, value) {
    if (!root) return null;
    if (value < root.value) {
        root.left = deleteNode(root.left, value);
    } else if (value > root.value) {
        root.right = deleteNode(root.right, value);
    } else {
        if (!root.left) return root.right;
        if (!root.right) return root.left;
        let successor = findMin(root.right);
        root.value = successor.value;
        root.right = deleteNode(root.right, successor.value);
    }
    return root;
}

function search(root, value) {
    let path = [];
    let cur = root;
    while (cur) {
        path.push(cur.value);
        if (value === cur.value) return { found: true, path };
        cur = value < cur.value ? cur.left : cur.right;
    }
    return { found: false, path };
}

function contains(root, value) {
    let cur = root;
    while (cur) {
        if (value === cur.value) return true;
        cur = value < cur.value ? cur.left : cur.right;
    }
    return false;
}

// ─── Traversals ───────────────────────────────────────────────────
function inorder(node, res = []) { if (node) { inorder(node.left, res); res.push(node.value); inorder(node.right, res); } return res; }
function preorder(node, res = []) { if (node) { res.push(node.value); preorder(node.left, res); preorder(node.right, res); } return res; }
function postorder(node, res = []) { if (node) { postorder(node.left, res); postorder(node.right, res); res.push(node.value); } return res; }

// ─── Stats ────────────────────────────────────────────────────────
function height(node) {
    if (!node) return -1;
    return 1 + Math.max(height(node.left), height(node.right));
}

function countNodes(node) {
    if (!node) return 0;
    return 1 + countNodes(node.left) + countNodes(node.right);
}

function findMinVal(node) { while (node && node.left) node = node.left; return node ? node.value : null; }
function findMaxVal(node) { while (node && node.right) node = node.right; return node ? node.value : null; }

// ─── Canvas Drawing ───────────────────────────────────────────────
const canvas = document.getElementById('treeCanvas');
const ctx = canvas.getContext('2d');

// Base constants (max size, shrinks from here)
const BASE_R = 24;
const BASE_LVLH = 68;
const MIN_R = 8;
const MIN_LVLH = 26;

function resizeCanvas() {
    canvas.width = canvas.offsetWidth * window.devicePixelRatio;
    canvas.height = canvas.offsetHeight * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
}
resizeCanvas();
window.addEventListener('resize', () => { resizeCanvas(); drawTree(); });

// Compute x positions via inorder index
function computePositions(node, positions, counter) {
    if (!node) return counter;
    counter = computePositions(node.left, positions, counter);
    positions.set(node, { idx: counter });
    counter++;
    counter = computePositions(node.right, positions, counter);
    return counter;
}

// Dynamic scale: shrinks radius & level-height based on node count + tree height
function getScale(total, treeH) {
    const W = canvas.offsetWidth;

    // Width scale: nodes side-by-side fit?
    const neededW = total * (BASE_R * 2 + 6);
    const scaleW = Math.min(1, W / neededW);

    // Height scale: levels fit within max allowed canvas height
    const levels = treeH + 1;
    const neededH = levels * BASE_LVLH + BASE_R * 2;
    const maxH = 620;
    const scaleH = Math.min(1, maxH / neededH);

    const scale = Math.min(scaleW, scaleH);
    const r = Math.max(MIN_R, Math.round(BASE_R * scale));
    const lvlH = Math.max(MIN_LVLH, Math.round(BASE_LVLH * scale));
    const fontSize = Math.max(9, Math.round(14 * scale));

    return { r, lvlH, fontSize };
}

function drawTree() {
    const W = canvas.offsetWidth;
    ctx.clearRect(0, 0, W, canvas.offsetHeight);

    if (!tree) {
        canvas.style.height = '200px';
        resizeCanvas();
        ctx.clearRect(0, 0, W, canvas.offsetHeight);
        ctx.fillStyle = '#64748b';
        ctx.font = '15px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('Ağac boşdur. Yuxarıda bir node əlavə edin.', W / 2, 100);
        return;
    }

    // 1) inorder positions
    const positions = new Map();
    const total = computePositions(tree, positions, 0);
    const treeH = height(tree);

    // 2) dynamic scale
    const { r, lvlH, fontSize } = getScale(total, treeH);

    // 3) resize canvas height to fit
    const neededH = (treeH + 1) * lvlH + r * 2 + 24;
    canvas.style.height = Math.max(neededH, 200) + 'px';
    resizeCanvas();
    ctx.clearRect(0, 0, canvas.offsetWidth, canvas.offsetHeight);

    const unitW = W / total;

    // 4) assign pixel coords
    function assignCoords(node, depth) {
        if (!node) return;
        const pos = positions.get(node);
        pos.x = pos.idx * unitW + unitW / 2;
        pos.y = depth * lvlH + r + 14;
        assignCoords(node.left, depth + 1);
        assignCoords(node.right, depth + 1);
    }
    assignCoords(tree, 0);

    // 5) draw edges
    function drawEdges(node) {
        if (!node) return;
        const p = positions.get(node);
        [node.left, node.right].forEach(child => {
            if (!child) return;
            const c = positions.get(child);
            ctx.beginPath();
            ctx.moveTo(p.x, p.y + r);
            ctx.lineTo(c.x, c.y - r);
            ctx.strokeStyle = '#475569';
            ctx.lineWidth = Math.max(1.2, r * 0.12);
            ctx.stroke();
            drawEdges(child);
        });
    }
    drawEdges(tree);

    // 6) draw nodes
    function drawNodes(node) {
        if (!node) return;
        const p = positions.get(node);

        let fillColor = '#6366f1';
        let strokeColor = '#818cf8';
        let textColor = '#e0e7ff';

        if (highlightFound !== null && highlightPath.includes(node.value)) {
            if (node.value === highlightFound) {
                fillColor = '#10b981';
                strokeColor = '#34d399';
            } else {
                fillColor = '#f59e0b';
                strokeColor = '#fbbf24';
            }
        }

        // Shadow
        ctx.beginPath();
        ctx.arc(p.x, p.y + Math.max(1, r * 0.08), r, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(0,0,0,0.3)';
        ctx.fill();

        // Circle
        ctx.beginPath();
        ctx.arc(p.x, p.y, r, 0, Math.PI * 2);
        ctx.fillStyle = fillColor;
        ctx.fill();
        ctx.strokeStyle = strokeColor;
        ctx.lineWidth = Math.max(1.2, r * 0.11);
        ctx.stroke();

        // Text
        ctx.fillStyle = textColor;
        ctx.font = 'bold ' + fontSize + 'px monospace';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(String(node.value), p.x, p.y);

        drawNodes(node.left);
        drawNodes(node.right);
    }
    drawNodes(tree);
}

// ─── UI Updates ───────────────────────────────────────────────────
function updateStats() {
    document.getElementById('statCount').textContent = countNodes(tree);
    document.getElementById('statHeight').textContent = tree ? height(tree) : 0;
    document.getElementById('statMin').textContent = tree ? findMinVal(tree) : '—';
    document.getElementById('statMax').textContent = tree ? findMaxVal(tree) : '—';
}

function updateTraversals() {
    const fmt = arr => arr.length ? arr.join(' → ') : '—';
    document.getElementById('travInorder').textContent = fmt(inorder(tree));
    document.getElementById('travPreorder').textContent = fmt(preorder(tree));
    document.getElementById('travPostorder').textContent = fmt(postorder(tree));
}

function showStatus(msg) {
    const el = document.getElementById('statusMessage');
    el.textContent = msg;
    el.classList.remove('hidden');
    document.getElementById('errorMessage').classList.add('hidden');
    setTimeout(() => el.classList.add('hidden'), 2500);
}

function showError(msg) {
    const el = document.getElementById('errorMessage');
    el.textContent = msg;
    el.classList.remove('hidden');
    document.getElementById('statusMessage').classList.add('hidden');
    setTimeout(() => el.classList.add('hidden'), 2500);
}

function refresh() {
    updateStats();
    updateTraversals();
    drawTree();
}

// ─── Button Handlers ──────────────────────────────────────────────
const nodeInput = document.getElementById('nodeValue');

function getInputValue() {
    const raw = nodeInput.value.trim();
    const val = Number(raw);
    if (raw === '' || isNaN(val) || !Number.isInteger(val)) return null;
    return val;
}

document.getElementById('insertBtn').addEventListener('click', () => {
    const val = getInputValue();
    if (val === null) { showError('Düzgün bir tam ədad daxil edin.'); return; }
    if (contains(tree, val)) { showError(val + ' artıq ağacın içindedir!'); return; }
    tree = insert(tree, val);
    highlightPath = [];
    highlightFound = null;
    nodeInput.value = '';
    showStatus(val + ' uğurla əlavə edildi ✓');
    refresh();
});

document.getElementById('deleteBtn').addEventListener('click', () => {
    const val = getInputValue();
    if (val === null) { showError('Düzgün bir tam ədad daxil edin.'); return; }
    if (!contains(tree, val)) { showError(val + ' ağacın içinde yoxdur!'); return; }
    tree = deleteNode(tree, val);
    highlightPath = [];
    highlightFound = null;
    nodeInput.value = '';
    showStatus(val + ' uğurla silindi ✓');
    refresh();
});

document.getElementById('searchBtn').addEventListener('click', () => {
    const val = getInputValue();
    if (val === null) { showError('Düzgün bir tam ədad daxil edin.'); return; }
    if (!tree) { showError('Ağac boşdur!'); return; }
    const result = search(tree, val);
    highlightPath = result.path;
    highlightFound = result.found ? val : null;
    if (result.found) {
        showStatus(val + ' tapıldı ✓  |  Yol: ' + result.path.join(' → '));
    } else {
        showError(val + ' tapılmadı ✗  |  Yol: ' + result.path.join(' → '));
    }
    drawTree();
});

document.getElementById('clearBtn').addEventListener('click', () => {
    tree = null;
    highlightPath = [];
    highlightFound = null;
    nodeInput.value = '';
    showStatus('Ağac temizlendi ✓');
    refresh();
});

// Enter key
nodeInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') document.getElementById('insertBtn').click();
});

// ─── Init: start with a sample tree ──────────────────────────────
[50, 30, 70, 20, 40, 60, 80].forEach(v => { tree = insert(tree, v); });
refresh();
