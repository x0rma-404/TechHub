/**
 * py_visualizer.js
 * Python Execution Tracer & Visualizer
 */

let pyodide = null;
let editor = null;
let snapshots = [];
let currentStep = 0;
let lastActiveLine = null;

const PYODIDE_INDEX_URL = 'https://cdn.jsdelivr.net/pyodide/v0.25.0/full/';

// --- Initialization ---

window.addEventListener('DOMContentLoaded', () => {
    const textarea = document.getElementById("code-editor");
    editor = CodeMirror.fromTextArea(textarea, {
        lineNumbers: true,
        mode: "python",
        theme: "material-darker",
        indentUnit: 4,
        matchBrackets: true,
        autoCloseBrackets: true,
        lineWrapping: true
    });

    init_pyodide();
});

async function init_pyodide() {
    const loadingOverlay = document.getElementById('vis-loading');
    const visBtn = document.getElementById('visBtn');

    try {
        pyodide = await loadPyodide({ indexURL: PYODIDE_INDEX_URL });
        loadingOverlay.classList.add('hidden');
        visBtn.disabled = false;
    } catch (err) {
        console.error('Pyodide Error:', err);
        loadingOverlay.innerHTML = `<p class="text-red-500">Yüklənmə xətası. Yenidən cəhd edin.</p>`;
    }
}

// --- Tracer Logic ---

async function startVisualization() {
    const code = editor.getValue().trim();
    if (!code) return;

    const visBtn = document.getElementById('visBtn');
    visBtn.disabled = true;
    visBtn.innerHTML = "<i class='bx bx-loader-alt animate-spin mr-2'></i> Hazırlanır...";

    // Trace Script: Wraps user code and uses sys.settrace
    const tracerScript = `
import sys
import json
import types

class VisualTracer:
    def __init__(self):
        self.snapshots = []
        self.output = []
        self.max_steps = 1000
    
    def serialize_val(self, val):
        if isinstance(val, (int, float, bool, str, type(None))):
            return val
        if isinstance(val, (list, tuple, set)):
            return [self.serialize_val(x) for x in val]
        if isinstance(val, dict):
            return {str(k): self.serialize_val(v) for k, v in val.items()}
        return str(val)

    def trace_hook(self, frame, event, arg):
        if event not in ("line", "return"):
            return self.trace_hook
        
        if len(self.snapshots) >= self.max_steps:
            return None # Stop tracing

        # Current line info
        line_no = frame.f_lineno
        
        # Capture locals (ignoring internals)
        locs = {}
        for name, val in frame.f_locals.items():
            if not name.startswith('__'):
                locs[name] = {
                    'type': type(val).__name__,
                    'value': self.serialize_val(val)
                }
        
        # If it's a return event, we might want to show the return value too
        if event == "return" and frame.f_code.co_name != "<module>":
            locs["__return__"] = {
                'type': type(arg).__name__,
                'value': self.serialize_val(arg)
            }

        self.snapshots.append({
            'line': line_no,
            'locals': locs,
            'stdout': sys.stdout.getvalue(),
            'event': event
        })
        
        return self.trace_hook

# Setup Environment
tracer = VisualTracer()

import sys
from io import StringIO
original_stdout = sys.stdout
sys.stdout = StringIO()

try:
    # Compile and execute with trace
    code_obj = compile(${JSON.stringify(code)}, '<script>', 'exec')
    sys.settrace(tracer.trace_hook)
    exec(code_obj, {})
    sys.settrace(None)
except Exception as e:
    sys.settrace(None)
    import traceback
    traceback.print_exc()

# Fetch results
sys.stdout = original_stdout
json.dumps({'snapshots': tracer.snapshots})
`;

    try {
        const resultJson = await pyodide.runPythonAsync(tracerScript);
        const data = JSON.parse(resultJson);
        snapshots = data.snapshots;

        if (snapshots.length === 0) {
            alert("Trace məlumatı alınmadı. Kodun icra edildiğinden əmin olun.");
            return;
        }

        currentStep = 0;
        updateUI();

        // Show controls
        document.getElementById('stepSlider').max = snapshots.length - 1;
        document.getElementById('stepSlider').value = 0;
        document.getElementById('prevBtn').disabled = true;
        document.getElementById('nextBtn').disabled = snapshots.length <= 1;

    } catch (err) {
        console.error("Tracing Error:", err);
        alert("Xəta baş verdi: " + err.message);
    } finally {
        visBtn.disabled = false;
        visBtn.innerHTML = "<i class='bx bx-play-circle mr-2'></i> Visualizə Et";
    }
}

// --- Navigation & UI UI ---

function updateUI() {
    const snapshot = snapshots[currentStep];
    const prevSnapshot = currentStep > 0 ? snapshots[currentStep - 1] : null;

    // 1. Line Highlight
    if (lastActiveLine !== null) {
        editor.removeLineClass(lastActiveLine, "background", "cm-active-line");
    }
    const lineIndex = snapshot.line - 1;
    editor.addLineClass(lineIndex, "background", "cm-active-line");
    lastActiveLine = lineIndex;

    // Scroll line into view
    editor.scrollIntoView({ line: lineIndex, ch: 0 }, 200);

    // 2. Variable Inspector
    const container = document.getElementById('variables-container');
    container.innerHTML = "";

    const frame = document.createElement('div');
    frame.className = "frame-box";
    frame.innerHTML = '<div class="frame-header">Global Scope / Locals</div>';

    const items = Object.entries(snapshot.locals);
    if (items.length === 0) {
        frame.innerHTML += '<div class="p-3 text-slate-500 text-xs italic">Dəyişən yoxdur</div>';
    } else {
        items.forEach(([name, data]) => {
            const row = document.createElement('div');
            row.className = "variable-row";

            // Check if changed
            const isChanged = prevSnapshot &&
                (!prevSnapshot.locals[name] ||
                    JSON.stringify(prevSnapshot.locals[name].value) !== JSON.stringify(data.value));

            const valueClass = getValueClass(data.type);
            let displayVal = formatValue(data.value, data.type);

            row.innerHTML = `
                <div class="var-name">${name}</div>
                <div class="var-value-box ${isChanged ? 'value-changed' : ''}">
                    <span class="type-tag">${data.type}</span>
                    <span class="${valueClass}">${displayVal}</span>
                </div>
            `;
            frame.appendChild(row);
        });
    }
    container.appendChild(frame);

    // 3. Console Update
    document.getElementById('vis-console').textContent = snapshot.stdout || "Çıxış yoxdur...";

    // 4. Step Info
    document.getElementById('step-counter').textContent = `Addım: ${currentStep + 1} / ${snapshots.length}`;

    // 5. Button States
    document.getElementById('prevBtn').disabled = currentStep === 0;
    document.getElementById('nextBtn').disabled = currentStep === snapshots.length - 1;
    document.getElementById('stepSlider').value = currentStep;
}

function nextStep() {
    if (currentStep < snapshots.length - 1) {
        currentStep++;
        updateUI();
    }
}

function prevStep() {
    if (currentStep > 0) {
        currentStep--;
        updateUI();
    }
}

function goToStep(val) {
    currentStep = parseInt(val);
    updateUI();
}

function resetVisualizer() {
    snapshots = [];
    currentStep = 0;
    if (lastActiveLine !== null) {
        editor.removeLineClass(lastActiveLine, "background", "cm-active-line");
    }
    document.getElementById('variables-container').innerHTML = `
        <div class="text-center py-20 text-slate-500 italic">
            <i class='bx bx-info-circle text-4xl block mb-2 opacity-20'></i>
            Kodunuzu visualizə etmək üçün "Visualizə Et" düyməsini sıxın
        </div>`;
    document.getElementById('vis-console').textContent = "";
    document.getElementById('step-counter').textContent = "Addım: 0 / 0";
    document.getElementById('stepSlider').max = 0;
    document.getElementById('prevBtn').disabled = true;
    document.getElementById('nextBtn').disabled = true;
}

// --- Helpers ---

function getValueClass(type) {
    if (['int', 'float'].includes(type)) return 'val-int';
    if (type === 'str') return 'val-str';
    if (type === 'bool') return 'val-bool';
    if (type === 'NoneType') return 'val-none';
    if (['list', 'dict', 'tuple'].includes(type)) return `val-${type}`;
    return '';
}

function formatValue(val, type) {
    if (type === 'str') return '"' + val + '"';
    if (type === 'NoneType') return 'None';
    if (Array.isArray(val)) return '[' + val.map(v => typeof v === 'string' ? '"' + v + '"' : v).join(', ') + ']';
    if (typeof val === 'object' && val !== null) return JSON.stringify(val);
    return val;
}
