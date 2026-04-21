// Environment-aware API base URL detection
// In production (served by Flask/gunicorn), use the current origin.
// In development, fall back to localhost:5000.
const API_BASE = (() => {
    const loc = window.location;
    if (loc.hostname === 'localhost' || loc.hostname === '127.0.0.1') {
        return `${loc.protocol}//${loc.hostname}:${loc.port || '5000'}/api`;
    }
    return `${loc.protocol}//${loc.host}/api`;
})();

// =========================================================
// ===  UI SYSTEM: Toast · Progress · Confirm  =============
// =========================================================

function showToast(title, message = '', type = 'info', duration = 4000) {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <div class="toast-icon"></div>
        <div class="toast-body">
            <div class="toast-title">${title}</div>
            ${message ? `<div class="toast-msg">${message}</div>` : ''}
        </div>
        <button class="toast-close" onclick="this.parentElement.remove()">×</button>`;
    container.appendChild(toast);
    setTimeout(() => {
        toast.classList.add('exiting');
        setTimeout(() => toast.remove(), 320);
    }, duration);
}

function showProgress(title, subtitle = '') {
    document.getElementById('progress-title').textContent = title;
    document.getElementById('progress-subtitle').textContent = subtitle;
    document.getElementById('progress-stats').textContent = '';
    const bar = document.getElementById('progress-bar');
    bar.style.width = '0%';
    bar.classList.add('indeterminate');
    document.getElementById('progress-overlay').classList.remove('hidden');
}

function setProgress(pct, stats = '') {
    const bar = document.getElementById('progress-bar');
    bar.classList.remove('indeterminate');
    bar.style.width = `${Math.min(100, pct)}%`;
    if (stats) document.getElementById('progress-stats').textContent = stats;
}

function hideProgress() {
    setProgress(100);
    setTimeout(() => {
        document.getElementById('progress-overlay').classList.add('hidden');
        document.getElementById('progress-bar').style.width = '0%';
        document.getElementById('progress-bar').classList.add('indeterminate');
    }, 400);
}

function showConfirm(message, icon = '⚠️') {
    return new Promise(resolve => {
        document.getElementById('confirm-message').textContent = message;
        document.getElementById('confirm-icon').textContent = icon;
        const overlay = document.getElementById('confirm-overlay');
        overlay.classList.remove('hidden');
        const ok = document.getElementById('confirm-ok-btn');
        const cancel = document.getElementById('confirm-cancel-btn');
        const cleanup = (result) => {
            overlay.classList.add('hidden');
            ok.replaceWith(ok.cloneNode(true));
            cancel.replaceWith(cancel.cloneNode(true));
            resolve(result);
        };
        document.getElementById('confirm-ok-btn').onclick = () => cleanup(true);
        document.getElementById('confirm-cancel-btn').onclick = () => cleanup(false);
    });
}

// =========================================================
// ===  NAVIGATION / PANELS  ===============================
// =========================================================

function toggleDebugPanel() {
    document.getElementById('debug-drawer').classList.toggle('hidden-right');
}

function toggleKnowledgeModal() {
    const modal = document.getElementById('knowledge-modal');
    const isHidden = modal.classList.contains('hidden');
    if (isHidden) { modal.classList.remove('hidden'); fetchKnowledge(); }
    else { modal.classList.add('hidden'); }
}

let isLightMode = false;
function toggleTheme() {
    isLightMode = !isLightMode;
    document.body.classList.toggle('light-theme', isLightMode);
    
    // Update mode text and toggle icons
    const modeText = document.getElementById('mode-text');
    const moonIcon = document.querySelector('.moon-icon');
    const sunIcon = document.querySelector('.sun-icon');
    
    if (isLightMode) {
        modeText.textContent = 'Light Mode';
        moonIcon.classList.add('hidden');
        sunIcon.classList.remove('hidden');
    } else {
        modeText.textContent = 'Dark Mode';
        moonIcon.classList.remove('hidden');
        sunIcon.classList.add('hidden');
    }
}

// =========================================================
// ===  CHAT  ==============================================
// =========================================================

const historyDiv = document.getElementById('chat-history');

function scrollChat() {
    setTimeout(() => {
        const viewport = historyDiv.parentElement;
        viewport.scrollTo({ top: viewport.scrollHeight, behavior: 'smooth' });
    }, 50);
}

/**
 * Lightweight Markdown Formatter for v0.6.2
 * Handles: #### (H4), - (Bullets), and `code`
 */
function formatMarkdown(text) {
    if (!text) return "";
    let fmt = text;

    // --- HTML Escaping for Code Stability ---
    // We escape < and > globally, then restore tags we actually want (h4, ul, li)
    const escapeHTML = (str) => str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

    // 1. Triple Backtick Code Blocks (Multi-line)
    fmt = fmt.replace(/```(\w*)\n([\s\S]*?)```/g, (match, lang, code) => {
        return `<pre class="code-block h-scroll"><code>${escapeHTML(code.trim())}</code></pre>`;
    });

    // 2. Inline Code
    fmt = fmt.replace(/`(.*?)`/g, (match, code) => `<code>${escapeHTML(code)}</code>`);

    // 3. Headers
    fmt = fmt.replace(/^#### (.*$)/gim, '<h4>$1</h4>');

    // 3.5. Links [text](url)
    fmt = fmt.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" class="chat-link">$1</a>');

    // 4. Bullets
    fmt = fmt.replace(/^\- (.*$)/gim, '<li>$1</li>');

    // 5. Wrap lists
    if (fmt.includes('<li>')) {
        fmt = fmt.replace(/(<li>.*<\/li>)/gms, '<ul>$1</ul>');
    }

    // 6. Newlines to breaks (if not in pre blocks)
    // We only apply <br> to areas not wrapped in <pre>
    const chunks = fmt.split(/(<pre[\s\S]*?<\/pre>)/g);
    fmt = chunks.map(chunk => {
        if (chunk.startsWith('<pre')) return chunk;
        return chunk.replace(/\n/g, '<br>');
    }).join('');

    return fmt;
}

function appendTelemetryChip(data, container) {
    if (!data || data.matching_query === 'None') return;
    
    const chip = document.createElement('div');
    chip.className = 'telemetry-chip slide-in';
    const confColor = data.confidence > 0.8 ? '#22c55e' : (data.confidence > 0.5 ? '#f59e0b' : '#ef4444');
    
    chip.innerHTML = `
        <span class="chip-node">🎯 Node: ${data.matching_query}</span>
        <span class="chip-divider"></span>
        <span class="chip-conf" style="color:${confColor}">⚡ Conf: ${(data.confidence * 100).toFixed(0)}%</span>
    `;
    container.appendChild(chip);
}

function addCopyButton(bubble, text) {
    const btn = document.createElement('button');
    btn.className = 'copy-btn';
    btn.innerHTML = '📄 Copy';
    btn.onclick = () => {
        navigator.clipboard.writeText(text);
        btn.innerHTML = '✅ Copied';
        setTimeout(() => btn.innerHTML = '📄 Copy', 2000);
    };
    bubble.appendChild(btn);
}

function appendMessage(text, sender, metadata = null) {
    const wrapper = document.createElement('div');
    wrapper.className = `chat-bubble-wrapper ${sender}`;
    
    if (metadata && sender === 'bot') {
        appendTelemetryChip(metadata, wrapper);
    }

    const msg = document.createElement('div');
    msg.className = `chat-bubble ${sender} slide-in`;
    
    const formatted = sender === 'bot' ? formatMarkdown(text) : text;
    msg.innerHTML = `<div class="bubble-content">${formatted}</div>`;
    
    if (sender === 'bot' && text.length > 10) {
        addCopyButton(msg, text);
    }
    
    wrapper.appendChild(msg);
    historyDiv.appendChild(wrapper);
    scrollChat();
    return msg.querySelector('.bubble-content'); // Return reference for streaming updates
}

function toggleTypingDots(show) {
    if (show) {
        const msg = document.createElement('div');
        msg.className = `chat-bubble bot slide-in`;
        msg.id = "typing-msg";
        msg.innerHTML = `<div class="bubble-content"><div class="typing-indicator"><span></span><span></span><span></span></div></div>`;
        historyDiv.appendChild(msg);
        scrollChat();
    } else {
        const el = document.getElementById('typing-msg');
        if (el) el.remove();
    }
}

function updateDebug(data) {
    if (!data) return;
    document.getElementById('d-node').innerText = data.matching_query || '--';
    document.getElementById('d-sim').innerText = data.similarity ? data.similarity.toFixed(4) : '0.0000';
    document.getElementById('d-score').innerText = data.final_score ? data.final_score.toFixed(4) : '0.0000';
    document.getElementById('d-reason').innerText = data.reason || 'No semantic routing applied.';
}

function handleKeyPress(e) {
    if (e.key === 'Enter') sendMessage();
}

// =========================================================
// ===  CONTEXT MANAGEMENT  ================================
// =========================================================

let _contextNodes = [];   // Flat array of all ad-hoc nodes
let _contextFiles = [];   // [{ filename, nodeCount }]

async function attachContextFile(event) {
    const file = event.target.files[0];
    event.target.value = '';
    if (!file) return;

    const ext = file.name.split('.').pop().toLowerCase();
    const MAX_MB = 50;
    if (file.size > MAX_MB * 1024 * 1024) {
        showToast('File Too Large', `Max file size for context is ${MAX_MB}MB.`, 'error');
        return;
    }

    showProgress('Processing Context File', file.name);
    const fd = new FormData();
    fd.append('file', file);

    // For CSV, peek headers first
    if (ext === 'csv') {
        try {
            const peekRes = await fetch(`${API_BASE}/knowledge/csv-headers`, { method: 'POST', body: fd });
            const peekData = await peekRes.json();
            hideProgress();
            if (!peekRes.ok || !peekData.headers?.length) {
                showToast('CSV Error', peekData.error || 'No headers found.', 'error');
                return;
            }
            await _showCsvContextMapper(file, peekData.headers);
            return;
        } catch(e) {
            hideProgress();
            showToast('Network Error', 'Could not read CSV headers.', 'error');
            return;
        }
    }

    await _doContextFetch(file, null, null);
}

async function _showCsvContextMapper(file, headers) {
    const opts = headers.map(h => `<option value="${h}">${h}</option>`).join('');
    const overlay = document.createElement('div');
    overlay.className = 'fullscreen-modal';
    overlay.style.cssText = 'z-index:600;background:rgba(0,0,0,0.8);';
    overlay.innerHTML = `
        <div class="editor-box" style="width:440px;">
            <h3 style="margin-bottom:6px;">Map Context Columns</h3>
            <p style="font-size:0.85rem;color:var(--text-muted);margin-bottom:20px;">${file.name} — context only, not saved permanently</p>
            <div class="form-group">
                <label style="font-size:0.8rem;color:var(--text-muted);display:block;margin-bottom:6px;">Query Column</label>
                <select id="ctx-qcol" style="width:100%;background:var(--bg-panel);border:1px solid var(--border);color:var(--text-primary);padding:12px;border-radius:6px;">${opts}</select>
            </div>
            <div class="form-group">
                <label style="font-size:0.8rem;color:var(--text-muted);display:block;margin-bottom:6px;">Answer Column</label>
                <select id="ctx-acol" style="width:100%;background:var(--bg-panel);border:1px solid var(--border);color:var(--text-primary);padding:12px;border-radius:6px;">${opts}</select>
            </div>
            <div style="display:flex;gap:12px;justify-content:flex-end;margin-top:24px;">
                <button class="btn" id="ctx-cancel">Cancel</button>
                <button class="btn active" id="ctx-confirm">Add to Context</button>
            </div>
        </div>`;
    document.body.appendChild(overlay);

    const qSel = document.getElementById('ctx-qcol');
    const aSel = document.getElementById('ctx-acol');
    qSel.value = headers.find(h => /query|question|input|prompt|code/i.test(h)) || headers[0];
    aSel.value = headers.find(h => /answer|response|output|doc|context|documentation/i.test(h)) || headers[headers.length - 1];

    document.getElementById('ctx-cancel').onclick = () => overlay.remove();
    document.getElementById('ctx-confirm').onclick = async () => {
        const qCol = qSel.value, aCol = aSel.value;
        overlay.remove();
        await _doContextFetch(file, qCol, aCol);
    };
}

async function _doContextFetch(file, queryCol, answerCol) {
    const fd = new FormData();
    fd.append('file', file);
    if (queryCol)  fd.append('query_col', queryCol);
    if (answerCol) fd.append('answer_col', answerCol);

    showProgress('Loading Context', `Extracting nodes from ${file.name}...`);
    try {
        const res = await fetch(`${API_BASE}/chat/context`, { method: 'POST', body: fd });
        const data = await res.json();
        hideProgress();

        if (res.ok && data.status === 'success') {
            _contextNodes.push(...data.nodes);
            _contextFiles.push({ filename: file.name, nodeCount: data.nodes.length });
            _renderContextStrip();
            showToast('Context Loaded', `${data.nodes.length} nodes from "${file.name}" — active for this session.`, 'success', 5000);
        } else {
            showToast(data.status === 'skipped' ? 'Nothing Extracted' : 'Context Failed',
                data.message || data.error,
                data.status === 'skipped' ? 'warning' : 'error');
        }
    } catch(e) {
        hideProgress();
        showToast('Upload Failed', 'Could not reach backend.', 'error');
    }
}

function _renderContextStrip() {
    const strip = document.getElementById('context-strip');
    const badgesEl = document.getElementById('context-badges');

    if (_contextFiles.length === 0) {
        strip.classList.add('hidden');
        return;
    }

    strip.classList.remove('hidden');
    badgesEl.innerHTML = _contextFiles.map((f, i) => `
        <span class="context-badge active">
            📄 ${f.filename} <span style="opacity:0.6">(${f.nodeCount})</span>
            <button class="context-badge-remove" onclick="removeContextFile(${i})">×</button>
        </span>`).join('');
}

function removeContextFile(idx) {
    const removed = _contextFiles.splice(idx, 1)[0];
    // Rebuild node pool (remove nodes from that file)
    _contextNodes = _contextNodes.filter(n => n.source !== `attached:${removed.filename}`);
    _renderContextStrip();
    showToast('Context Removed', `"${removed.filename}" detached.`, 'info', 3000);
}

function clearAllContext() {
    _contextNodes = [];
    _contextFiles = [];
    _renderContextStrip();
    showToast('Context Cleared', 'All attached files removed.', 'info', 2500);
}

// =========================================================
// ===  CHAT  ==============================================
// =========================================================

async function sendMessage() {
    console.log("SM: Initializing Neural Transmission...");
    const input = document.getElementById('chat-input');
    const text = input.value.trim();
    if (!text) return;

    // --- Raindrop Shatter & Progress State ---
    const btn = document.querySelector('.fluid-send-btn');
    btn.classList.add('active-send');

    // --- Radial Ripple Effect ---
    const ripple = document.createElement('span');
    ripple.className = 'ripple';
    btn.appendChild(ripple);
    setTimeout(() => ripple.remove(), 600);
    
    appendMessage(text, 'user');
    input.value = '';
    toggleTypingDots(true);

    try {
        const payload = { message: text };
        if (_contextNodes.length > 0) payload.ad_hoc_knowledge = _contextNodes;

        const response = await fetch(`${API_BASE}/chat/stream`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) throw new Error('Network reach failure');

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let botContentRef = null;
        let accumulatedText = "";
        let metaReceived = false;

        toggleTypingDots(false);

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            const lines = chunk.split('\n');

            for (const line of lines) {
                if (!line.startsWith('data: ')) continue;
                const jsonStr = line.replace('data: ', '').trim();
                try {
                    const data = JSON.parse(jsonStr);

                    if (data.type === 'metadata' && !metaReceived) {
                        metaReceived = true;
                        
                        // Switch to success checkmark on first metadata/content received
                        btn.classList.remove('active-send');
                        btn.classList.add('active-success');
                        
                        // Reset button to raindrop after 2 seconds of success
                        setTimeout(() => {
                            btn.classList.remove('active-success');
                        }, 2000);
                        
                        botContentRef = appendMessage("", 'bot', data);
                        // Add context badge if needed
                        const isCtx = data.source && data.source.startsWith('attached:');
                        if (isCtx) {
                            const badge = document.createElement('span');
                            badge.className = 'bubble-source';
                            badge.innerHTML = `📎 Using context: ${data.source.replace('attached:', '')}`;
                            botContentRef.parentElement.appendChild(badge);
                        }
                    } else if (data.type === 'content') {
                        // Also trigger success if we get content before metadata for some reason
                        if (!metaReceived) {
                            btn.classList.remove('active-send');
                            btn.classList.add('active-success');
                            setTimeout(() => {
                                btn.classList.remove('active-success');
                            }, 2000);
                        }
                        accumulatedText += data.delta;
                        if (botContentRef) {
                            botContentRef.innerHTML = formatMarkdown(accumulatedText);
                        }
                    } else if (data.type === 'error') {
                        appendMessage(`Neural error: ${data.message}`, 'system');
                    }
                } catch (e) {
                    console.error("Chunk parse error:", e);
                }
            }
        }
        
        // Reset button after slight delay
        setTimeout(() => {
            btn.classList.remove('active-success', 'active-processing', 'active-send');
        }, 1500);
        
        scrollChat();

    } catch (e) {
        toggleTypingDots(false);
        appendMessage(`Connection refused or stream broken: ${e.message}`, 'system');
    }
}

// =========================================================
// ===  CHAT EXPORT  =======================================
// =========================================================

function exportChat() {
    const bubbles = document.querySelectorAll('#chat-history .chat-bubble');
    if (!bubbles.length) {
        showToast('Nothing to Export', 'No chat messages yet.', 'warning');
        return;
    }

    const now = new Date();
    const ts = now.toISOString().slice(0, 16).replace('T', ' ');
    const lines = [`# MMF Chat Export\n_Exported: ${ts}_\n`];
    const ctxList = _contextFiles.map(f => `- ${f.filename} (${f.nodeCount} nodes)`).join('\n');
    if (ctxList) lines.push(`## Active Context Files\n${ctxList}\n`);
    lines.push(`---\n`);

    bubbles.forEach(bubble => {
        const isUser   = bubble.classList.contains('user');
        const isBot    = bubble.classList.contains('bot');
        const isSystem = bubble.classList.contains('system');
        // Get text only (strip source badge spans)
        const clone = bubble.querySelector('.bubble-content').cloneNode(true);
        clone.querySelectorAll('.bubble-source').forEach(el => el.remove());
        const text = clone.innerText.trim();
        if (!text) return;

        if (isUser)   lines.push(`**You:** ${text}\n`);
        else if (isBot)   lines.push(`**MMF:** ${text}\n`);
        else if (isSystem) lines.push(`> 🔧 *${text}*\n`);
    });

    const blob = new Blob([lines.join('\n')], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `mmf-chat-${now.toISOString().slice(0,10)}.md`;
    a.click();
    URL.revokeObjectURL(url);
    showToast('Chat Exported', `Saved as mmf-chat-${now.toISOString().slice(0,10)}.md`, 'success');
}

// =========================================================
// ===  KNOWLEDGE TABLE  ===================================
// =========================================================

let _knowledgeCache = [];

async function fetchKnowledge() {
    try {
        const res = await fetch(`${API_BASE}/knowledge`);
        const data = await res.json();
        renderTable(data);
    } catch (e) {
        showToast('Load Failed', 'Could not fetch knowledge nodes.', 'error');
    }
}

function renderTable(data) {
    _knowledgeCache = data;
    const tbody = document.getElementById('k-tbody');
    tbody.innerHTML = '';
    document.getElementById('select-all-cb').checked = false;
    updateBulkToolbar();

    data.forEach(item => {
        const tr = document.createElement('tr');
        tr.dataset.id = item.id;
        let qs = item.queries ? item.queries.join(', ') : (item.query || '');
        if (qs.length > 50) qs = qs.substring(0, 47) + '...';
        let ans = item.response || '';
        if (ans.length > 70) ans = ans.substring(0, 67) + '...';
        tr.innerHTML = `
            <td><input type="checkbox" class="row-cb" value="${item.id}" onchange="onRowCheckChange()"></td>
            <td>${qs}</td>
            <td>${ans}</td>
            <td>
                <button class="btn" style="padding:5px 10px;margin-right:5px;" onclick="openAddEditor('${item.id}')">Edit</button>
                <button class="btn" style="padding:5px 10px;background:#EF4444;border-color:#EF4444;color:#fff;" onclick="deleteKnowledge('${item.id}')">Drop</button>
            </td>`;
        tbody.appendChild(tr);
    });
}

// =========================================================
// ===  SELECTION  =========================================
// =========================================================

function toggleSelectAll(masterCb) {
    document.querySelectorAll('.row-cb').forEach(cb => cb.checked = masterCb.checked);
    updateBulkToolbar();
}

function onRowCheckChange() {
    const all = document.querySelectorAll('.row-cb');
    const checked = document.querySelectorAll('.row-cb:checked');
    document.getElementById('select-all-cb').checked = all.length > 0 && all.length === checked.length;
    updateBulkToolbar();
}

function getSelectedIds() {
    return [...document.querySelectorAll('.row-cb:checked')].map(cb => cb.value);
}

function updateBulkToolbar() {
    const ids = getSelectedIds();
    const toolbar = document.getElementById('bulk-toolbar');
    document.getElementById('bulk-count').textContent = `${ids.length} selected`;
    toolbar.classList.toggle('hidden', ids.length === 0);
}

// =========================================================
// ===  BULK ACTIONS  ======================================
// =========================================================

async function deleteSelectedNodes() {
    const ids = getSelectedIds();
    if (!ids.length) return;
    const ok = await showConfirm(`Delete ${ids.length} node(s) permanently?`, '🗑️');
    if (!ok) return;

    showProgress('Deleting Nodes', `Removing ${ids.length} entries...`);
    try {
        const res = await fetch(`${API_BASE}/knowledge/bulk-delete`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ids })
        });
        const data = await res.json();
        hideProgress();
        if (res.ok) {
            showToast('Deleted', `${data.removed} node(s) removed.`, 'success');
            fetchKnowledge();
        } else {
            showToast('Delete Failed', data.error, 'error');
        }
    } catch(e) {
        hideProgress();
        showToast('Request Failed', 'Could not reach backend.', 'error');
    }
}

function exportSelectedNodes() {
    const ids = new Set(getSelectedIds());
    const rows = _knowledgeCache.filter(item => ids.has(item.id));
    if (!rows.length) return;
    const header = ['query', 'response', 'confidence', 'source'];
    const csvLines = [header.join(',')];
    rows.forEach(item => {
        const q = (item.queries ? item.queries[0] : item.query || '').replace(/"/g, '""');
        const r = (item.response || '').replace(/"/g, '""');
        csvLines.push(`"${q}","${r}","${item.confidence || ''}","${item.source || ''}"`);
    });
    const blob = new Blob([csvLines.join('\n')], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = 'selected_nodes.csv'; a.click();
    URL.revokeObjectURL(url);
    showToast('Exported', `${rows.length} nodes exported as CSV.`, 'success');
}

// =========================================================
// ===  EXPORT / IMPORT  ===================================
// =========================================================

function toggleExportMenu(e) {
    e.stopPropagation();
    const menu = document.getElementById('export-menu');
    menu.classList.toggle('hidden');
    document.addEventListener('click', () => menu.classList.add('hidden'), { once: true });
}
function exportMatrix() { window.open(`${API_BASE}/knowledge/export`, '_blank'); }
function exportNodes()  { window.open(`${API_BASE}/knowledge/export/nodes`, '_blank'); }

async function importKnowledge(event) {
    const file = event.target.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    showProgress('Importing Brain', 'Extracting .mmf binary and hot-reloading...');
    try {
        const res = await fetch(`${API_BASE}/knowledge/import`, { method: 'POST', body: formData });
        const data = await res.json();
        hideProgress();
        if (res.ok) {
            showToast('Brain Swapped', 'New .mmf imported and engine reloaded.', 'success');
            fetchKnowledge();
        } else {
            showToast('Import Failed', data.error, 'error');
        }
    } catch(e) {
        hideProgress();
        showToast('Upload Failed', 'Could not reach backend.', 'error');
    }
    event.target.value = '';
}

// ---- CSV Column Mapping State ----
let _pendingIngestFile = null;

async function ingestDocument(event) {
    const file = event.target.files[0];
    event.target.value = '';
    if (!file) return;

    const ext = file.name.split('.').pop().toLowerCase();

    // For CSV: peek headers first and let user map columns
    if (ext === 'csv') {
        _pendingIngestFile = file;
        await _showCsvColumnMapper(file);
        return;
    }

    // Non-CSV: ingest directly
    await _doIngest(file, null, null);
}

async function _showCsvColumnMapper(file) {
    // Peek headers from backend
    showProgress('Reading CSV Headers', file.name);
    const fd = new FormData();
    fd.append('file', file);
    let headers = [];
    try {
        const res = await fetch(`${API_BASE}/knowledge/csv-headers`, { method: 'POST', body: fd });
        const data = await res.json();
        hideProgress();
        if (!res.ok) { showToast('CSV Error', data.error, 'error'); return; }
        headers = data.headers || [];
    } catch(e) {
        hideProgress();
        showToast('Network Error', 'Could not read CSV headers.', 'error');
        return;
    }

    if (headers.length === 0) {
        showToast('Empty CSV', 'No headers found in file.', 'warning');
        return;
    }

    // Build options HTML
    const opts = headers.map(h => `<option value="${h}">${h}</option>`).join('');

    // Inject a temporary mapper modal
    const overlay = document.createElement('div');
    overlay.className = 'fullscreen-modal';
    overlay.style.cssText = 'z-index:600;background:rgba(0,0,0,0.8);';
    overlay.innerHTML = `
        <div class="editor-box" style="width:460px;">
            <h3 style="margin-bottom:6px;">Map CSV Columns</h3>
            <p style="font-size:0.85rem;color:var(--text-muted);margin-bottom:20px;">${file.name} — ${headers.length} columns detected</p>
            <div class="form-group">
                <label style="font-size:0.8rem;color:var(--text-muted);display:block;margin-bottom:6px;">Query Column (what users ask)</label>
                <select id="csv-query-col" style="width:100%;background:var(--bg-panel);border:1px solid var(--border);color:var(--text-primary);padding:12px;border-radius:6px;font-size:0.95rem;">${opts}</select>
            </div>
            <div class="form-group">
                <label style="font-size:0.8rem;color:var(--text-muted);display:block;margin-bottom:6px;">Answer Column (what the engine returns)</label>
                <select id="csv-answer-col" style="width:100%;background:var(--bg-panel);border:1px solid var(--border);color:var(--text-primary);padding:12px;border-radius:6px;font-size:0.95rem;">${opts}</select>
            </div>
            <div style="display:flex;gap:12px;justify-content:flex-end;margin-top:24px;">
                <button class="btn" id="csv-cancel-btn">Cancel</button>
                <button class="btn active" id="csv-confirm-btn">Ingest File</button>
            </div>
        </div>`;
    document.body.appendChild(overlay);

    // Try to pre-select sensible defaults
    const qSel = document.getElementById('csv-query-col');
    const aSel = document.getElementById('csv-answer-col');
    const queryGuess  = headers.find(h => /query|question|input|prompt|code/i.test(h)) || headers[0];
    const answerGuess = headers.find(h => /answer|response|output|doc|context|documentation/i.test(h)) || headers[headers.length - 1];
    qSel.value = queryGuess;
    aSel.value = answerGuess;

    document.getElementById('csv-cancel-btn').onclick = () => overlay.remove();
    document.getElementById('csv-confirm-btn').onclick = async () => {
        const qCol = qSel.value;
        const aCol = aSel.value;
        overlay.remove();
        await _doIngest(_pendingIngestFile, qCol, aCol);
        _pendingIngestFile = null;
    };
}

async function _doIngest(file, queryCol, answerCol) {
    const formData = new FormData();
    formData.append('file', file);
    if (queryCol)  formData.append('query_col',  queryCol);
    if (answerCol) formData.append('answer_col', answerCol);

    showProgress('Ingesting Document', `${file.name}${queryCol ? ` · query: ${queryCol} → ${answerCol}` : ''}`);
    try {
        const res = await fetch(`${API_BASE}/knowledge/ingest`, { method: 'POST', body: formData });
        const data = await res.json();
        hideProgress();
        if (res.ok && data.status === 'success') {
            showToast('Ingestion Complete',
                `Extracted: ${data.extracted} · Added: ${data.added} · Merged: ${data.merged} · Skipped: ${data.skipped}`,
                'success', 7000);
            fetchKnowledge();
        } else {
            showToast(data.status === 'skipped' ? 'Nothing Extracted' : 'Ingestion Failed',
                data.message || data.error, data.status === 'skipped' ? 'warning' : 'error');
        }
    } catch(e) {
        hideProgress();
        showToast('Upload Failed', 'Could not reach backend.', 'error');
    }
}

// =========================================================
// ===  HUGGING FACE IMPORT  ===============================
// =========================================================

function toggleHFModal() {
    document.getElementById('hf-modal').classList.toggle('hidden');
}

async function submitHFImport() {
    const dataset_id = document.getElementById('hf-dataset-id').value.trim();
    const query_col  = document.getElementById('hf-query-col').value.trim();
    const answer_col = document.getElementById('hf-answer-col').value.trim();
    const config     = document.getElementById('hf-config').value.trim() || 'default';
    const split      = document.getElementById('hf-split').value.trim() || 'train';
    const limit      = parseInt(document.getElementById('hf-limit').value) || 100;

    if (!dataset_id || !query_col || !answer_col) {
        showToast('Validation Error', 'Dataset ID, Query Column, and Answer Column are required.', 'error');
        return;
    }

    toggleHFModal();
    showProgress('Fetching from HuggingFace', `${dataset_id} · split: ${split} · limit: ${limit}`);

    try {
        const res = await fetch(`${API_BASE}/knowledge/import/huggingface`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ dataset_id, query_col, answer_col, config, split, limit })
        });
        const data = await res.json();
        hideProgress();
        if (res.ok && data.status === 'success') {
            showToast(
                'HuggingFace Import Complete',
                `Fetched: ${data.fetched} · Added: ${data.added} · Merged: ${data.merged} · Skipped: ${data.skipped}`,
                'success', 7000
            );
            fetchKnowledge();
        } else {
            showToast('Import Failed', data.error || data.message, 'error');
        }
    } catch(e) {
        hideProgress();
        showToast('Network Error', 'Could not reach backend.', 'error');
    }
}

// =========================================================
// ===  SINGLE NODE CRUD  ==================================
// =========================================================

let currentEditorId = null;

async function openAddEditor(id = null) {
    currentEditorId = id;
    document.getElementById('editor-modal').classList.remove('hidden');
    if (id) {
        document.getElementById('editor-title').innerText = 'Modify Neural Node';
        const res = await fetch(`${API_BASE}/knowledge`);
        const data = await res.json();
        const item = data.find(i => i.id === id);
        if (item) {
            document.getElementById('m-query').value = item.queries ? item.queries[0] : item.query;
            document.getElementById('m-response').value = item.response;
        }
    } else {
        document.getElementById('editor-title').innerText = 'Inject Neural Node';
        document.getElementById('m-query').value = '';
        document.getElementById('m-response').value = '';
    }
}

function closeEditorModal() {
    document.getElementById('editor-modal').classList.add('hidden');
}

async function saveKnowledge() {
    const q = document.getElementById('m-query').value.trim();
    const r = document.getElementById('m-response').value.trim();
    if (!q || !r) { showToast('Validation Error', 'Query and response cannot be empty.', 'error'); return; }
    const endpoint = currentEditorId ? `${API_BASE}/knowledge/${currentEditorId}` : `${API_BASE}/knowledge`;
    const method   = currentEditorId ? 'PUT' : 'POST';
    try {
        const res = await fetch(endpoint, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: q, response: r })
        });
        if (res.ok) {
            showToast('Saved', currentEditorId ? 'Node updated.' : 'Node injected.', 'success');
            closeEditorModal();
            fetchKnowledge();
        } else {
            const data = await res.json();
            showToast('Save Failed', data.error, 'error');
        }
    } catch(e) { showToast('Request Failed', 'Could not reach backend.', 'error'); }
}

async function deleteKnowledge(id) {
    const ok = await showConfirm('Permanently delete this node?', '🗑️');
    if (!ok) return;
    try {
        const res = await fetch(`${API_BASE}/knowledge/${id}`, { method: 'DELETE' });
        if (res.ok) {
            showToast('Deleted', 'Node removed successfully.', 'success');
            fetchKnowledge();
        } else {
            const d = await res.json();
            showToast('Delete Failed', d.error, 'error');
        }
    } catch(e) { showToast('Request Failed', 'Could not reach backend.', 'error'); }
}
