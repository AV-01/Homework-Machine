const canvas = document.getElementById('drawing-canvas');
const ctx = canvas.getContext('2d');
const statusBar = document.getElementById('status-bar');

// API Base URL
const API_BASE = '/api/fonts';

// State
let fonts = [];
let currentFont = '';
let fontData = {};
let currentChar = 'A';

// Drawing State
const SCALE = 20; // 20 pixels = 1 Hershey Unit
let strokes = [];
let currentStroke = null;
let isDrawing = false;
let bounds = [-10, 10]; // [left, right] in Hershey units

// Interaction State
let draggingBound = null; // 'left' or 'right'

// Canvas transforms
function getCanvasCenter() { return { x: canvas.width / 2, y: canvas.height / 2 + 50 }; }

function hersheyToScreen(hx, hy) {
    const center = getCanvasCenter();
    return {
        x: center.x + (hx * SCALE),
        y: center.y - (hy * SCALE)
    };
}

function screenToHershey(px, py) {
    const center = getCanvasCenter();
    return {
        x: (px - center.x) / SCALE,
        y: (center.y - py) / SCALE
    };
}

// Initialization
async function init() {
    setupEvents();
    populateCharGrid();
    await fetchFonts();
    render();
}

function setupEvents() {
    // Canvas pointer events
    canvas.addEventListener('pointerdown', handlePointerDown);
    canvas.addEventListener('pointermove', handlePointerMove);
    canvas.addEventListener('pointerup', handlePointerUp);
    canvas.addEventListener('pointercancel', handlePointerUp);

    // Tools
    document.getElementById('btn-clear').addEventListener('click', () => { strokes = []; render(); });
    document.getElementById('btn-undo').addEventListener('click', () => { strokes.pop(); render(); });
    document.getElementById('btn-save').addEventListener('click', saveCharacter);
    document.getElementById('btn-delete').addEventListener('click', deleteCharacter);
    
    // Changing Char
    const charInput = document.getElementById('char-input');
    charInput.addEventListener('input', (e) => {
        if (e.target.value) {
            setCurrentChar(e.target.value);
        }
    });

    // Font Selection
    document.getElementById('font-select').addEventListener('change', (e) => {
        loadFont(e.target.value);
    });

    // New Font Modal
    const modal = document.getElementById('modal-new-font');
    document.getElementById('btn-new-font').addEventListener('click', () => modal.classList.add('active'));
    document.getElementById('btn-cancel-modal').addEventListener('click', () => modal.classList.remove('active'));
    document.getElementById('btn-confirm-modal').addEventListener('click', async () => {
        const name = document.getElementById('new-font-name').value.trim();
        if (name) {
            await createFont(name);
            modal.classList.remove('active');
        }
    });

    // Hotkeys
    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === 'z') { strokes.pop(); render(); }
    });
}

function populateCharGrid() {
    const grid = document.getElementById('char-grid');
    grid.innerHTML = '';
    const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!?;:,.+-=/()".split('');
    chars.forEach(c => {
        const div = document.createElement('div');
        div.className = 'char-item';
        div.textContent = c;
        div.dataset.char = c;
        div.addEventListener('click', () => {
            document.getElementById('char-input').value = c;
            setCurrentChar(c);
        });
        grid.appendChild(div);
    });
}

function updateCharGridState() {
    document.querySelectorAll('.char-item').forEach(el => {
        el.classList.remove('active');
        el.classList.remove('saved');
        const c = el.dataset.char;
        if (c === currentChar) el.classList.add('active');
        if (fontData && fontData[c]) el.classList.add('saved');
    });
}

function setCurrentChar(c) {
    currentChar = c;
    if (fontData[currentChar]) {
        const data = fontData[currentChar];
        bounds = [data[0], data[1]];
        strokes = data.slice(2);
    } else {
        bounds = [-10, 10];
        strokes = [];
    }
    updateCharGridState();
    render();
}

// API Calls
async function fetchFonts() {
    try {
        const res = await fetch(API_BASE);
        const data = await res.json();
        fonts = data.fonts;
        
        const select = document.getElementById('font-select');
        select.innerHTML = '';
        if (fonts.length === 0) {
            select.innerHTML = '<option value="">Create a font first...</option>';
        } else {
            fonts.forEach(f => {
                const opt = document.createElement('option');
                opt.value = f;
                opt.textContent = f;
                select.appendChild(opt);
            });
            if (!currentFont) {
                currentFont = fonts[0];
                await loadFont(currentFont);
            }
        }
    } catch(e) { console.error(e); }
}

async function createFont(name) {
    try {
        const res = await fetch(`${API_BASE}/${name}`, { method: 'POST' });
        if (res.ok) {
            setStatus(`Font ${name} created!`);
            currentFont = name;
            await fetchFonts();
            document.getElementById('font-select').value = name;
            await loadFont(name);
        }
    } catch(e) { console.error(e); }
}

async function loadFont(name) {
    if (!name) return;
    try {
        currentFont = name;
        const res = await fetch(`${API_BASE}/${name}`);
        fontData = await res.json();
        setCurrentChar(currentChar);
        setStatus(`Loaded font: ${name}`);
    } catch(e) { console.error(e); }
}

async function saveCharacter() {
    if (!currentFont) return alert("Please create or select a font first.");
    
    // Optionally apply gentle smoothing here, but raw points are fine
    const payload = {
        bounds: bounds,
        strokes: strokes
    };
    
    try {
        const res = await fetch(`${API_BASE}/${currentFont}/${encodeURIComponent(currentChar)}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (res.ok) {
            fontData[currentChar] = [bounds[0], bounds[1], ...strokes];
            updateCharGridState();
            setStatus(`Saved char: ${currentChar}`);
        }
    } catch(e) { console.error(e); }
}

async function deleteCharacter() {
    if (!currentFont || !fontData[currentChar]) return;
    try {
        const res = await fetch(`${API_BASE}/${currentFont}/${encodeURIComponent(currentChar)}`, { method: 'DELETE' });
        if (res.ok) {
            delete fontData[currentChar];
            strokes = [];
            updateCharGridState();
            render();
            setStatus(`Deleted char: ${currentChar}`);
        }
    } catch(e) { console.error(e); }
}

// Drawing Logic
function handlePointerDown(e) {
    if (e.target !== canvas) return;
    canvas.setPointerCapture(e.pointerId);
    
    const rect = canvas.getBoundingClientRect();
    const px = e.clientX - rect.left;
    const py = e.clientY - rect.top;
    const hPoint = screenToHershey(px, py);

    // Check bounds drag
    const HIT_RADIUS = 0.5; // Hershey units
    if (Math.abs(hPoint.x - bounds[0]) < HIT_RADIUS) { draggingBound = 0; return; }
    if (Math.abs(hPoint.x - bounds[1]) < HIT_RADIUS) { draggingBound = 1; return; }

    // Start stroke (Round coords for smaller json size)
    currentStroke = [[Math.round(hPoint.x * 10)/10, Math.round(hPoint.y * 10)/10]];
    strokes.push(currentStroke);
    isDrawing = true;
    render();
}

function handlePointerMove(e) {
    const rect = canvas.getBoundingClientRect();
    const px = e.clientX - rect.left;
    const py = e.clientY - rect.top;
    const hPoint = screenToHershey(px, py);
    hPoint.x = Math.round(hPoint.x * 10) / 10;
    hPoint.y = Math.round(hPoint.y * 10) / 10;

    if (draggingBound !== null) {
        bounds[draggingBound] = hPoint.x;
        render();
        return;
    }

    if (!isDrawing || !currentStroke) return;
    
    const lastPoint = currentStroke[currentStroke.length - 1];
    // Filter points too close
    const dist = Math.hypot(hPoint.x - lastPoint[0], hPoint.y - lastPoint[1]);
    if (dist > 0.5) { // 0.5 units threshold
        currentStroke.push([hPoint.x, hPoint.y]);
        render();
    }
}

function handlePointerUp(e) {
    isDrawing = false;
    currentStroke = null;
    draggingBound = null;
    canvas.releasePointerCapture(e.pointerId);
}

// Rendering
function render() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Draw Guidelines
    drawHersheyLine(null, 12, 'rgba(255,255,255,0.1)', [5,5]); // Cap Height
    drawHersheyLine(null, 5, 'rgba(255,255,255,0.15)', [5,5]); // Mean line
    drawHersheyLine(null, 0, 'rgba(255,255,255,0.4)', []); // Baseline
    drawHersheyLine(null, -9, 'rgba(255,255,255,0.1)', [5,5]); // Descender
    
    drawHersheyLine(0, null, 'rgba(255,255,255,0.1)', []); // Y-axis

    // Draw Boundaries
    ctx.strokeStyle = '#6366f1';
    ctx.lineWidth = 1.5;
    ctx.setLineDash([4, 4]);
    
    const pLeft = hersheyToScreen(bounds[0], 0);
    ctx.beginPath(); ctx.moveTo(pLeft.x, 0); ctx.lineTo(pLeft.x, canvas.height); ctx.stroke();
    
    const pRight = hersheyToScreen(bounds[1], 0);
    ctx.beginPath(); ctx.moveTo(pRight.x, 0); ctx.lineTo(pRight.x, canvas.height); ctx.stroke();
    
    ctx.setLineDash([]); // Reset
    
    // Draw strokes
    ctx.lineWidth = 3;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.strokeStyle = '#fff';
    
    strokes.forEach(stroke => {
        if (stroke.length < 2) return;
        ctx.beginPath();
        const start = hersheyToScreen(stroke[0][0], stroke[0][1]);
        ctx.moveTo(start.x, start.y);
        for(let i=1; i<stroke.length; i++) {
            const p = hersheyToScreen(stroke[i][0], stroke[i][1]);
            ctx.lineTo(p.x, p.y);
        }
        ctx.stroke();
    });
}

function drawHersheyLine(xStr, yStr, color, dash) {
    ctx.beginPath();
    ctx.strokeStyle = color;
    ctx.lineWidth = 1;
    ctx.setLineDash(dash);
    if (xStr !== null) { // vertical
        const p = hersheyToScreen(xStr, 0);
        ctx.moveTo(p.x, 0); ctx.lineTo(p.x, canvas.height);
    } else { // horizontal
        const p = hersheyToScreen(0, yStr);
        ctx.moveTo(0, p.y); ctx.lineTo(canvas.width, p.y);
    }
    ctx.stroke();
}

function setStatus(msg) {
    statusBar.textContent = msg;
    setTimeout(() => { if(statusBar.textContent===msg) statusBar.textContent='Ready'; }, 3000);
}

// Start
init();
