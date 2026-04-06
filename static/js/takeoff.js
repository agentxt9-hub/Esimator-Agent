/**
 * takeoff.js — ZenBid Takeoff Module
 * Session 18 — Foundation: PDF viewer, pan/zoom, page nav, item CRUD
 * Drawing tools (Session 19) will extend this state object.
 */
'use strict';

const TK = (() => {

    // ── State ────────────────────────────────────────────────────────────────
    const state = {
        projectId: null,
        plans: [],          // parsed from embedded JSON
        currentPlanId: null,
        currentPageId: null,
        currentPageNum: 1,
        pdfDoc: null,
        renderTask: null,   // in-flight PDF render task (to cancel on page change)
        zoom: 1.0,
        panX: 0,
        panY: 0,
        isPanning: false,
        lastMouseX: 0,
        lastMouseY: 0,
        activeTool: 'select',
        items: [],
        leftCollapsed: false,
        rightCollapsed: false,
    };

    // ── DOM refs (set on init) ────────────────────────────────────────────────
    let pdfCanvas, overlayCanvas, pdfCtx, overlayCtx, canvasWrap;

    // ── Init ─────────────────────────────────────────────────────────────────
    function init() {
        state.projectId = JSON.parse(
            document.getElementById('tk-project-id').textContent
        );
        state.plans = JSON.parse(
            document.getElementById('tk-plans-data').textContent
        ) || [];

        pdfCanvas    = document.getElementById('pdf-canvas');
        overlayCanvas = document.getElementById('overlay-canvas');
        pdfCtx       = pdfCanvas.getContext('2d');
        overlayCtx   = overlayCanvas.getContext('2d');
        canvasWrap   = document.getElementById('tk-canvas-wrap');

        _bindEvents();
        _renderPageList();
        fetchItems();

        if (state.plans.length > 0) {
            const firstPlan = state.plans[0];
            if (firstPlan.pages && firstPlan.pages.length > 0) {
                const firstPage = firstPlan.pages[0];
                loadPDF(firstPlan.id, firstPage.id, firstPage.page_number);
            }
        } else {
            document.getElementById('tk-empty-state').style.display = 'flex';
        }
    }

    // ── Event binding ─────────────────────────────────────────────────────────
    function _bindEvents() {
        // Mouse wheel zoom on canvas wrap
        canvasWrap.addEventListener('wheel', _onWheel, { passive: false });

        // Middle-mouse pan + left-drag pan (space bar hold for pan mode TBD in S19)
        overlayCanvas.addEventListener('mousedown', _onMouseDown);
        window.addEventListener('mousemove', _onMouseMove);
        window.addEventListener('mouseup',   _onMouseUp);

        // Mousemove → update status bar coordinates
        overlayCanvas.addEventListener('mousemove', _updateCoordsDisplay);

        // Keyboard shortcuts
        window.addEventListener('keydown', _onKeyDown);

        // Color swatches in new-item modal
        document.querySelectorAll('.color-swatch').forEach(el => {
            el.addEventListener('click', () => {
                document.querySelectorAll('.color-swatch').forEach(s => s.classList.remove('selected'));
                el.classList.add('selected');
                document.getElementById('ni-color').value = el.dataset.color;
            });
        });

        // Tool buttons
        document.querySelectorAll('.tool-btn[data-tool]').forEach(btn => {
            btn.addEventListener('click', () => {
                if (btn.dataset.tool === 'scale') { openScaleModal(); return; }
                if (btn.dataset.tool === 'fit')   { zoomToFit(); return; }
                if (btn.dataset.tool === 'print') { return; }  // handled inline
                setActiveTool(btn.dataset.tool);
            });
        });
    }

    // ── Tool management ───────────────────────────────────────────────────────
    function setActiveTool(tool) {
        state.activeTool = tool;
        document.querySelectorAll('.tool-btn[data-tool]').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tool === tool);
        });
        overlayCanvas.style.cursor = tool === 'select' ? 'default' : 'crosshair';
    }

    // ── PDF loading ───────────────────────────────────────────────────────────
    function loadPDF(planId, pageId, pageNum) {
        state.currentPlanId = planId;
        state.currentPageId = pageId;
        state.currentPageNum = pageNum;

        const url = `/project/${state.projectId}/takeoff/plan/${planId}/pdf`;
        pdfjsLib.getDocument(url).promise.then(doc => {
            state.pdfDoc = doc;
            renderPage(pageNum);
        }).catch(err => {
            console.error('PDF load error:', err);
        });
    }

    function renderPage(pageNum) {
        if (!state.pdfDoc) return;

        // Cancel any in-flight render
        if (state.renderTask) {
            state.renderTask.cancel();
            state.renderTask = null;
        }

        state.pdfDoc.getPage(pageNum).then(page => {
            const viewport = page.getViewport({ scale: state.zoom });

            pdfCanvas.width     = viewport.width;
            pdfCanvas.height    = viewport.height;
            overlayCanvas.width  = viewport.width;
            overlayCanvas.height = viewport.height;

            // Apply pan via CSS transform on the canvases
            _applyTransform();

            const task = page.render({ canvasContext: pdfCtx, viewport });
            state.renderTask = task;

            task.promise.then(() => {
                state.renderTask = null;
                renderOverlays();
                _updateStatusBar();
            }).catch(err => {
                if (err.name !== 'RenderingCancelledException') {
                    console.error('Render error:', err);
                }
            });
        });
    }

    function _applyTransform() {
        const transform = `translate(${state.panX}px, ${state.panY}px)`;
        pdfCanvas.style.transform     = transform;
        overlayCanvas.style.transform = transform;
    }

    // ── Overlays (placeholder — drawing tools in Session 19) ─────────────────
    function renderOverlays() {
        overlayCtx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);
        // Session 19: draw measurements on current page here
        _updateDataTable();
    }

    // ── Pan / Zoom ────────────────────────────────────────────────────────────
    function _onWheel(e) {
        e.preventDefault();
        const delta = e.deltaY < 0 ? 0.1 : -0.1;
        zoom(delta);
    }

    function zoom(delta) {
        state.zoom = Math.max(0.1, Math.min(8.0, state.zoom + delta));
        if (state.pdfDoc) renderPage(state.currentPageNum);
        _updateZoomDisplay();
    }

    function zoomToFit() {
        if (!pdfCanvas.width) return;
        const wrapW = canvasWrap.clientWidth;
        const wrapH = canvasWrap.clientHeight;
        const scaleX = wrapW / (pdfCanvas.width  / state.zoom);
        const scaleY = wrapH / (pdfCanvas.height / state.zoom);
        state.zoom = Math.min(scaleX, scaleY) * 0.95;
        state.panX = 0;
        state.panY = 0;
        if (state.pdfDoc) renderPage(state.currentPageNum);
        _updateZoomDisplay();
    }

    function _onMouseDown(e) {
        if (e.button === 1 || e.button === 0) {   // middle or left
            state.isPanning = true;
            state.lastMouseX = e.clientX;
            state.lastMouseY = e.clientY;
            overlayCanvas.style.cursor = 'grabbing';
        }
    }

    function _onMouseMove(e) {
        if (!state.isPanning) return;
        state.panX += e.clientX - state.lastMouseX;
        state.panY += e.clientY - state.lastMouseY;
        state.lastMouseX = e.clientX;
        state.lastMouseY = e.clientY;
        _applyTransform();
    }

    function _onMouseUp() {
        state.isPanning = false;
        overlayCanvas.style.cursor = state.activeTool === 'select' ? 'default' : 'crosshair';
    }

    // ── Keyboard shortcuts ────────────────────────────────────────────────────
    function _onKeyDown(e) {
        // Ignore when typing in an input
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

        switch (e.key) {
            case 'f':
            case 'F':
                zoomToFit();
                break;
            case 'ArrowRight':
                _nextPage();
                break;
            case 'ArrowLeft':
                _prevPage();
                break;
            case 'Escape':
                setActiveTool('select');
                break;
            case 'Delete':
                // Session 19: delete selected measurement
                break;
        }
    }

    // ── Page navigation ───────────────────────────────────────────────────────
    function _nextPage() {
        const plan = state.plans.find(p => p.id === state.currentPlanId);
        if (!plan) return;
        const idx = plan.pages.findIndex(p => p.id === state.currentPageId);
        if (idx < plan.pages.length - 1) {
            const next = plan.pages[idx + 1];
            loadPage(next.id, next.page_number);
        }
    }

    function _prevPage() {
        const plan = state.plans.find(p => p.id === state.currentPlanId);
        if (!plan) return;
        const idx = plan.pages.findIndex(p => p.id === state.currentPageId);
        if (idx > 0) {
            const prev = plan.pages[idx - 1];
            loadPage(prev.id, prev.page_number);
        }
    }

    function loadPage(pageId, pageNum) {
        state.currentPageId  = pageId;
        state.currentPageNum = pageNum;
        state.panX = 0;
        state.panY = 0;
        renderPage(pageNum);
        _highlightActivePage();
        _updateStatusBar();
    }

    // ── Page list sidebar ─────────────────────────────────────────────────────
    function _renderPageList(filterText = '') {
        const list = document.getElementById('tk-page-list');
        list.innerHTML = '';
        const q = filterText.toLowerCase();

        state.plans.forEach(plan => {
            const pages = plan.pages.filter(p =>
                !q || p.page_name.toLowerCase().includes(q)
            );
            if (pages.length === 0) return;

            // Plan header
            const header = document.createElement('div');
            header.className = 'plan-header';
            header.textContent = plan.original_filename;
            list.appendChild(header);

            pages.forEach(page => {
                const item = document.createElement('div');
                item.className = 'page-thumb-item';
                item.dataset.pageId = page.id;
                item.dataset.pageNum = page.page_number;

                const thumb = page.thumbnail_url
                    ? `<img src="${page.thumbnail_url}" class="page-thumb-img" loading="lazy" alt="">`
                    : `<div class="page-thumb-placeholder">📄</div>`;

                item.innerHTML = `
                    ${thumb}
                    <span class="page-thumb-name">${_escHtml(page.page_name)}</span>
                `;
                item.addEventListener('click', () => {
                    state.currentPlanId = plan.id;
                    loadPage(page.id, page.page_number);
                });
                list.appendChild(item);
            });
        });
    }

    function _highlightActivePage() {
        document.querySelectorAll('.page-thumb-item').forEach(el => {
            el.classList.toggle('active', el.dataset.pageId == state.currentPageId);
        });
    }

    function filterPages(text) {
        _renderPageList(text);
        _highlightActivePage();
    }

    // ── Right sidebar — items list ────────────────────────────────────────────
    function fetchItems() {
        fetch(`/project/${state.projectId}/takeoff/items`)
            .then(r => r.json())
            .then(items => {
                state.items = items;
                _renderItemList();
                _updateDataTable();
            })
            .catch(err => console.error('fetchItems:', err));
    }

    function _renderItemList(filterText = '') {
        const list = document.getElementById('tk-item-list');
        list.innerHTML = '';
        const q = filterText.toLowerCase();

        const filtered = state.items.filter(i =>
            !q || i.name.toLowerCase().includes(q)
        );

        if (filtered.length === 0) {
            list.innerHTML = '<div class="tk-empty-msg">No takeoffs yet.<br>Click + New to add one.</div>';
            return;
        }

        filtered.forEach(item => {
            const row = document.createElement('div');
            row.className = 'takeoff-item-row';
            row.dataset.itemId = item.id;

            const unit = _unitForType(item.measurement_type);
            const valStr = item.total > 0
                ? `${item.total.toLocaleString(undefined, {maximumFractionDigits:2})} ${unit}`
                : '—';

            row.innerHTML = `
                <span class="ti-icon">${_iconForType(item.measurement_type)}</span>
                <span class="ti-name">${_escHtml(item.name)}</span>
                <span class="ti-value">${valStr}</span>
                <span class="ti-color-dot" style="background:${item.color}"></span>
                <span class="ti-actions">
                    <button class="ti-del-btn" title="Delete" data-id="${item.id}">&times;</button>
                </span>
            `;

            row.querySelector('.ti-del-btn').addEventListener('click', e => {
                e.stopPropagation();
                if (confirm(`Delete "${item.name}"? This also deletes all measurements.`)) {
                    deleteItem(item.id);
                }
            });

            list.appendChild(row);
        });
    }

    function filterItems(text) {
        _renderItemList(text);
    }

    // ── Floating data table ───────────────────────────────────────────────────
    function _updateDataTable() {
        // Show items that have measurements on the current page
        const tableEl = document.getElementById('tk-data-table');
        const rowsEl  = document.getElementById('tk-dt-rows');

        const pageItems = state.items.filter(i => i.measurement_count > 0);
        if (pageItems.length === 0) {
            tableEl.style.display = 'none';
            return;
        }

        tableEl.style.display = 'block';
        rowsEl.innerHTML = '';

        pageItems.forEach(item => {
            const unit = _unitForType(item.measurement_type);
            const row = document.createElement('div');
            row.className = 'tk-dt-row';
            row.innerHTML = `
                <span class="tk-dt-dot" style="background:${item.color}"></span>
                <span class="tk-dt-name">${_escHtml(item.name)}</span>
                <span class="tk-dt-val">${item.total.toLocaleString(undefined,{maximumFractionDigits:2})} ${unit}</span>
            `;
            rowsEl.appendChild(row);
        });
    }

    // ── Status bar / display updates ──────────────────────────────────────────
    function _updateStatusBar() {
        const plan = state.plans.find(p => p.id === state.currentPlanId);
        const page = plan && plan.pages.find(p => p.id === state.currentPageId);

        document.getElementById('tk-status-page').textContent =
            page ? page.page_name : 'No page selected';

        const scaleEl = document.getElementById('tk-status-scale');
        const badgeEl = document.getElementById('tk-scale-display');
        if (page && page.scale_set) {
            scaleEl.textContent = 'Scale: set';
            badgeEl.textContent = 'Scale: set';
            badgeEl.className = 'scale-badge scale-set';
        } else {
            scaleEl.textContent = 'Scale: not set';
            badgeEl.textContent = '⚠ Scale Not Set';
            badgeEl.className = 'scale-badge scale-unset';
        }

        _updateZoomDisplay();
    }

    function _updateZoomDisplay() {
        const pct = Math.round(state.zoom * 100) + '%';
        document.getElementById('tk-zoom-pct').textContent = pct;
        document.getElementById('tk-status-zoom').textContent = pct;
    }

    function _updateCoordsDisplay(e) {
        if (!pdfCanvas.width) return;
        const rect = overlayCanvas.getBoundingClientRect();
        const x = ((e.clientX - rect.left - state.panX) / state.zoom).toFixed(1);
        const y = ((e.clientY - rect.top  - state.panY) / state.zoom).toFixed(1);
        document.getElementById('tk-status-xy').textContent = `X: ${x}  Y: ${y}`;
    }

    // ── Upload modal ──────────────────────────────────────────────────────────
    function openUploadModal() {
        document.getElementById('upload-modal').style.display = 'flex';
        document.getElementById('upload-progress').style.display = 'none';
        document.getElementById('drop-zone').style.display = 'block';
    }

    function closeUploadModal(e) {
        if (!e || e.target === document.getElementById('upload-modal')) {
            document.getElementById('upload-modal').style.display = 'none';
        }
    }

    function handleDrop(e) {
        e.preventDefault();
        document.getElementById('drop-zone').classList.remove('dragover');
        const file = e.dataTransfer.files[0];
        if (file) handleFileSelect(file);
    }

    function handleFileSelect(file) {
        if (!file) return;
        if (!file.name.toLowerCase().endsWith('.pdf')) {
            alert('Only PDF files are supported.');
            return;
        }
        _uploadFile(file);
    }

    function _uploadFile(file) {
        document.getElementById('drop-zone').style.display = 'none';
        document.getElementById('upload-progress').style.display = 'block';
        document.getElementById('upload-filename').textContent = file.name;
        document.getElementById('upload-status-msg').textContent = 'Uploading…';
        document.getElementById('upload-progress-bar').style.width = '0%';

        const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
        const fd = new FormData();
        fd.append('pdf', file);

        const xhr = new XMLHttpRequest();
        xhr.open('POST', `/project/${state.projectId}/takeoff/upload`);
        xhr.setRequestHeader('X-CSRFToken', csrfToken);

        xhr.upload.onprogress = ev => {
            if (ev.lengthComputable) {
                const pct = Math.round((ev.loaded / ev.total) * 80);
                document.getElementById('upload-progress-bar').style.width = pct + '%';
            }
        };

        xhr.onload = () => {
            document.getElementById('upload-progress-bar').style.width = '90%';
            if (xhr.status === 200) {
                const data = JSON.parse(xhr.responseText);
                if (data.success) {
                    document.getElementById('upload-status-msg').textContent =
                        `Processing ${data.page_count} page(s)…`;
                    document.getElementById('upload-progress-bar').style.width = '100%';
                    setTimeout(() => {
                        closeUploadModal();
                        _onUploadComplete(data);
                    }, 600);
                } else {
                    document.getElementById('upload-status-msg').textContent =
                        'Error: ' + (data.error || 'Upload failed');
                }
            } else {
                document.getElementById('upload-status-msg').textContent =
                    'Upload failed (server error).';
            }
        };
        xhr.onerror = () => {
            document.getElementById('upload-status-msg').textContent = 'Network error.';
        };
        xhr.send(fd);
    }

    function _onUploadComplete(data) {
        // Reload page to get updated plans from server
        // (Simple and reliable; avoids state sync complexity for Session 18)
        window.location.reload();
    }

    // ── New item modal ────────────────────────────────────────────────────────
    function openNewItemModal() {
        document.getElementById('new-item-modal').style.display = 'flex';
        document.getElementById('ni-name').focus();
    }

    function closeNewItemModal(e) {
        if (!e || e.target === document.getElementById('new-item-modal')) {
            document.getElementById('new-item-modal').style.display = 'none';
        }
    }

    function submitNewItem(e) {
        e.preventDefault();
        const payload = {
            name:             document.getElementById('ni-name').value.trim(),
            measurement_type: document.getElementById('ni-type').value,
            color:            document.getElementById('ni-color').value,
            opacity:          parseInt(document.getElementById('ni-opacity').value) / 100,
            assembly_notes:   document.getElementById('ni-notes').value.trim(),
        };
        createItem(payload);
    }

    function createItem(payload) {
        fetch(`/project/${state.projectId}/takeoff/item`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                closeNewItemModal();
                // Reset form
                document.getElementById('ni-name').value = '';
                document.getElementById('ni-notes').value = '';
                fetchItems();
            } else {
                alert('Error: ' + (data.error || 'Could not create takeoff.'));
            }
        })
        .catch(err => console.error('createItem:', err));
    }

    function deleteItem(itemId) {
        fetch(`/project/${state.projectId}/takeoff/item/${itemId}`, {
            method: 'DELETE',
        })
        .then(r => r.json())
        .then(data => {
            if (data.success) fetchItems();
        })
        .catch(err => console.error('deleteItem:', err));
    }

    // ── Scale modal ───────────────────────────────────────────────────────────
    function openScaleModal() {
        document.getElementById('scale-modal').style.display = 'flex';
    }

    function closeScaleModal(e) {
        if (!e || e.target === document.getElementById('scale-modal')) {
            document.getElementById('scale-modal').style.display = 'none';
        }
    }

    function applyScalePreset(val) {
        if (val) document.getElementById('scale-ppf').value = val;
    }

    function saveScale() {
        const ppf = parseFloat(document.getElementById('scale-ppf').value);
        if (!ppf || ppf <= 0) { alert('Enter a valid pixels-per-foot value.'); return; }
        // Session 19: persist to TakeoffPage via PATCH/PUT route
        // For now, update local state
        const plan = state.plans.find(p => p.id === state.currentPlanId);
        if (plan) {
            const page = plan.pages.find(p => p.id === state.currentPageId);
            if (page) {
                page.scale_set = true;
                _updateStatusBar();
            }
        }
        closeScaleModal();
        alert(`Scale set: ${ppf} px/ft. (Persist in Session 19.)`);
    }

    // ── Panel collapse ────────────────────────────────────────────────────────
    function toggleLeft() {
        state.leftCollapsed = !state.leftCollapsed;
        document.getElementById('tk-left').classList.toggle('collapsed', state.leftCollapsed);
        document.getElementById('tk-left-collapse').textContent = state.leftCollapsed ? '▶' : '◀';
    }

    function toggleRight() {
        state.rightCollapsed = !state.rightCollapsed;
        document.getElementById('tk-right').classList.toggle('collapsed', state.rightCollapsed);
    }

    // ── Utilities ─────────────────────────────────────────────────────────────
    function _escHtml(str) {
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }

    function _unitForType(type) {
        switch (type) {
            case 'area': return 'SF';
            case 'count': return 'EA';
            default: return 'FT';
        }
    }

    function _iconForType(type) {
        switch (type) {
            case 'area':             return '▭';
            case 'count':           return '•';
            case 'linear_with_width': return '═';
            case 'segment':         return '╌';
            default:                return '─';
        }
    }

    // ── Public API ────────────────────────────────────────────────────────────
    return {
        init,
        zoom,
        zoomToFit,
        filterPages,
        filterItems,
        fetchItems,
        createItem,
        deleteItem,
        loadPage,
        openUploadModal,
        closeUploadModal,
        handleDrop,
        handleFileSelect,
        openNewItemModal,
        closeNewItemModal,
        submitNewItem,
        openScaleModal,
        closeScaleModal,
        applyScalePreset,
        saveScale,
        toggleLeft,
        toggleRight,
        setActiveTool,
        renderOverlays,
        // Expose state for Session 19 drawing tools
        _state: state,
    };

})();

// Boot on DOMContentLoaded
document.addEventListener('DOMContentLoaded', TK.init);
