/**
 * takeoff.js — ZenBid Takeoff Module
 * Session 18 — Foundation: PDF viewer, page nav, item CRUD
 * Session 18d — Pan/zoom rewrite: GPU-accelerated CSS transforms.
 *   PDF.js renders once at 1.5x base resolution; all pan/zoom uses
 *   CSS transform on #canvas-inner. Quality re-render fires on zoom
 *   end (debounced 300 ms). Drawing tools extend this in Session 19.
 */
'use strict';

const TK = (() => {

    // ── State ────────────────────────────────────────────────────────────────
    const state = {
        projectId: null,
        plans: [],
        currentPlanId: null,
        currentPageId: null,
        currentPageNum: 1,
        pdfDoc: null,
        renderTask: null,       // in-flight PDF render task (cancel on page change)

        // Logical zoom — user-facing "100%" = 1.0
        zoom: 1.0,

        // CSS transform state — resets to 1.0 after each quality re-render
        cssScale: 1.0,
        cssX: 0,
        cssY: 0,

        // PDF decoded at zoom * baseRenderScale for crisp output
        baseRenderScale: 1.5,
        // Zoom value at the last completed PDF decode
        _lastRenderZoom: 1.0,

        // Debounce timer for quality re-render on zoom end
        renderDebounceTimer: null,

        // Space-bar pan mode
        spaceDown: false,
        isPanning: false,
        lastX: 0,
        lastY: 0,

        activeTool: 'select',
        items: [],
        leftCollapsed: false,
        rightCollapsed: false,

        // Touch tracking (pinch zoom)
        _touches: {},
    };

    // ── DOM refs (set on init) ────────────────────────────────────────────────
    let pdfCanvas, overlayCanvas, pdfCtx, overlayCtx, canvasWrap, canvasInner;

    // ── Init ─────────────────────────────────────────────────────────────────
    function init() {
        state.projectId = JSON.parse(
            document.getElementById('tk-project-id').textContent
        );
        state.plans = JSON.parse(
            document.getElementById('tk-plans-data').textContent
        ) || [];

        pdfCanvas     = document.getElementById('pdf-canvas');
        overlayCanvas = document.getElementById('overlay-canvas');
        pdfCtx        = pdfCanvas.getContext('2d');
        overlayCtx    = overlayCanvas.getContext('2d');
        canvasWrap    = document.getElementById('tk-canvas-wrap');
        canvasInner   = document.getElementById('canvas-inner');

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
        // Mouse wheel zoom — smooth, cursor-centered
        canvasWrap.addEventListener('wheel', _onWheel, { passive: false });

        // Pan: middle button OR space + left button
        canvasWrap.addEventListener('mousedown', _onMouseDown);
        window.addEventListener('mousemove', _onMouseMove);
        window.addEventListener('mouseup', _onMouseUp);

        // Coordinate readout (wrap space, not canvas space)
        canvasWrap.addEventListener('mousemove', _updateCoordsDisplay);

        // Space-bar + general keyboard shortcuts
        window.addEventListener('keydown', _onKeyDown);
        window.addEventListener('keyup', _onKeyUp);

        // Touch: single-finger pan + pinch zoom
        canvasWrap.addEventListener('touchstart', _onTouchStart, { passive: true });
        canvasWrap.addEventListener('touchmove', _onTouchMove, { passive: false });
        canvasWrap.addEventListener('touchend', _onTouchEnd, { passive: true });

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
                if (btn.dataset.tool === 'print') { return; }
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
        if (!state.spaceDown) {
            canvasWrap.style.cursor = tool === 'select' ? 'grab' : 'crosshair';
        }
    }

    // ── CSS Transform ─────────────────────────────────────────────────────────
    function applyTransform() {
        canvasInner.style.transform =
            `translate(${state.cssX}px, ${state.cssY}px) scale(${state.cssScale})`;
    }

    // ── PDF loading ───────────────────────────────────────────────────────────
    async function loadPDF(planId, pageId, pageNum) {
        state.currentPlanId = planId;
        state.currentPageId = pageId;
        state.currentPageNum = pageNum;

        const url = `/project/${state.projectId}/takeoff/plan/${planId}/pdf`;
        try {
            const doc = await pdfjsLib.getDocument(url).promise;
            state.pdfDoc = doc;

            // Pre-calculate zoom-to-fit before first render so initial render is correct
            const firstPage = await doc.getPage(pageNum);
            const naturalVp = firstPage.getViewport({ scale: 1.0 });
            const wrapW = canvasWrap.clientWidth;
            const wrapH = canvasWrap.clientHeight;
            const fitZoom = Math.min(
                (wrapW / naturalVp.width)  * 0.95,
                (wrapH / naturalVp.height) * 0.95
            );
            state.zoom          = Math.max(0.1, Math.min(10, fitZoom));
            state._lastRenderZoom = state.zoom;

            // Center the canvas in the wrap
            const canvasW = state.baseRenderScale * state.zoom * naturalVp.width;
            const canvasH = state.baseRenderScale * state.zoom * naturalVp.height;
            state.cssX     = Math.max(0, (wrapW - canvasW) / 2);
            state.cssY     = Math.max(0, (wrapH - canvasH) / 2);
            state.cssScale = 1.0;

            renderPage(pageNum);

            // Generate thumbnails for all pages in this plan
            const plan = state.plans.find(p => p.id === planId);
            if (plan) generateThumbnails(planId, plan.pages);
        } catch (err) {
            console.error('PDF load error:', err);
        }
    }

    // ── Client-side thumbnail generation ─────────────────────────────────────
    async function generateThumbnails(planId, pages) {
        if (!state.pdfDoc) return;
        for (const pageData of pages) {
            const thumbImg = document.querySelector(
                `[data-page-id="${pageData.id}"] .page-thumb-img`
            );
            if (!thumbImg) continue;
            try {
                const pdfPage = await state.pdfDoc.getPage(pageData.page_number);
                const viewport = pdfPage.getViewport({ scale: 0.15 });
                const canvas = document.createElement('canvas');
                canvas.width  = viewport.width;
                canvas.height = viewport.height;
                await pdfPage.render({ canvasContext: canvas.getContext('2d'), viewport }).promise;
                thumbImg.src = canvas.toDataURL('image/jpeg', 0.7);
            } catch (err) {
                console.error(`Thumbnail error page ${pageData.page_number}:`, err);
            }
        }
    }

    // ── Render page at current zoom ───────────────────────────────────────────
    function renderPage(pageNum) {
        if (!state.pdfDoc) return;

        if (state.renderTask) { state.renderTask.cancel(); state.renderTask = null; }
        clearTimeout(state.renderDebounceTimer);

        state.pdfDoc.getPage(pageNum).then(page => {
            const renderScale = state.baseRenderScale * state.zoom;
            const viewport    = page.getViewport({ scale: renderScale });

            pdfCanvas.width      = viewport.width;
            pdfCanvas.height     = viewport.height;
            overlayCanvas.width  = viewport.width;
            overlayCanvas.height = viewport.height;

            // Canvas is now sized for current zoom — CSS scale resets to 1
            state.cssScale = 1.0;
            applyTransform();

            const task = page.render({ canvasContext: pdfCtx, viewport });
            state.renderTask = task;
            task.promise.then(() => {
                state.renderTask = null;
                state._lastRenderZoom = state.zoom;
                renderOverlays();
                _updateStatusBar();
            }).catch(err => {
                if (err.name !== 'RenderingCancelledException') console.error('Render error:', err);
            });
        });
    }

    // ── Quality re-render (called on zoom end, debounced 300 ms) ─────────────
    function rerenderAtCurrentZoom() {
        if (!state.pdfDoc) return;
        if (state.renderTask) { state.renderTask.cancel(); state.renderTask = null; }

        const targetZoom = state.zoom;
        state.pdfDoc.getPage(state.currentPageNum).then(page => {
            const renderScale = state.baseRenderScale * targetZoom;
            const viewport    = page.getViewport({ scale: renderScale });

            pdfCanvas.width      = viewport.width;
            pdfCanvas.height     = viewport.height;
            overlayCanvas.width  = viewport.width;
            overlayCanvas.height = viewport.height;

            const task = page.render({ canvasContext: pdfCtx, viewport });
            state.renderTask = task;
            task.promise.then(() => {
                state.renderTask       = null;
                state._lastRenderZoom  = targetZoom;
                state.cssScale         = 1.0;
                applyTransform();
                renderOverlays();
                _updateStatusBar();
            }).catch(err => {
                if (err.name !== 'RenderingCancelledException') console.error('Rerender error:', err);
            });
        });
    }

    function _scheduleRerender() {
        clearTimeout(state.renderDebounceTimer);
        state.renderDebounceTimer = setTimeout(rerenderAtCurrentZoom, 300);
    }

    // ── Overlays (placeholder — drawing tools in Session 19) ─────────────────
    function renderOverlays() {
        overlayCtx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);
        // Session 19: draw measurements on current page here
        _updateDataTable();
    }

    // ── Pan / Zoom ────────────────────────────────────────────────────────────

    // Mouse wheel — zoom centered on cursor
    function _onWheel(e) {
        e.preventDefault();
        const factor = e.deltaY > 0 ? 0.9 : 1.1;
        const rect   = canvasWrap.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;

        state.cssX    = mouseX - (mouseX - state.cssX) * factor;
        state.cssY    = mouseY - (mouseY - state.cssY) * factor;
        state.zoom    = Math.max(0.1, Math.min(10, state.zoom * factor));
        state.cssScale = state.zoom / state._lastRenderZoom;
        applyTransform();
        _updateZoomDisplay();
        _scheduleRerender();
    }

    // Public zoom buttons — centered on wrap center
    function zoom(delta) {
        const factor = 1 + delta;
        const cx = canvasWrap.clientWidth  / 2;
        const cy = canvasWrap.clientHeight / 2;
        state.cssX    = cx - (cx - state.cssX) * factor;
        state.cssY    = cy - (cy - state.cssY) * factor;
        state.zoom    = Math.max(0.1, Math.min(10, state.zoom * factor));
        state.cssScale = state.zoom / state._lastRenderZoom;
        applyTransform();
        _updateZoomDisplay();
        _scheduleRerender();
    }

    // Zoom to fit — animate CSS then quality re-render
    function zoomToFit() {
        if (!state.pdfDoc || !pdfCanvas.width) return;

        const naturalW = pdfCanvas.width  / (state.baseRenderScale * state._lastRenderZoom);
        const naturalH = pdfCanvas.height / (state.baseRenderScale * state._lastRenderZoom);
        const wrapW    = canvasWrap.clientWidth;
        const wrapH    = canvasWrap.clientHeight;

        const fitZoom = Math.min((wrapW / naturalW) * 0.95, (wrapH / naturalH) * 0.95);
        state.zoom = Math.max(0.1, Math.min(10, fitZoom));

        // During CSS animation use current canvas + target scale
        const cssTarget = state.zoom / state._lastRenderZoom;
        const visualW   = pdfCanvas.width  * cssTarget;
        const visualH   = pdfCanvas.height * cssTarget;
        state.cssScale  = cssTarget;
        state.cssX      = Math.max(0, (wrapW - visualW) / 2);
        state.cssY      = Math.max(0, (wrapH - visualH) / 2);

        canvasInner.style.transition = 'transform 0.2s ease';
        applyTransform();
        _updateZoomDisplay();

        // After animation: quality re-render resets cssScale=1, position preserved
        setTimeout(() => {
            canvasInner.style.transition = '';
            rerenderAtCurrentZoom();
        }, 200);
    }

    // Pan start
    function _onMouseDown(e) {
        if (e.button === 1 || (e.button === 0 && state.spaceDown)) {
            if (e.button === 1) e.preventDefault();
            state.isPanning = true;
            state.lastX = e.clientX;
            state.lastY = e.clientY;
            canvasWrap.style.cursor = 'grabbing';
        }
    }

    // Pan move
    function _onMouseMove(e) {
        if (!state.isPanning) return;
        state.cssX += e.clientX - state.lastX;
        state.cssY += e.clientY - state.lastY;
        state.lastX = e.clientX;
        state.lastY = e.clientY;
        applyTransform();
    }

    // Pan end
    function _onMouseUp() {
        if (!state.isPanning) return;
        state.isPanning = false;
        canvasWrap.style.cursor = (state.spaceDown || state.activeTool === 'select')
            ? 'grab' : 'crosshair';
    }

    // ── Touch: single-finger pan + pinch zoom ─────────────────────────────────
    function _onTouchStart(e) {
        for (const t of e.changedTouches) {
            state._touches[t.identifier] = { x: t.clientX, y: t.clientY };
        }
    }

    function _onTouchMove(e) {
        e.preventDefault();
        if (e.touches.length === 1) {
            const t    = e.touches[0];
            const prev = state._touches[t.identifier];
            if (prev) {
                state.cssX += t.clientX - prev.x;
                state.cssY += t.clientY - prev.y;
                applyTransform();
            }
            state._touches[t.identifier] = { x: t.clientX, y: t.clientY };
        } else if (e.touches.length === 2) {
            const t1 = e.touches[0];
            const t2 = e.touches[1];
            const p1 = state._touches[t1.identifier];
            const p2 = state._touches[t2.identifier];
            if (p1 && p2) {
                const prevDist = Math.hypot(p1.x - p2.x, p1.y - p2.y);
                const currDist = Math.hypot(t1.clientX - t2.clientX, t1.clientY - t2.clientY);
                if (prevDist > 0) {
                    const factor = currDist / prevDist;
                    const rect   = canvasWrap.getBoundingClientRect();
                    const midX   = (t1.clientX + t2.clientX) / 2 - rect.left;
                    const midY   = (t1.clientY + t2.clientY) / 2 - rect.top;
                    state.cssX    = midX - (midX - state.cssX) * factor;
                    state.cssY    = midY - (midY - state.cssY) * factor;
                    state.zoom    = Math.max(0.1, Math.min(10, state.zoom * factor));
                    state.cssScale = state.zoom / state._lastRenderZoom;
                    applyTransform();
                    _updateZoomDisplay();
                    _scheduleRerender();
                }
            }
            for (const t of e.touches) {
                state._touches[t.identifier] = { x: t.clientX, y: t.clientY };
            }
        }
    }

    function _onTouchEnd(e) {
        for (const t of e.changedTouches) delete state._touches[t.identifier];
    }

    // ── Keyboard shortcuts ────────────────────────────────────────────────────
    function _onKeyDown(e) {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

        if (e.code === 'Space' && !state.spaceDown) {
            e.preventDefault();
            state.spaceDown = true;
            canvasWrap.style.cursor = 'grab';
            return;
        }

        switch (e.key) {
            case 'f': case 'F': zoomToFit(); break;
            case 'ArrowRight':  _nextPage(); break;
            case 'ArrowLeft':   _prevPage(); break;
            case 'Escape':      setActiveTool('select'); break;
            case 'Delete':      break; // Session 19: delete selected measurement
        }
    }

    function _onKeyUp(e) {
        if (e.code === 'Space') {
            state.spaceDown = false;
            if (!state.isPanning) {
                canvasWrap.style.cursor = state.activeTool === 'select' ? 'grab' : 'crosshair';
            }
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
        state.cssX = 0;
        state.cssY = 0;
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

            const header = document.createElement('div');
            header.className = 'plan-header';
            header.textContent = plan.original_filename;
            list.appendChild(header);

            pages.forEach(page => {
                const item = document.createElement('div');
                item.className = 'page-thumb-item';
                item.dataset.pageId     = page.id;
                item.dataset.pageNumber = page.page_number;
                item.innerHTML = `
                    <div class="thumb-wrapper">
                        <img class="page-thumb-img"
                             src="${page.thumbnail_url || ''}"
                             style="width:100%;background:#252B33;min-height:80px;display:block;"
                             alt="Page ${page.page_number}">
                    </div>
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
            const unit   = _unitForType(item.measurement_type);
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

    function filterItems(text) { _renderItemList(text); }

    // ── Floating data table ───────────────────────────────────────────────────
    function _updateDataTable() {
        const tableEl = document.getElementById('tk-data-table');
        const rowsEl  = document.getElementById('tk-dt-rows');
        const pageItems = state.items.filter(i => i.measurement_count > 0);
        if (pageItems.length === 0) { tableEl.style.display = 'none'; return; }

        tableEl.style.display = 'block';
        rowsEl.innerHTML = '';
        pageItems.forEach(item => {
            const unit = _unitForType(item.measurement_type);
            const row  = document.createElement('div');
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
            badgeEl.className   = 'scale-badge scale-set';
        } else {
            scaleEl.textContent = 'Scale: not set';
            badgeEl.textContent = '⚠ Scale Not Set';
            badgeEl.className   = 'scale-badge scale-unset';
        }
        _updateZoomDisplay();
    }

    function _updateZoomDisplay() {
        const pct = Math.round(state.zoom * 100) + '%';
        document.getElementById('tk-zoom-pct').textContent = pct;
        document.getElementById('tk-status-zoom').textContent = pct;
    }

    function _updateCoordsDisplay(e) {
        if (!pdfCanvas.width || !state._lastRenderZoom) return;
        const rect   = canvasWrap.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;
        // wrap space → canvas space → PDF natural space (px at zoom 1.0)
        const canvasX = (mouseX - state.cssX) / state.cssScale;
        const canvasY = (mouseY - state.cssY) / state.cssScale;
        const pdfX = (canvasX / state.baseRenderScale / state._lastRenderZoom).toFixed(1);
        const pdfY = (canvasY / state.baseRenderScale / state._lastRenderZoom).toFixed(1);
        document.getElementById('tk-status-xy').textContent = `X: ${pdfX}  Y: ${pdfY}`;
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
        document.getElementById('upload-status-msg').textContent = 'Uploading...';
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
                        `Uploaded ${data.page_count} page(s). Rendering thumbnails...`;
                    document.getElementById('upload-progress-bar').style.width = '100%';
                    setTimeout(() => { closeUploadModal(); _onUploadComplete(data); }, 400);
                } else {
                    document.getElementById('upload-status-msg').textContent =
                        'Error: ' + (data.error || 'Upload failed');
                }
            } else {
                document.getElementById('upload-status-msg').textContent = 'Upload failed (server error).';
            }
        };
        xhr.onerror = () => {
            document.getElementById('upload-status-msg').textContent = 'Network error.';
        };
        xhr.send(fd);
    }

    function _onUploadComplete(data) {
        const newPlan = {
            id: data.plan_id,
            original_filename: data.original_filename || 'Uploaded Plan',
            page_count: data.page_count,
            pages: data.pages.map(p => ({
                id: p.id,
                page_number: p.page_number,
                page_name: p.page_name,
                thumbnail_url: null,
                scale_set: false,
                scale_method: null,
            })),
        };
        state.plans.push(newPlan);
        document.getElementById('tk-empty-state').style.display = 'none';
        _renderPageList();
        _highlightActivePage();

        if (newPlan.pages.length > 0) {
            const firstPage = newPlan.pages[0];
            loadPDF(newPlan.id, firstPage.id, firstPage.page_number);
        }
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
        createItem({
            name:             document.getElementById('ni-name').value.trim(),
            measurement_type: document.getElementById('ni-type').value,
            color:            document.getElementById('ni-color').value,
            opacity:          parseInt(document.getElementById('ni-opacity').value) / 100,
            assembly_notes:   document.getElementById('ni-notes').value.trim(),
        });
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
                document.getElementById('ni-name').value  = '';
                document.getElementById('ni-notes').value = '';
                fetchItems();
            } else {
                alert('Error: ' + (data.error || 'Could not create takeoff.'));
            }
        })
        .catch(err => console.error('createItem:', err));
    }

    function deleteItem(itemId) {
        fetch(`/project/${state.projectId}/takeoff/item/${itemId}`, { method: 'DELETE' })
            .then(r => r.json())
            .then(data => { if (data.success) fetchItems(); })
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
        const plan = state.plans.find(p => p.id === state.currentPlanId);
        if (plan) {
            const page = plan.pages.find(p => p.id === state.currentPageId);
            if (page) { page.scale_set = true; _updateStatusBar(); }
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
            .replace(/&/g, '&amp;').replace(/</g, '&lt;')
            .replace(/>/g, '&gt;') .replace(/"/g, '&quot;');
    }

    function _unitForType(type) {
        return type === 'area' ? 'SF' : type === 'count' ? 'EA' : 'FT';
    }

    function _iconForType(type) {
        switch (type) {
            case 'area':              return '▭';
            case 'count':            return '•';
            case 'linear_with_width': return '═';
            case 'segment':          return '╌';
            default:                 return '─';
        }
    }

    // ── Public API ────────────────────────────────────────────────────────────
    return {
        init,
        zoom,
        zoomToFit,
        applyTransform,
        rerenderAtCurrentZoom,
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
        generateThumbnails,
        // Expose state for Session 19 drawing tools
        _state: state,
    };

})();

// Boot on DOMContentLoaded
document.addEventListener('DOMContentLoaded', TK.init);
