/**
 * takeoff.js — ZenBid Takeoff Module
 * Session 18 — Foundation: PDF viewer, page nav, item CRUD
 * Session 19 — Konva.js migration: 3-layer stage, native pan/zoom
 * Session 19b — Bug fixes: loadPDF/loadPage separation, sidebar pre-render,
 *               thumbnail regeneration, console diagnostics
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
 *
 * LOAD FLOW (Bug 1 fix)
 * loadPage(pageId, pageNum, planId)  — main entry point for any page navigation
 *   ↳ loadPDF(planId)               — loads PDF.js doc if plan changed / not loaded
 *       ↳ regenerateAllThumbnails() — renders sidebar thumbnails after doc loads
 *   ↳ renderPDFPage(pageNum)         — renders the page to Konva pdfLayer
 *   ↳ zoomToFit()                   — centers and fits the rendered page
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
        stage:        null,
        pdfLayer:     null,
        measureLayer: null,
        uiLayer:      null,
        pdfImage:     null,

        // Current stage zoom (stage.scaleX())
        currentZoom: 1.0,

        // PDF render dimensions (pixels at RENDER_SCALE)
        renderWidth:  0,
        renderHeight: 0,

        // Coordinate converter — exported for Session 2 drawing tools
        screenToPDF: null,

        activeTool:     'select',
        items:          [],
        leftCollapsed:  false,
        rightCollapsed: false,

        // Touch tracking for pinch zoom
        _touches: {},
    };

    // Active Konva tween (destroyed before starting a new one)
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

        console.log('[TK] init — projectId:', state.projectId,
                    'plans:', state.plans.length);

        initStage();
        _bindEvents();
        // Bind click handlers to server-pre-rendered sidebar items
        _bindSidebarClicks();
        fetchItems();

        if (state.plans.length > 0) {
            const firstPlan = state.plans[0];
            if (firstPlan.pages && firstPlan.pages.length > 0) {
                const firstPage = firstPlan.pages[0];
                console.log('[TK] Auto-loading first page:',
                            firstPage.page_name, 'plan:', firstPlan.id);
                loadPage(firstPage.id, firstPage.page_number, firstPlan.id)
                    .catch(err => console.error('[TK] Auto-load failed:', err));
            }
        } else {
            console.log('[TK] No plans — showing empty state');
            document.getElementById('tk-empty-state').style.display = 'flex';
        }
    }

    // ── Stage initialization ──────────────────────────────────────────────────
    function initStage() {
        // Fallback if CSS layout hasn't settled yet (can be 0 at DOMContentLoaded)
        const w = canvasWrap.clientWidth  || window.innerWidth  || 900;
        const h = canvasWrap.clientHeight || window.innerHeight || 600;

        console.log('[TK] initStage — container size:', w, '×', h);

        state.stage = new Konva.Stage({
            container: 'konva-container',
            width:  w,
            height: h,
            draggable: true,
        });

        state.pdfLayer     = new Konva.Layer();
        state.measureLayer = new Konva.Layer();
        state.uiLayer      = new Konva.Layer();

        state.stage.add(state.pdfLayer);
        state.stage.add(state.measureLayer);
        state.stage.add(state.uiLayer);

        // Correct dimensions after first paint (handles flexbox layout settling)
        requestAnimationFrame(() => {
            const rw = canvasWrap.clientWidth;
            const rh = canvasWrap.clientHeight;
            if (rw > 0 && (rw !== w || rh !== h)) {
                console.log('[TK] Correcting stage size after layout:', rw, '×', rh);
                state.stage.width(rw);
                state.stage.height(rh);
            }
        });

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

        // screenToPDF: converts stage pointer coords → PDF-space coords
        function _screenToPDF(screenX, screenY) {
            const pos   = state.stage.position();
            const scale = state.stage.scaleX();
            return {
                x: (screenX - pos.x) / scale,
                y: (screenY - pos.y) / scale,
            };
        }

        state.screenToPDF = _screenToPDF;
    }

    // ── Event binding ─────────────────────────────────────────────────────────
    function _bindEvents() {
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

        // Toolbar tool buttons
        document.querySelectorAll('.tool-btn[data-tool]').forEach(btn => {
            btn.addEventListener('click', () => {
                if (btn.dataset.tool === 'scale') { openScaleModal(); return; }
                if (btn.dataset.tool === 'fit')   { zoomToFit();      return; }
                if (btn.dataset.tool === 'print') { return; }
                setActiveTool(btn.dataset.tool);
            });
        });
    }

    // Bind click handlers to sidebar items — works on both Jinja-rendered and
    // JS-rendered items. Call after any DOM rebuild (_renderPageList / init).
    function _bindSidebarClicks() {
        document.querySelectorAll('#tk-page-list .page-thumb-item').forEach(item => {
            // Use replaceWith clone to strip any prior listeners before rebinding
            const fresh = item.cloneNode(true);
            item.parentNode.replaceChild(fresh, item);
            fresh.addEventListener('click', () => {
                const planId  = parseInt(fresh.dataset.planId);
                const pageId  = parseInt(fresh.dataset.pageId);
                const pageNum = parseInt(fresh.dataset.pageNumber);
                loadPage(pageId, pageNum, planId)
                    .catch(err => console.error('[TK] loadPage error:', err));
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

    // ── PDF document loading (Bug 1 fix) ──────────────────────────────────────
    // Loads the PDF.js document for a plan. Does NOT render any page.
    // Called by loadPage() if the plan changes or doc is null.
    async function loadPDF(planId) {
        console.log('[TK] loadPDF — planId:', planId);
        const url = `/project/${state.projectId}/takeoff/plan/${planId}/pdf`;
        try {
            const doc = await pdfjsLib.getDocument(url).promise;
            state.pdfDoc       = doc;
            state.currentPlanId = planId;
            console.log('[TK] PDF document ready — numPages:', doc.numPages);

            // Kick off thumbnail generation for this plan's pages
            const plan = state.plans.find(p => p.id === planId);
            if (plan && plan.pages.length > 0) {
                regenerateAllThumbnails(planId, plan.pages);
            }
        } catch (err) {
            console.error('[TK] loadPDF failed — url:', url, err);
            throw err;
        }
    }

    // ── Page render — main entry point for ALL page navigation (Bug 1 fix) ────
    // Ensures the right PDF doc is loaded, then renders the requested page.
    async function loadPage(pageId, pageNum, planId) {
        console.log('[TK] loadPage —', { pageId, pageNum, planId });

        // Load PDF.js document if this is a new plan or not yet loaded
        if (!state.pdfDoc || state.currentPlanId !== planId) {
            await loadPDF(planId);
        }

        state.currentPageId  = pageId;
        state.currentPageNum = pageNum;

        // Clear Konva layers for the incoming page
        state.pdfLayer.destroyChildren();
        state.measureLayer.destroyChildren();
        state.uiLayer.destroyChildren();
        state.pdfImage = null;

        await renderPDFPage(pageNum);
        zoomToFit();
        _highlightActivePage();
        _updateStatusBar();
    }

    // ── Render a single PDF page onto pdfLayer ────────────────────────────────
    async function renderPDFPage(pageNum) {
        if (!state.pdfDoc) {
            console.warn('[TK] renderPDFPage called but state.pdfDoc is null');
            return;
        }
        console.log('[TK] renderPDFPage — page', pageNum);

        // Cancel any in-flight render task
        if (state.renderTask) {
            state.renderTask.cancel();
            state.renderTask = null;
        }

        const page     = await state.pdfDoc.getPage(pageNum);
        const viewport = page.getViewport({ scale: RENDER_SCALE });

        console.log('[TK] Rendering page', pageNum,
                    'at scale', RENDER_SCALE,
                    '→ canvas', viewport.width, '×', viewport.height);

        // Render PDF.js into an offscreen canvas (never touches the visible Konva stage)
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
                console.error('[TK] renderPDFPage error:', err);
            }
            return;
        }
        state.renderTask = null;

        // Store pixel dimensions for zoomToFit calculations
        state.renderWidth  = viewport.width;
        state.renderHeight = viewport.height;

        // Create or update the Konva.Image on pdfLayer
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
        console.log('[TK] Page', pageNum, 'rendered onto pdfLayer ✓');
        _updateStatusBar();
    }

    // ── Thumbnail regeneration (Bug 2 fix) ───────────────────────────────────
    // Renders small-scale thumbnails for all pages of a plan, sequentially.
    // Aborts early if the plan changes during generation.
    async function regenerateAllThumbnails(planId, pages) {
        const pdfDoc = state.pdfDoc;  // capture at call time
        if (!pdfDoc || state.currentPlanId !== planId) return;

        console.log('[TK] regenerateAllThumbnails — plan', planId,
                    pages.length, 'pages');

        for (const pageData of pages) {
            // Abort if another plan loaded in the meantime
            if (state.currentPlanId !== planId || state.pdfDoc !== pdfDoc) {
                console.log('[TK] Thumbnail generation aborted — plan changed');
                break;
            }

            // Find the thumbnail <img> — works on both Jinja and JS-rendered items
            const parentEl = document.querySelector(
                `#tk-page-list [data-page-id="${pageData.id}"]`
            );
            const thumbImg = parentEl && parentEl.querySelector('.page-thumb-img');
            if (!thumbImg) {
                console.warn('[TK] No thumb img for page id', pageData.id,
                             '— DOM element missing');
                continue;
            }

            try {
                const pdfPage  = await pdfDoc.getPage(pageData.page_number);
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
                console.error('[TK] Thumbnail error page',
                              pageData.page_number, err);
            }
        }

        console.log('[TK] Thumbnail generation complete — plan', planId);
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

    // ── Touch: pinch zoom (single-finger pan handled by Konva draggable) ──────
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

        // Space — temporary pan mode (re-enable draggable even in drawing tools)
        if (e.code === 'Space' && !_spaceDown) {
            e.preventDefault();
            _spaceDown = true;
            state.stage.draggable(true);
            canvasWrap.style.cursor = 'grab';
            return;
        }

        switch (e.key) {
            case 'f': case 'F':  zoomToFit(); break;
            case '=': case '+':  zoom(0.1);   break;
            case '-':            zoom(-0.1);  break;
            case 'ArrowRight':   _nextPage(); break;
            case 'ArrowLeft':    _prevPage(); break;
            case 'Escape':       setActiveTool('select'); break;
            case 'Delete':       break;  // Session 2: delete selected measurement
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
            loadPage(next.id, next.page_number, plan.id)
                .catch(err => console.error('[TK] _nextPage error:', err));
        }
    }

    function _prevPage() {
        const plan = state.plans.find(p => p.id === state.currentPlanId);
        if (!plan) return;
        const idx = plan.pages.findIndex(p => p.id === state.currentPageId);
        if (idx > 0) {
            const prev = plan.pages[idx - 1];
            loadPage(prev.id, prev.page_number, plan.id)
                .catch(err => console.error('[TK] _prevPage error:', err));
        }
    }

    // ── Page list sidebar ─────────────────────────────────────────────────────
    // Rebuilds the sidebar from state.plans. Called for:
    //   • filtering (filterText != '')
    //   • after upload (_onUploadComplete)
    // On first load, the sidebar is already Jinja-rendered; JS just binds clicks.
    function _renderPageList(filterText = '') {
        const list = document.getElementById('tk-page-list');
        list.innerHTML = '';
        const q = filterText.toLowerCase().trim();

        state.plans.forEach(plan => {
            const pages = plan.pages.filter(p =>
                !q || p.page_name.toLowerCase().includes(q)
            );
            if (pages.length === 0) return;

            const header = document.createElement('div');
            header.className      = 'plan-header';
            header.dataset.planId = plan.id;
            header.textContent    = plan.original_filename;
            list.appendChild(header);

            pages.forEach(page => {
                const item = document.createElement('div');
                item.className          = 'page-thumb-item';
                item.dataset.planId     = plan.id;
                item.dataset.pageId     = page.id;
                item.dataset.pageNumber = page.page_number;
                item.innerHTML = `
                    <div class="thumb-wrapper">
                        <img class="page-thumb-img" src="${page.thumbnail_url || ''}"
                             alt="Page ${page.page_number}"
                             style="width:100%;background:#252B33;min-height:80px;display:block;">
                    </div>
                    <span class="page-thumb-name">${_escHtml(page.page_name)}</span>
                `;
                item.addEventListener('click', () => {
                    loadPage(page.id, page.page_number, plan.id)
                        .catch(err => console.error('[TK] loadPage error:', err));
                });
                list.appendChild(item);
            });
        });

        _highlightActivePage();
    }

    function _highlightActivePage() {
        document.querySelectorAll('.page-thumb-item').forEach(el => {
            // == (not ===) to handle string/int comparison across data attrs
            el.classList.toggle('active', el.dataset.pageId == state.currentPageId);
        });
    }

    // Filter sidebar by page name (show/hide — no rebuild needed)
    function filterPages(text) {
        const q = text.toLowerCase().trim();
        if (!q) {
            document.querySelectorAll(
                '#tk-page-list .page-thumb-item, #tk-page-list .plan-header'
            ).forEach(el => { el.style.display = ''; });
            return;
        }
        const visiblePlans = new Set();
        document.querySelectorAll('#tk-page-list .page-thumb-item').forEach(el => {
            const name = (el.querySelector('.page-thumb-name') || {}).textContent || '';
            const show = name.toLowerCase().includes(q);
            el.style.display = show ? '' : 'none';
            if (show) visiblePlans.add(el.dataset.planId);
        });
        document.querySelectorAll('#tk-page-list .plan-header').forEach(el => {
            el.style.display = visiblePlans.has(el.dataset.planId) ? '' : 'none';
        });
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
            .catch(err => console.error('[TK] fetchItems:', err));
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

        const csrfToken = document.querySelector('meta[name="csrf-token"]')
            .getAttribute('content');
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
                        `Uploaded ${data.page_count} page(s). Rendering thumbnails…`;
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

    // Bug 3 fix: rebuild sidebar (so new plan appears), then load its first page.
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

        // Rebuild sidebar from state.plans (includes new plan) + re-bind clicks
        _renderPageList();

        if (newPlan.pages.length > 0) {
            const firstPage = newPlan.pages[0];
            loadPage(firstPage.id, firstPage.page_number, newPlan.id)
                .catch(err => console.error('[TK] Post-upload loadPage error:', err));
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
        .catch(err => console.error('[TK] createItem:', err));
    }

    function deleteItem(itemId) {
        fetch(`/project/${state.projectId}/takeoff/item/${itemId}`, { method: 'DELETE' })
            .then(r => r.json())
            .then(data => { if (data.success) fetchItems(); })
            .catch(err => console.error('[TK] deleteItem:', err));
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
        setTimeout(() => {
            state.stage.width(canvasWrap.clientWidth);
            state.stage.height(canvasWrap.clientHeight);
        }, 210);
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
        loadPDF,
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
        regenerateAllThumbnails,
        // Expose state for Session 2 drawing tools
        _state: state,
    };

})();

// Boot on DOMContentLoaded
document.addEventListener('DOMContentLoaded', TK.init);
