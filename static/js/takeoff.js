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

        // Session 2 — measurement tool state
        scalePixelsPerFoot: null,
        currentDrawing:     [],   // [{x,y}] PDF-space points being placed
        activeItemId:       null, // item selected for new measurements
        selectedMeasId:     null, // measurement selected on canvas
        measurements:       [],   // loaded for current page

        // Touch tracking for pinch zoom
        _touches: {},
    };

    // Active Konva tween (destroyed before starting a new one)
    let _zoomTween = null;

    // Space-bar temporary pan mode
    let _spaceDown = false;

    // Scale tool 2-click state
    let _scaleClickState = 0;   // 0=idle, 1=point A placed
    let _scalePointA     = null; // PDF-space {x,y}
    let _scalePxDist     = 0;   // pixel distance computed from two clicks
    let _pendingScalePPF = null; // computed ppf waiting for modal confirm

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
        _initDataTableDrag();

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
        if (typeof Konva === 'undefined') {
            console.error('[TK] Konva not loaded — cannot initialize stage');
            return;
        }

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

        // Coordinate readout + live drawing preview
        state.stage.on('mousemove', () => {
            const pos = state.stage.getPointerPosition();
            if (!pos) return;
            const pdf = _screenToPDF(pos.x, pos.y);
            document.getElementById('tk-status-xy').textContent =
                `X: ${pdf.x.toFixed(1)}  Y: ${pdf.y.toFixed(1)}`;
            // Live preview for in-progress drawings
            if (['linear', 'area'].includes(state.activeTool)
                    && state.currentDrawing.length > 0) {
                _updateDrawPreview(pdf);
            }
        });

        // Stage click — dispatch to active drawing tool
        state.stage.on('click', (e) => {
            if (_spaceDown) return;
            const pos = state.stage.getPointerPosition();
            if (!pos) return;
            const pdf = _screenToPDF(pos.x, pos.y);
            switch (state.activeTool) {
                case 'scale':  _scaleToolClick(pdf);   break;
                case 'linear':
                case 'area':   _drawToolClick(pdf, e); break;
                case 'count':  _countToolClick(pdf);   break;
            }
        });

        // Double-click — complete current drawing
        state.stage.on('dblclick', () => {
            if (['linear', 'area'].includes(state.activeTool)) {
                _completeDraw();
            }
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
        document.querySelectorAll('#ni-color-swatches .color-swatch').forEach(el => {
            el.addEventListener('click', () => {
                document.querySelectorAll('#ni-color-swatches .color-swatch')
                    .forEach(s => s.classList.remove('selected'));
                el.classList.add('selected');
                document.getElementById('ni-color').value = el.dataset.color;
            });
        });

        // Color swatches in properties panel
        document.querySelectorAll('#pp-color-swatches .color-swatch').forEach(el => {
            el.addEventListener('click', () => {
                document.querySelectorAll('#pp-color-swatches .color-swatch')
                    .forEach(s => s.classList.remove('selected'));
                el.classList.add('selected');
                document.getElementById('pp-color').value = el.dataset.color;
            });
        });

        // Toolbar tool buttons
        document.querySelectorAll('.tool-btn[data-tool]').forEach(btn => {
            btn.addEventListener('click', () => {
                if (btn.dataset.tool === 'fit')    { zoomToFit();                  return; }
                if (btn.dataset.tool === 'print')  { return; }
                if (btn.dataset.tool === 'props')  { openPropsPanel(state.activeItemId); return; }
                if (btn.dataset.tool === 'delete') { deleteSelectedMeasurement(); return; }
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
        // Pre-condition checks for drawing tools
        if (['linear', 'area', 'count'].includes(tool)) {
            if (!state.scalePixelsPerFoot && !_pageHasScale()) {
                _showToast('Set page scale before measuring', 'warn');
                _flashBtn('tool-scale');
                return;
            }
            if (!state.activeItemId) {
                _showToast('Select a takeoff item in the right panel first', 'warn');
                return;
            }
        }

        // Cancel any in-progress drawing when switching tools
        if (state.activeTool !== tool) _cancelDraw();

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
        _updateToolbarHint();
    }

    function _pageHasScale() {
        const plan = state.plans.find(p => p.id === state.currentPlanId);
        if (!plan) return false;
        const page = plan.pages.find(p => p.id === state.currentPageId);
        return page && page.scale_set;
    }

    function _flashBtn(btnId) {
        const btn = document.getElementById(btnId);
        if (!btn) return;
        btn.style.background = '#FF6B35';
        setTimeout(() => { btn.style.background = ''; }, 600);
    }

    function _updateToolbarHint() {
        const hintEl = document.getElementById('tk-tool-hint');
        if (!hintEl) return;
        switch (state.activeTool) {
            case 'linear':
            case 'area':
                hintEl.textContent = 'Click to add points  •  Double-click or C to complete  •  Backspace to undo last';
                hintEl.style.display = 'block';
                break;
            case 'scale':
                hintEl.textContent = 'Click first point, then second point on a known dimension';
                hintEl.style.display = 'block';
                break;
            case 'count':
                hintEl.textContent = 'Click to place markers  •  Escape to finish';
                hintEl.style.display = 'block';
                break;
            default:
                hintEl.textContent = '';
                hintEl.style.display = 'none';
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
        if (!state.stage || !state.pdfLayer) {
            console.error('[TK] Stage not initialized — cannot load page');
            return;
        }
        console.log('[TK] loadPage —', { pageId, pageNum, planId });

        // Load PDF.js document if this is a new plan or not yet loaded
        if (!state.pdfDoc || state.currentPlanId !== planId) {
            await loadPDF(planId);
        }

        state.currentPageId  = pageId;
        state.currentPageNum = pageNum;

        // Cancel any in-progress drawing when switching pages
        _cancelDraw();
        state.selectedMeasId = null;
        state.measurements   = [];

        // Clear Konva layers for the incoming page
        state.pdfLayer.destroyChildren();
        state.measureLayer.destroyChildren();
        state.uiLayer.destroyChildren();
        state.pdfImage = null;

        await renderPDFPage(pageNum);
        zoomToFit();
        _highlightActivePage();
        _updateStatusBar();
        loadPageMeasurements(pageId);
    }

    // ── Render a single PDF page onto pdfLayer ────────────────────────────────
    async function renderPDFPage(pageNum) {
        if (!state.pdfLayer) {
            console.error('[TK] pdfLayer is null');
            return;
        }
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

        // Ctrl+Z — undo last measurement
        if ((e.ctrlKey || e.metaKey) && (e.key === 'z' || e.key === 'Z')) {
            e.preventDefault();
            undoLastMeasurement();
            return;
        }

        switch (e.key) {
            case 'f': case 'F':  zoomToFit();            break;
            case '=': case '+':  zoom(0.1);               break;
            case '-':            zoom(-0.1);              break;
            case 'ArrowRight':   _nextPage();             break;
            case 'ArrowLeft':    _prevPage();             break;
            case 'l': case 'L':  setActiveTool('linear'); break;
            case 'a': case 'A':  setActiveTool('area');   break;
            case 'k': case 'K':  setActiveTool('count');  break;
            case 's': case 'S':  setActiveTool('scale');  break;
            case 'c': case 'C':  _completeDraw();         break;
            case 'Delete':       deleteSelectedMeasurement(); break;
            case 'Backspace':    _removeLastPoint();      break;
            case 'Escape':
                if (state.currentDrawing.length > 0) {
                    _cancelDraw();
                } else {
                    deselectMeasurement();
                    closePropsPanel();
                    setActiveTool('select');
                }
                break;
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
            if (item.id === state.activeItemId) row.classList.add('active');
            row.dataset.itemId = item.id;
            const unit   = _unitForType(item.measurement_type);
            const valStr = item.total > 0
                ? `${item.total.toLocaleString(undefined, { maximumFractionDigits: 2 })} ${unit}`
                : '—';
            row.innerHTML = `
                <span class="ti-icon">${_iconForType(item.measurement_type)}</span>
                <span class="ti-color-dot" style="background:${item.color}"></span>
                <span class="ti-name">${_escHtml(item.name)}</span>
                <span class="ti-value">${valStr}</span>
                <span class="ti-actions">
                    <button class="ti-del-btn" title="Delete" data-id="${item.id}">&times;</button>
                </span>
            `;
            // Click row → set as active item + open props panel
            row.addEventListener('click', () => setActiveItem(item.id));
            row.querySelector('.ti-del-btn').addEventListener('click', e => {
                e.stopPropagation();
                if (confirm(`Delete "${item.name}"? This also deletes all measurements.`)) {
                    deleteItem(item.id);
                }
            });
            list.appendChild(row);
        });

        // Aggregate totals footer
        const totalLF  = state.items.filter(i => i.measurement_type !== 'area' && i.measurement_type !== 'count')
                                    .reduce((s, i) => s + (i.total || 0), 0);
        const totalSF  = state.items.filter(i => i.measurement_type === 'area')
                                    .reduce((s, i) => s + (i.total || 0), 0);
        const totalEA  = state.items.filter(i => i.measurement_type === 'count')
                                    .reduce((s, i) => s + (i.total || 0), 0);
        const footer   = document.createElement('div');
        footer.className = 'tk-item-totals';
        footer.innerHTML = `
            <span>LF: ${totalLF.toFixed(1)}</span>
            <span>SF: ${totalSF.toFixed(1)}</span>
            <span>EA: ${totalEA}</span>
        `;
        list.appendChild(footer);
    }

    function filterItems(text) { _renderItemList(text); }

    // ── Floating data table ───────────────────────────────────────────────────
    // Shows page-specific measurement totals derived from state.measurements
    function _updateDataTable() {
        const tableEl = document.getElementById('tk-data-table');
        const rowsEl  = document.getElementById('tk-dt-rows');

        // Build per-item totals from page measurements
        const byItem = {};
        state.measurements.forEach(m => {
            if (!byItem[m.item_id]) {
                byItem[m.item_id] = {
                    name:    m.item_name,
                    color:   m.item_color,
                    type:    m.measurement_type,
                    total:   0,
                };
            }
            byItem[m.item_id].total += (m.calculated_value || 0);
        });

        const entries = Object.values(byItem);
        if (entries.length === 0) { tableEl.style.display = 'none'; return; }

        tableEl.style.display = 'block';
        rowsEl.innerHTML = '';
        entries.forEach(entry => {
            const unit = _unitForType(entry.type);
            const row  = document.createElement('div');
            row.className = 'tk-dt-row';
            row.innerHTML = `
                <span class="tk-dt-dot" style="background:${entry.color}"></span>
                <span class="tk-dt-name">${_escHtml(entry.name)}</span>
                <span class="tk-dt-val">
                    ${entry.total.toLocaleString(undefined, { maximumFractionDigits: 2 })} ${unit}
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

    // ── Overlays — delegates to renderMeasurements ───────────────────────────
    function renderOverlays() {
        renderMeasurements(state.measurements);
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
        const dimMode = document.getElementById('scale-dim-mode');
        const pxMode  = document.getElementById('scale-px-mode');
        if (dimMode) dimMode.style.display = 'none';
        if (pxMode)  pxMode.style.display  = 'block';
        document.getElementById('scale-modal').style.display = 'flex';
    }

    function closeScaleModal(e) {
        if (!e || e.target === document.getElementById('scale-modal')) {
            document.getElementById('scale-modal').style.display = 'none';
            // If cancelling a 2-click scale, clear the UI dots
            if (_scaleClickState > 0) {
                state.uiLayer.find('[id^="scale-"]').forEach(n => n.destroy());
                state.uiLayer.batchDraw();
                _scaleClickState = 0;
                _scalePointA     = null;
                _pendingScalePPF = null;
            }
        }
    }

    function applyScalePreset(val) {
        if (val) document.getElementById('scale-ppf').value = val;
    }

    function saveScale() {
        if (!state.currentPageId) { alert('No page selected.'); return; }

        let ppf;
        if (_pendingScalePPF) {
            // 2-click mode: use pre-computed value
            ppf = _pendingScalePPF;
        } else {
            ppf = parseFloat(document.getElementById('scale-ppf').value);
        }
        if (!ppf || ppf <= 0) { alert('Enter a valid pixels-per-foot value.'); return; }

        fetch(`/project/${state.projectId}/takeoff/page/${state.currentPageId}/scale`, {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({ pixels_per_foot: ppf, method: 'manual' }),
        })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                state.scalePixelsPerFoot = ppf;
                // Update in-memory plan page so scale badge refreshes
                const plan = state.plans.find(p => p.id === state.currentPlanId);
                if (plan) {
                    const page = plan.pages.find(p => p.id === state.currentPageId);
                    if (page) { page.scale_set = true; page.scale_method = 'manual'; }
                }
                _updateStatusBarScale(ppf);
                // Clear scale tool visuals
                state.uiLayer.destroyChildren();
                state.uiLayer.batchDraw();
                _scaleClickState = 0;
                _scalePointA     = null;
                _pendingScalePPF = null;
                closeScaleModal();
                setActiveTool('select');
                _showToast('Scale set successfully', 'ok');
            } else {
                alert('Error saving scale: ' + (data.error || 'Unknown error'));
            }
        })
        .catch(err => {
            console.error('[TK] saveScale error:', err);
            alert('Network error saving scale.');
        });
    }

    function _updateStatusBarScale(ppf) {
        const scaleEl = document.getElementById('tk-status-scale');
        const badgeEl = document.getElementById('tk-scale-display');
        const label   = `${ppf.toFixed(1)} px/ft`;
        if (scaleEl) scaleEl.textContent = `Scale: ${label}`;
        if (badgeEl) {
            badgeEl.textContent = label;
            badgeEl.className   = 'scale-badge scale-set';
        }
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

    // ═══════════════════════════════════════════════════════════════════════════
    // SESSION 2 — MEASUREMENT TOOLS
    // ═══════════════════════════════════════════════════════════════════════════

    // ── Load page measurements from server ────────────────────────────────────
    function loadPageMeasurements(pageId) {
        if (!pageId) return;
        fetch(`/project/${state.projectId}/takeoff/page/${pageId}/measurements`)
            .then(r => r.json())
            .then(data => {
                state.measurements = data.measurements || [];
                // Sync scale from server
                if (data.scale_pixels_per_foot) {
                    state.scalePixelsPerFoot = data.scale_pixels_per_foot;
                    // Update in-memory plan page scale_set flag
                    const plan = state.plans.find(p => p.id === state.currentPlanId);
                    if (plan) {
                        const page = plan.pages.find(p => p.id === pageId);
                        if (page) page.scale_set = true;
                    }
                    _updateStatusBarScale(data.scale_pixels_per_foot);
                }
                renderMeasurements(state.measurements);
                _updateDataTable();
            })
            .catch(err => console.error('[TK] loadPageMeasurements:', err));
    }

    // ── Scale tool — 2-click workflow ─────────────────────────────────────────
    function _scaleToolClick(pdf) {
        if (_scaleClickState === 0) {
            // First click: place point A
            _scalePointA    = pdf;
            _scaleClickState = 1;
            _drawScalePoint(pdf, 'A');
        } else {
            // Second click: compute distance, open modal for dimension entry
            const dx   = pdf.x - _scalePointA.x;
            const dy   = pdf.y - _scalePointA.y;
            _scalePxDist = Math.sqrt(dx * dx + dy * dy);
            _drawScaleLine(_scalePointA, pdf);
            _pendingScalePPF = null; // will be set when user enters feet
            _openScaleModalDim();
        }
    }

    function _drawScalePoint(pdf, label) {
        const size = 8;
        const g    = new Konva.Group({ id: `scale-pt-${label}` });
        g.add(new Konva.Line({
            points: [pdf.x - size, pdf.y, pdf.x + size, pdf.y],
            stroke: '#EF4444', strokeWidth: 2,
        }));
        g.add(new Konva.Line({
            points: [pdf.x, pdf.y - size, pdf.x, pdf.y + size],
            stroke: '#EF4444', strokeWidth: 2,
        }));
        state.uiLayer.add(g);
        state.uiLayer.batchDraw();
    }

    function _drawScaleLine(a, b) {
        state.uiLayer.add(new Konva.Line({
            points: [a.x, a.y, b.x, b.y],
            stroke: '#EF4444', strokeWidth: 1.5, dash: [6, 4],
            id: 'scale-line',
        }));
        state.uiLayer.batchDraw();
    }

    function _openScaleModalDim() {
        // Switch scale modal to "enter known dimension" mode
        const modal   = document.getElementById('scale-modal');
        const dimMode = document.getElementById('scale-dim-mode');
        const pxMode  = document.getElementById('scale-px-mode');
        if (dimMode) dimMode.style.display = 'block';
        if (pxMode)  pxMode.style.display  = 'none';
        modal.style.display = 'flex';
    }

    // Called by "Set Scale" in the dimension-entry mode of the scale modal
    function saveScaleFromDim() {
        const ft  = parseFloat(document.getElementById('scale-feet').value)  || 0;
        const ins = parseFloat(document.getElementById('scale-inches').value) || 0;
        const knownFt = ft + ins / 12;
        if (knownFt <= 0 || _scalePxDist <= 0) {
            alert('Enter a valid dimension.'); return;
        }
        _pendingScalePPF = _scalePxDist / knownFt;
        saveScale();
    }

    // ── Drawing tools — click handler ─────────────────────────────────────────
    function _drawToolClick(pdf, e) {
        // Double-click fires click + dblclick — ignore second click of a dblclick
        if (e && e.evt && e.evt.detail >= 2) return;

        // If area tool: check if clicking near first vertex to close
        if (state.activeTool === 'area' && state.currentDrawing.length >= 3) {
            const first = state.currentDrawing[0];
            const dx = pdf.x - first.x;
            const dy = pdf.y - first.y;
            const scale = state.stage.scaleX();
            if (Math.sqrt(dx * dx + dy * dy) * scale < 12) {
                _completeDraw();
                return;
            }
        }

        state.currentDrawing.push(pdf);
        _redrawCurrentSegments();
        _updateStatusDraw();
    }

    function _countToolClick(pdf) {
        if (!state.activeItemId) return;
        const item = state.items.find(i => i.id === state.activeItemId);
        if (!item) return;

        const norm = _normalizePt(pdf);
        fetch(`/project/${state.projectId}/takeoff/measurement`, {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({
                item_id:          state.activeItemId,
                page_id:          state.currentPageId,
                points_json:      JSON.stringify([norm]),
                calculated_value: 1,
                measurement_type: 'count',
            }),
        })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                _onMeasurementSaved(data);
            }
        })
        .catch(err => console.error('[TK] countToolClick:', err));
    }

    // ── Complete / cancel drawing ─────────────────────────────────────────────
    function _completeDraw() {
        const tool  = state.activeTool;
        const pts   = state.currentDrawing;

        if (tool === 'linear' && pts.length < 2) { _cancelDraw(); return; }
        if (tool === 'area'   && pts.length < 3) { _cancelDraw(); return; }

        const item = state.items.find(i => i.id === state.activeItemId);
        if (!item) { _cancelDraw(); return; }

        const ppf = state.scalePixelsPerFoot;

        // Calculate value
        let calcVal = 0;
        let calcSec = null;
        const mType = (tool === 'area') ? 'area' : 'linear';

        if (tool === 'linear') {
            for (let i = 1; i < pts.length; i++) {
                const dx = pts[i].x - pts[i-1].x;
                const dy = pts[i].y - pts[i-1].y;
                calcVal += Math.sqrt(dx * dx + dy * dy);
            }
            calcVal = ppf ? calcVal / ppf : calcVal;

        } else if (tool === 'area') {
            // Shoelace formula for area
            let areaPx = 0;
            const n = pts.length;
            for (let i = 0; i < n; i++) {
                const j = (i + 1) % n;
                areaPx += pts[i].x * pts[j].y;
                areaPx -= pts[j].x * pts[i].y;
            }
            areaPx = Math.abs(areaPx) / 2;
            calcVal = ppf ? areaPx / (ppf * ppf) : areaPx;
            // Perimeter
            let perimPx = 0;
            for (let i = 0; i < n; i++) {
                const j = (i + 1) % n;
                const dx = pts[j].x - pts[i].x;
                const dy = pts[j].y - pts[i].y;
                perimPx += Math.sqrt(dx * dx + dy * dy);
            }
            calcSec = ppf ? perimPx / ppf : perimPx;
        }

        const normPts = pts.map(p => _normalizePt(p));
        fetch(`/project/${state.projectId}/takeoff/measurement`, {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({
                item_id:              state.activeItemId,
                page_id:              state.currentPageId,
                points_json:          JSON.stringify(normPts),
                calculated_value:     Math.round(calcVal * 100) / 100,
                calculated_secondary: calcSec ? Math.round(calcSec * 100) / 100 : null,
                measurement_type:     mType,
            }),
        })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                _onMeasurementSaved(data);
                state.currentDrawing = [];
                state.uiLayer.find('#draw-preview').forEach(n => n.destroy());
                state.uiLayer.find('#draw-segments').forEach(n => n.destroy());
                state.uiLayer.batchDraw();
                document.getElementById('tk-status-draw').textContent = '';
            }
        })
        .catch(err => console.error('[TK] completeDraw:', err));
    }

    function _cancelDraw() {
        state.currentDrawing = [];
        if (state.uiLayer) {
            state.uiLayer.find('#draw-preview').forEach(n => n.destroy());
            state.uiLayer.find('#draw-segments').forEach(n => n.destroy());
            state.uiLayer.batchDraw();
        }
        const sdEl = document.getElementById('tk-status-draw');
        if (sdEl) sdEl.textContent = '';
    }

    function _removeLastPoint() {
        if (state.currentDrawing.length === 0) return;
        state.currentDrawing.pop();
        _redrawCurrentSegments();
        _updateStatusDraw();
    }

    function _onMeasurementSaved(data) {
        // Reload measurements for current page and refresh item totals
        loadPageMeasurements(state.currentPageId);
        fetchItems();
    }

    // ── Draw preview (live dashed line from last point to cursor) ─────────────
    function _updateDrawPreview(cursorPdf) {
        if (state.currentDrawing.length === 0) return;
        const last = state.currentDrawing[state.currentDrawing.length - 1];

        // Remove stale preview line
        state.uiLayer.find('#draw-preview').forEach(n => n.destroy());

        const item = state.items.find(i => i.id === state.activeItemId);
        const col  = item ? item.color : '#2D5BFF';

        state.uiLayer.add(new Konva.Line({
            id:          'draw-preview',
            points:      [last.x, last.y, cursorPdf.x, cursorPdf.y],
            stroke:      col,
            strokeWidth: 1.5,
            dash:        [8, 5],
            opacity:     0.7,
            listening:   false,
        }));
        state.uiLayer.batchDraw();
    }

    function _redrawCurrentSegments() {
        state.uiLayer.find('#draw-segments').forEach(n => n.destroy());
        const pts  = state.currentDrawing;
        if (pts.length < 2) {
            state.uiLayer.batchDraw();
            return;
        }
        const item = state.items.find(i => i.id === state.activeItemId);
        const col  = item ? item.color : '#2D5BFF';
        const flat = pts.flatMap(p => [p.x, p.y]);

        state.uiLayer.add(new Konva.Line({
            id:          'draw-segments',
            points:      flat,
            stroke:      col,
            strokeWidth: 2,
            listening:   false,
        }));

        // Vertex dots
        pts.forEach((pt, idx) => {
            state.uiLayer.add(new Konva.Circle({
                id:          'draw-segments',
                x:           pt.x,
                y:           pt.y,
                radius:      idx === 0 ? 5 : 4,
                fill:        idx === 0 ? '#FFFFFF' : col,
                stroke:      col,
                strokeWidth: 1.5,
                listening:   false,
            }));
        });
        state.uiLayer.batchDraw();
    }

    function _updateStatusDraw() {
        const sdEl = document.getElementById('tk-status-draw');
        if (!sdEl) return;
        const pts = state.currentDrawing;
        if (pts.length < 2) { sdEl.textContent = ''; return; }
        const ppf = state.scalePixelsPerFoot;
        let total = 0;
        for (let i = 1; i < pts.length; i++) {
            const dx = pts[i].x - pts[i-1].x;
            const dy = pts[i].y - pts[i-1].y;
            total += Math.sqrt(dx * dx + dy * dy);
        }
        const val = ppf ? (total / ppf).toFixed(1) + ' FT' : total.toFixed(0) + ' px';
        sdEl.textContent = `Drawing: ${val}`;
    }

    // ── Normalize / denormalize points ────────────────────────────────────────
    function _normalizePt(pdf) {
        return {
            x: state.renderWidth  > 0 ? pdf.x / state.renderWidth  : 0,
            y: state.renderHeight > 0 ? pdf.y / state.renderHeight : 0,
        };
    }

    function _denormalizePt(norm) {
        return {
            x: norm.x * state.renderWidth,
            y: norm.y * state.renderHeight,
        };
    }

    // ── Render measurements onto measureLayer ─────────────────────────────────
    function renderMeasurements(measurements) {
        if (!state.measureLayer) return;
        state.measureLayer.destroyChildren();

        const ppf = state.scalePixelsPerFoot;

        measurements.forEach(m => {
            let pts;
            try {
                pts = JSON.parse(m.points_json);
            } catch (e) {
                return;
            }
            if (!pts || pts.length === 0) return;

            // Denormalize
            const dpts = pts.map(p => _denormalizePt(p));
            const flat  = dpts.flatMap(p => [p.x, p.y]);
            const color = m.item_color || '#2D5BFF';
            const alpha = m.item_opacity != null ? m.item_opacity : 0.5;
            let shape;

            switch (m.measurement_type) {
                case 'area':
                    shape = new Konva.Line({
                        id:          'meas_' + m.id,
                        points:      flat,
                        closed:      true,
                        fill:        color,
                        stroke:      color,
                        strokeWidth: 1.5,
                        opacity:     alpha,
                        listening:   true,
                    });
                    break;

                case 'linear_with_width': {
                    const sw = (m.item_width_ft && ppf) ? m.item_width_ft * ppf : 4;
                    shape = new Konva.Line({
                        id:          'meas_' + m.id,
                        points:      flat,
                        stroke:      color,
                        strokeWidth: sw,
                        opacity:     alpha,
                        lineCap:     'round',
                        lineJoin:    'round',
                        listening:   true,
                    });
                    break;
                }

                case 'count':
                    shape = new Konva.Circle({
                        id:          'meas_' + m.id,
                        x:           dpts[0].x,
                        y:           dpts[0].y,
                        radius:      8,
                        fill:        color,
                        stroke:      '#FFFFFF',
                        strokeWidth: 1.5,
                        opacity:     alpha,
                        listening:   true,
                    });
                    break;

                default: // linear
                    shape = new Konva.Line({
                        id:          'meas_' + m.id,
                        points:      flat,
                        stroke:      color,
                        strokeWidth: 2,
                        opacity:     alpha,
                        lineCap:     'round',
                        lineJoin:    'round',
                        listening:   true,
                    });
            }

            if (shape) {
                shape.on('click', () => selectMeasurement(m.id));
                state.measureLayer.add(shape);
            }
        });

        state.measureLayer.batchDraw();
    }

    // ── Measurement selection ─────────────────────────────────────────────────
    function selectMeasurement(measId) {
        state.selectedMeasId = measId;
        state.uiLayer.find('[id^="sel-"]').forEach(n => n.destroy());

        const m = state.measurements.find(x => x.id === measId);
        if (!m) return;

        let pts;
        try { pts = JSON.parse(m.points_json); } catch (e) { return; }
        const dpts = pts.map(p => _denormalizePt(p));

        // Blue square handles at each vertex
        dpts.forEach(pt => {
            state.uiLayer.add(new Konva.Rect({
                id:          'sel-handle',
                x:           pt.x - 5,
                y:           pt.y - 5,
                width:       10,
                height:      10,
                fill:        '#2D5BFF',
                stroke:      '#FFFFFF',
                strokeWidth: 1.5,
                listening:   false,
            }));
        });
        state.uiLayer.batchDraw();

        // Open props panel for this item
        if (m.item_id) openPropsPanel(m.item_id);
    }

    function deselectMeasurement() {
        state.selectedMeasId = null;
        if (state.uiLayer) {
            state.uiLayer.find('[id^="sel-"]').forEach(n => n.destroy());
            state.uiLayer.batchDraw();
        }
    }

    function deleteSelectedMeasurement() {
        if (!state.selectedMeasId) return;
        if (!confirm('Delete this measurement?')) return;
        const measId = state.selectedMeasId;
        fetch(`/project/${state.projectId}/takeoff/measurement/${measId}`, { method: 'DELETE' })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    deselectMeasurement();
                    _onMeasurementSaved(data);
                }
            })
            .catch(err => console.error('[TK] deleteSelectedMeasurement:', err));
    }

    function undoLastMeasurement() {
        if (state.measurements.length === 0) return;
        const last = state.measurements[state.measurements.length - 1];
        fetch(`/project/${state.projectId}/takeoff/measurement/${last.id}`, { method: 'DELETE' })
            .then(r => r.json())
            .then(data => {
                if (data.success) _onMeasurementSaved(data);
            })
            .catch(err => console.error('[TK] undoLastMeasurement:', err));
    }

    // ── Active item management ────────────────────────────────────────────────
    function setActiveItem(itemId) {
        state.activeItemId = itemId;
        _renderItemList();
        openPropsPanel(itemId);
    }

    // ── Properties panel ──────────────────────────────────────────────────────
    function openPropsPanel(itemId) {
        if (!itemId) return;
        const item = state.items.find(i => i.id === itemId);
        if (!item) return;

        state.activeItemId = itemId;
        const panel = document.getElementById('tk-props-panel');
        if (!panel) return;

        // Populate fields
        document.getElementById('pp-name').value         = item.name;
        document.getElementById('pp-type').value         = item.measurement_type;
        document.getElementById('pp-opacity').value      = Math.round(item.opacity * 100);
        document.getElementById('pp-opacity-label').textContent = Math.round(item.opacity * 100) + '%';
        document.getElementById('pp-notes').value        = item.assembly_notes || '';
        document.getElementById('pp-division').value     = item.division || '';

        // Color swatches
        document.querySelectorAll('#pp-color-swatches .color-swatch').forEach(s => {
            s.classList.toggle('selected', s.dataset.color === item.color);
        });
        document.getElementById('pp-color').value = item.color;

        // Width fields (show/hide for linear_with_width)
        const widthRow = document.getElementById('pp-width-row');
        if (widthRow) {
            widthRow.style.display =
                item.measurement_type === 'linear_with_width' ? '' : 'none';
        }
        if (item.width_ft) {
            const ftFull  = Math.floor(item.width_ft);
            const insFrac = (item.width_ft - ftFull) * 12;
            const wftEl   = document.getElementById('pp-width-ft');
            const winEl   = document.getElementById('pp-width-in');
            if (wftEl) wftEl.value = ftFull  || '';
            if (winEl) winEl.value = insFrac ? insFrac.toFixed(1) : '';
        }
        const solEl = document.getElementById('pp-sol');
        if (solEl) solEl.value = item.side_of_line || 'center';

        // Measurements list in panel
        const measListEl = document.getElementById('pp-meas-list');
        if (measListEl) {
            measListEl.innerHTML = '';
            const pageMeas = state.measurements.filter(m => m.item_id === itemId);
            if (pageMeas.length === 0) {
                measListEl.innerHTML = '<div class="pp-meas-empty">No measurements on this page.</div>';
            } else {
                pageMeas.forEach((m, idx) => {
                    const unit = _unitForType(m.measurement_type);
                    const val  = (m.calculated_value || 0).toFixed(2);
                    const row  = document.createElement('div');
                    row.className = 'pp-meas-row';
                    row.innerHTML = `
                        <span class="pp-meas-label">Measurement ${idx + 1}</span>
                        <span class="pp-meas-val">${val} ${unit}</span>
                    `;
                    measListEl.appendChild(row);
                });
            }
        }

        panel.classList.add('open');
        document.getElementById('pp-item-id').value = itemId;
    }

    function closePropsPanel() {
        const panel = document.getElementById('tk-props-panel');
        if (panel) panel.classList.remove('open');
    }

    function savePropsPanel() {
        const itemId = parseInt(document.getElementById('pp-item-id').value);
        if (!itemId) return;

        const ftVal  = parseFloat(document.getElementById('pp-width-ft')?.value) || 0;
        const inVal  = parseFloat(document.getElementById('pp-width-in')?.value) || 0;
        const wFt    = ftVal + inVal / 12;

        const payload = {
            name:           document.getElementById('pp-name').value.trim(),
            color:          document.getElementById('pp-color').value,
            opacity:        parseInt(document.getElementById('pp-opacity').value) / 100,
            width_ft:       wFt > 0 ? wFt : null,
            side_of_line:   document.getElementById('pp-sol')?.value || 'center',
            assembly_notes: document.getElementById('pp-notes').value,
            division:       document.getElementById('pp-division').value,
        };

        fetch(`/project/${state.projectId}/takeoff/item/${itemId}`, {
            method:  'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify(payload),
        })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                fetchItems();
                renderMeasurements(state.measurements);
                closePropsPanel();
                _showToast('Saved', 'ok');
            } else {
                alert('Error: ' + (data.error || 'Save failed'));
            }
        })
        .catch(err => console.error('[TK] savePropsPanel:', err));
    }

    // ── Toast notification ────────────────────────────────────────────────────
    function _showToast(msg, type = 'ok') {
        let toast = document.getElementById('tk-toast');
        if (!toast) {
            toast = document.createElement('div');
            toast.id = 'tk-toast';
            document.getElementById('takeoff-app').appendChild(toast);
        }
        toast.textContent = msg;
        toast.className   = `tk-toast tk-toast-${type} visible`;
        clearTimeout(toast._timer);
        toast._timer = setTimeout(() => toast.classList.remove('visible'), 2800);
    }

    // ── Data table draggable ──────────────────────────────────────────────────
    function _initDataTableDrag() {
        const table = document.getElementById('tk-data-table');
        if (!table) return;
        let dragging = false, ox = 0, oy = 0, sx = 0, sy = 0;

        table.addEventListener('mousedown', e => {
            if (e.target.closest('#tk-dt-rows')) return; // don't drag from rows
            dragging = true;
            const rect = table.getBoundingClientRect();
            ox = e.clientX - rect.left;
            oy = e.clientY - rect.top;
            sx = rect.left;
            sy = rect.top;
            table.style.cursor = 'grabbing';
            e.preventDefault();
        });

        document.addEventListener('mousemove', e => {
            if (!dragging) return;
            table.style.left   = (e.clientX - ox) + 'px';
            table.style.top    = (e.clientY - oy) + 'px';
            table.style.bottom = 'auto';
        });

        document.addEventListener('mouseup', () => {
            dragging = false;
            table.style.cursor = '';
        });
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
        // Session 2 additions
        saveScaleFromDim,
        loadPageMeasurements,
        renderMeasurements,
        selectMeasurement,
        deselectMeasurement,
        deleteSelectedMeasurement,
        undoLastMeasurement,
        setActiveItem,
        openPropsPanel,
        closePropsPanel,
        savePropsPanel,
        _state: state,
    };

})();

// Boot on DOMContentLoaded
document.addEventListener('DOMContentLoaded', TK.init);
