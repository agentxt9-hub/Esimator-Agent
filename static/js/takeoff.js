/**
 * takeoff.js — ZenBid Takeoff Module
 * Session 18 — Foundation: PDF viewer, page nav, item CRUD
 * Session 19 — Konva.js migration: GPU-accelerated stage, 3-layer architecture.
 *   PDF.js renders page → offscreen canvas → Konva.Image on pdfLayer.
 *   Pan/zoom is native Konva stage drag + scale (buttery smooth).
 *   Hit detection, selection, and measurement tools ready for Session 2.
 *
 * LAYER ARCHITECTURE
 * pdfLayer     — Konva.Image of current PDF page (PDF.js rendered at 2× scale)
 * measureLayer — Konva.Shape objects for each measurement (Session 2)
 * uiLayer      — Selection handles, vertex indicators, labels
 *
 * COORDINATE SYSTEM
 * All measurement points stored as PDF-space coordinates.
 * (0,0) = top-left of PDF page at RENDER_SCALE (2.0).
 * Use state.screenToPDF(x, y) to convert stage/screen coords.
 * Use state.stage.scale() and .position() for the inverse transform.
 */
'use strict';

const TK = (() => {

    // ── State ─────────────────────────────────────────────────────────────────
    const state = {
        projectId:      null,
        plans:          [],
        currentPlanId:  null,
        currentPageId:  null,
        currentPageNum: 1,
        pdfDoc:         null,
        renderTask:     null,   // in-flight PDF.js render task (cancel on page change)

        // Konva objects
        stage:        null,     // Konva.Stage
        pdfLayer:     null,     // Konva.Layer — PDF image
        measureLayer: null,     // Konva.Layer — measurements (Session 2)
        uiLayer:      null,     // Konva.Layer — handles/labels
        pdfImage:     null,     // Konva.Image holding rendered PDF page

        // Current stage zoom (stage.scaleX())
        currentZoom: 1.0,

        // PDF render dimensions (pixels at RENDER_SCALE)
        renderWidth:  0,
        renderHeight: 0,

        // coordinate converter — set in initStage(), exported for Session 2
        screenToPDF: null,

        activeTool:     'select',
        items:          [],
        leftCollapsed:  false,
        rightCollapsed: false,

        // Touch tracking for pinch zoom
        _touches: {},
    };

    // Active Konva tween (cancelled before starting a new one)
    let _zoomTween = null;

    // Space-bar temporary pan mode
    let _spaceDown = false;

    // DOM ref
    let canvasWrap;

    // PDF render scale — 2× for retina-quality output
    const RENDER_SCALE = 2.0;

    // ── Init ──────────────────────────────────────────────────────────────────
    function init() {
        state.projectId = JSON.parse(
            document.getElementById('tk-project-id').textContent
        );
        state.plans = JSON.parse(
            document.getElementById('tk-plans-data').textContent
        ) || [];

        canvasWrap = document.getElementById('tk-canvas-wrap');

        initStage();
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

    // ── Stage initialization ──────────────────────────────────────────────────
    function initStage() {
        state.stage = new Konva.Stage({
            container: 'konva-container',
            width:     canvasWrap.clientWidth,
            height:    canvasWrap.clientHeight,
            draggable: true,    // native pan when activeTool === 'select'
        });

        state.pdfLayer     = new Konva.Layer();
        state.measureLayer = new Konva.Layer();
        state.uiLayer      = new Konva.Layer();

        state.stage.add(state.pdfLayer);
        state.stage.add(state.measureLayer);
        state.stage.add(state.uiLayer);

        // Zoom on mouse wheel — cursor-centered, continuous factor for trackpads
        state.stage.on('wheel', (e) => {
            e.evt.preventDefault();
            if (_zoomTween) { _zoomTween.destroy(); _zoomTween = null; }

            const scaleBy  = Math.pow(0.999, e.evt.deltaY);
            const oldScale = state.stage.scaleX();
            const pointer  = state.stage.getPointerPosition();
            const origin   = {
                x: (pointer.x - state.stage.x()) / oldScale,
                y: (pointer.y - state.stage.y()) / oldScale,
            };
            const newScale = Math.max(0.05, Math.min(20, oldScale * scaleBy));

            state.stage.scale({ x: newScale, y: newScale });
            state.stage.position({
                x: pointer.x - origin.x * newScale,
                y: pointer.y - origin.y * newScale,
            });
            state.currentZoom = newScale;
            _updateZoomDisplay();
        });

        // Stage resize on window resize
        window.addEventListener('resize', () => {
            state.stage.width(canvasWrap.clientWidth);
            state.stage.height(canvasWrap.clientHeight);
        });

        // Cursor management
        state.stage.on('mouseenter', () => {
            if (state.activeTool === 'select' || _spaceDown) {
                canvasWrap.style.cursor = 'grab';
            }
        });
        state.stage.on('dragstart', () => {
            if (state.activeTool === 'select' || _spaceDown) {
                canvasWrap.style.cursor = 'grabbing';
            }
        });
        state.stage.on('dragend', () => {
            canvasWrap.style.cursor =
                (state.activeTool === 'select' || _spaceDown) ? 'grab' : 'crosshair';
        });

        // Coordinate readout in status bar
        state.stage.on('mousemove', () => {
            const pos = state.stage.getPointerPosition();
            if (!pos) return;
            const pdf = _screenToPDF(pos.x, pos.y);
            document.getElementById('tk-status-xy').textContent =
                `X: ${pdf.x.toFixed(1)}  Y: ${pdf.y.toFixed(1)}`;
        });

        // screenToPDF: stage/screen coords → PDF-space coords (Session 2 needs this)
        function _screenToPDF(screenX, screenY) {
            const pos   = state.stage.position();
            const scale = state.stage.scaleX();
            return {
                x: (screenX - pos.x) / scale,
                y: (screenY - pos.y) / scale,
            };
        }

        // Export on state so Session 2 drawing tools can import it
        state.screenToPDF = _screenToPDF;
    }

    // ── Event binding ─────────────────────────────────────────────────────────
    function _bindEvents() {
        // Keyboard shortcuts
        window.addEventListener('keydown', _onKeyDown);
        window.addEventListener('keyup',   _onKeyUp);

        // Touch pinch zoom (single-finger pan handled by Konva draggable)
        canvasWrap.addEventListener('touchstart', _onTouchStart, { passive: true });
        canvasWrap.addEventListener('touchmove',  _onTouchMove,  { passive: false });
        canvasWrap.addEventListener('touchend',   _onTouchEnd,   { passive: true });

        // Color swatches in new-item modal
        document.querySelectorAll('.color-swatch').forEach(el => {
            el.addEventListener('click', () => {
                document.querySelectorAll('.color-swatch')
                    .forEach(s => s.classList.remove('selected'));
                el.classList.add('selected');
                document.getElementById('ni-color').value = el.dataset.color;
            });
        });

        // Tool buttons
        document.querySelectorAll('.tool-btn[data-tool]').forEach(btn => {
            btn.addEventListener('click', () => {
                if (btn.dataset.tool === 'scale') { openScaleModal(); return; }
                if (btn.dataset.tool === 'fit')   { zoomToFit();      return; }
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
        if (tool === 'select') {
            state.stage.draggable(true);
            canvasWrap.style.cursor = 'grab';
        } else {
            state.stage.draggable(false);
            canvasWrap.style.cursor = 'crosshair';
        }
    }

    // ── PDF loading ───────────────────────────────────────────────────────────
    async function loadPDF(planId, pageId, pageNum) {
        state.currentPlanId  = planId;
        state.currentPageId  = pageId;
        state.currentPageNum = pageNum;

        const url = `/project/${state.projectId}/takeoff/plan/${planId}/pdf`;
        try {
            const doc = await pdfjsLib.getDocument(url).promise;
            state.pdfDoc = doc;
            await renderPDFPage(pageNum);
            zoomToFit();
            _highlightActivePage();

            // Client-side thumbnails for all pages in this plan
            const plan = state.plans.find(p => p.id === planId);
            if (plan) generateThumbnails(planId, plan.pages);
        } catch (err) {
            console.error('PDF load error:', err);
        }
    }

    // ── Render PDF page → offscreen canvas → Konva.Image on pdfLayer ─────────
    async function renderPDFPage(pageNum) {
        if (!state.pdfDoc) return;

        // Cancel any in-flight render
        if (state.renderTask) {
            state.renderTask.cancel();
            state.renderTask = null;
        }

        const page     = await state.pdfDoc.getPage(pageNum);
        const viewport = page.getViewport({ scale: RENDER_SCALE });

        // Render PDF.js into offscreen canvas (never touches the visible stage)
        const offscreen    = document.createElement('canvas');
        offscreen.width    = viewport.width;
        offscreen.height   = viewport.height;
        const ctx          = offscreen.getContext('2d');

        const task = page.render({ canvasContext: ctx, viewport });
        state.renderTask = task;

        try {
            await task.promise;
        } catch (err) {
            if (err.name !== 'RenderingCancelledException') {
                console.error('Render error:', err);
            }
            return;
        }
        state.renderTask = null;

        // Store pixel dimensions for zoomToFit calculations
        state.renderWidth  = viewport.width;
        state.renderHeight = viewport.height;

        // Create or update Konva.Image (update avoids layer rebuild on page nav)
        if (state.pdfImage) {
            state.pdfImage.image(offscreen);
            state.pdfImage.width(viewport.width);
            state.pdfImage.height(viewport.height);
        } else {
            state.pdfImage = new Konva.Image({
                x:      0,
                y:      0,
                image:  offscreen,
                width:  viewport.width,
                height: viewport.height,
            });
            state.pdfLayer.add(state.pdfImage);
        }

        state.pdfLayer.batchDraw();
        _updateStatusBar();
    }

    // ── Client-side thumbnail generation (unchanged from Session 18) ──────────
    async function generateThumbnails(planId, pages) {
        if (!state.pdfDoc) return;
        for (const pageData of pages) {
            const thumbImg = document.querySelector(
                `[data-page-id="${pageData.id}"] .page-thumb-img`
            );
            if (!thumbImg) continue;
            try {
                const pdfPage  = await state.pdfDoc.getPage(pageData.page_number);
                const viewport = pdfPage.getViewport({ scale: 0.15 });
                const canvas   = document.createElement('canvas');
                canvas.width   = viewport.width;
                canvas.height  = viewport.height;
                await pdfPage.render({
                    canvasContext: canvas.getContext('2d'),
                    viewport,
                }).promise;
                thumbImg.src = canvas.toDataURL('image/jpeg', 0.7);
            } catch (err) {
                console.error(`Thumbnail error page ${pageData.page_number}:`, err);
            }
        }
    }

    // ── Zoom to fit — animated via Konva.Tween ────────────────────────────────
    function zoomToFit() {
        if (!state.pdfImage || !state.renderWidth) return;
        if (_zoomTween) { _zoomTween.destroy(); _zoomTween = null; }

        const padding = 40;
        const scaleX  = (canvasWrap.clientWidth  - padding) / state.renderWidth;
        const scaleY  = (canvasWrap.clientHeight - padding) / state.renderHeight;
        const scale   = Math.min(scaleX, scaleY);

        _zoomTween = new Konva.Tween({
            node:     state.stage,
            duration: 0.2,
            scaleX:   scale,
            scaleY:   scale,
            x: (canvasWrap.clientWidth  - state.renderWidth  * scale) / 2,
            y: (canvasWrap.clientHeight - state.renderHeight * scale) / 2,
            easing:   Konva.Easings.EaseInOut,
            onFinish: () => {
                state.currentZoom = scale;
                _updateZoomDisplay();
                _zoomTween = null;
            },
        });
        _zoomTween.play();
    }

    // ── Zoom buttons (+/-) — animated via Konva.Tween ────────────────────────
    function zoom(delta) {
        if (_zoomTween) { _zoomTween.destroy(); _zoomTween = null; }

        const factor   = 1 + delta;
        const oldScale = state.stage.scaleX();
        const newScale = Math.max(0.05, Math.min(20, oldScale * factor));
        const stagePos = state.stage.position();
        const cx       = canvasWrap.clientWidth  / 2;
        const cy       = canvasWrap.clientHeight / 2;

        _zoomTween = new Konva.Tween({
            node:     state.stage,
            duration: 0.15,
            scaleX:   newScale,
            scaleY:   newScale,
            x: cx - (cx - stagePos.x) * (newScale / oldScale),
            y: cy - (cy - stagePos.y) * (newScale / oldScale),
            easing:   Konva.Easings.EaseInOut,
            onFinish: () => {
                state.currentZoom = newScale;
                _updateZoomDisplay();
                _zoomTween = null;
            },
        });
        _zoomTween.play();
    }

    // ── Touch: pinch zoom (single-finger pan is Konva draggable) ─────────────
    function _onTouchStart(e) {
        for (const t of e.changedTouches) {
            state._touches[t.identifier] = { x: t.clientX, y: t.clientY };
        }
    }

    function _onTouchMove(e) {
        if (e.touches.length !== 2) return;
        e.preventDefault();

        const t1 = e.touches[0];
        const t2 = e.touches[1];
        const p1 = state._touches[t1.identifier];
        const p2 = state._touches[t2.identifier];

        if (p1 && p2) {
            const prevDist = Math.hypot(p1.x - p2.x, p1.y - p2.y);
            const currDist = Math.hypot(t1.clientX - t2.clientX, t1.clientY - t2.clientY);

            if (prevDist > 0) {
                if (_zoomTween) { _zoomTween.destroy(); _zoomTween = null; }

                const factor   = currDist / prevDist;
                const oldScale = state.stage.scaleX();
                const newScale = Math.max(0.05, Math.min(20, oldScale * factor));
                const rect     = canvasWrap.getBoundingClientRect();
                const midX     = (t1.clientX + t2.clientX) / 2 - rect.left;
                const midY     = (t1.clientY + t2.clientY) / 2 - rect.top;
                const stagePos = state.stage.position();

                state.stage.scale({ x: newScale, y: newScale });
                state.stage.position({
                    x: midX - (midX - stagePos.x) * (newScale / oldScale),
                    y: midY - (midY - stagePos.y) * (newScale / oldScale),
                });
                state.currentZoom = newScale;
                _updateZoomDisplay();
            }
        }

        for (const t of e.touches) {
            state._touches[t.identifier] = { x: t.clientX, y: t.clientY };
        }
    }

    function _onTouchEnd(e) {
        for (const t of e.changedTouches) delete state._touches[t.identifier];
    }

    // ── Keyboard shortcuts ────────────────────────────────────────────────────
    function _onKeyDown(e) {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

        // Space — temporary pan mode
        if (e.code === 'Space' && !_spaceDown) {
            e.preventDefault();
            _spaceDown = true;
            state.stage.draggable(true);
            canvasWrap.style.cursor = 'grab';
            return;
        }

        switch (e.key) {
            case 'f': case 'F':    zoomToFit(); break;
            case '=': case '+':    zoom(0.1);   break;
            case '-':              zoom(-0.1);  break;
            case 'ArrowRight':     _nextPage(); break;
            case 'ArrowLeft':      _prevPage(); break;
            case 'Escape':         setActiveTool('select'); break;
            case 'Delete':         break;  // Session 2: delete selected measurement
        }
    }

    function _onKeyUp(e) {
        if (e.code === 'Space') {
            _spaceDown = false;
            if (state.activeTool !== 'select') {
                state.stage.draggable(false);
                canvasWrap.style.cursor = 'crosshair';
            } else {
                canvasWrap.style.cursor = 'grab';
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

        // Clear layers for new page (Session 2 reloads measurements here too)
        state.pdfLayer.destroyChildren();
        state.measureLayer.destroyChildren();
        state.uiLayer.destroyChildren();
        state.pdfImage = null;

        renderPDFPage(pageNum).then(() => zoomToFit());
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
            list.innerHTML =
                '<div class="tk-empty-msg">No takeoffs yet.<br>Click + New to add one.</div>';
            return;
        }

        filtered.forEach(item => {
            const row    = document.createElement('div');
            row.className   = 'takeoff-item-row';
            row.dataset.itemId = item.id;
            const unit   = _unitForType(item.measurement_type);
            const valStr = item.total > 0
                ? `${item.total.toLocaleString(undefined, { maximumFractionDigits: 2 })} ${unit}`
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
        const tableEl   = document.getElementById('tk-data-table');
        const rowsEl    = document.getElementById('tk-dt-rows');
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
                <span class="tk-dt-val">
                    ${item.total.toLocaleString(undefined, { maximumFractionDigits: 2 })} ${unit}
                </span>
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
        const pct = Math.round(state.currentZoom * 100) + '%';
        document.getElementById('tk-zoom-pct').textContent    = pct;
        document.getElementById('tk-status-zoom').textContent = pct;
    }

    // ── Overlays — placeholder for Session 2 drawing tools ───────────────────
    function renderOverlays() {
        // Session 2: add Konva.Line/Polygon/Circle shapes to measureLayer here.
        _updateDataTable();
    }

    // ── Upload modal ──────────────────────────────────────────────────────────
    function openUploadModal() {
        document.getElementById('upload-modal').style.display    = 'flex';
        document.getElementById('upload-progress').style.display = 'none';
        document.getElementById('drop-zone').style.display       = 'block';
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
        document.getElementById('drop-zone').style.display          = 'none';
        document.getElementById('upload-progress').style.display    = 'block';
        document.getElementById('upload-filename').textContent      = file.name;
        document.getElementById('upload-status-msg').textContent    = 'Uploading...';
        document.getElementById('upload-progress-bar').style.width  = '0%';

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
        const newPlan = {
            id:                data.plan_id,
            original_filename: data.original_filename || 'Uploaded Plan',
            page_count:        data.page_count,
            pages: data.pages.map(p => ({
                id:            p.id,
                page_number:   p.page_number,
                page_name:     p.page_name,
                thumbnail_url: null,
                scale_set:     false,
                scale_method:  null,
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
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify(payload),
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
        // Session 2: persist to TakeoffPage via PATCH route
        const plan = state.plans.find(p => p.id === state.currentPlanId);
        if (plan) {
            const page = plan.pages.find(p => p.id === state.currentPageId);
            if (page) { page.scale_set = true; _updateStatusBar(); }
        }
        closeScaleModal();
        alert(`Scale set: ${ppf} px/ft. (Persist in Session 2.)`);
    }

    // ── Panel collapse ────────────────────────────────────────────────────────
    function toggleLeft() {
        state.leftCollapsed = !state.leftCollapsed;
        document.getElementById('tk-left').classList.toggle('collapsed', state.leftCollapsed);
        document.getElementById('tk-left-collapse').textContent =
            state.leftCollapsed ? '▶' : '◀';
        // Let stage know its container changed width
        setTimeout(() => {
            state.stage.width(canvasWrap.clientWidth);
            state.stage.height(canvasWrap.clientHeight);
        }, 210);    // after 200ms CSS transition
    }

    function toggleRight() {
        state.rightCollapsed = !state.rightCollapsed;
        document.getElementById('tk-right').classList.toggle('collapsed', state.rightCollapsed);
        setTimeout(() => {
            state.stage.width(canvasWrap.clientWidth);
            state.stage.height(canvasWrap.clientHeight);
        }, 210);
    }

    // ── Utilities ─────────────────────────────────────────────────────────────
    function _escHtml(str) {
        return String(str)
            .replace(/&/g,  '&amp;')
            .replace(/</g,  '&lt;')
            .replace(/>/g,  '&gt;')
            .replace(/"/g,  '&quot;');
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
        // Expose state for Session 2 drawing tools
        _state: state,
    };

})();

// Boot on DOMContentLoaded
document.addEventListener('DOMContentLoaded', TK.init);
