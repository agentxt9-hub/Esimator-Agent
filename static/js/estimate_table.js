/* estimate_table.js — Session 22: TanStack Table v8
   React component for the Zenbid estimate grid.
   Loaded via <script type="text/babel"> (Babel Standalone).
   CDN globals: React, ReactDOM, ReactTable, XLSX
*/

'use strict';

(function () {
  const { useState, useEffect, useRef, useCallback, useMemo } = React;
  const {
    useReactTable,
    getCoreRowModel,
    getSortedRowModel,
    getFilteredRowModel,
    flexRender,
  } = ReactTable;

  // ─── DESIGN TOKENS ────────────────────────────────────────────────────────
  const ZB = {
    bg:      '#0F1419',
    card:    '#1A1F26',
    input:   '#252B33',
    sidebar: '#16181D',
    blue:    '#2D5BFF',
    coral:   '#FF6B35',
    text:    '#E8EAED',
    muted:   '#6B7280',
    border:  '#2A3040',
    success: '#22C55E',
    warn:    '#F59E0B',
    danger:  '#EF4444',
  };

  // Division colors (cycling 8 colors for group headers)
  const DIV_COLORS = [
    '#2D5BFF', '#14B8A6', '#8B5CF6', '#22C55E',
    '#FF6B35', '#F59E0B', '#EC4899', '#6B7280',
  ];

  // AI badge config
  const AI_STATUS = {
    verified:     { label: 'Verified',    color: '#22C55E', icon: 'check'     },
    suggestion:   { label: 'AI Tip',      color: '#2D5BFF', icon: 'sparkles'  },
    gap:          { label: 'Scope Gap',   color: '#FF6B35', icon: 'alert'     },
    'live-price': { label: 'Live Price',  color: '#F59E0B', icon: 'trending'  },
  };

  const UNIT_OPTIONS = ['SF', 'LF', 'CY', 'EA', 'LB', 'HR', 'LS', 'SQ', 'TON', 'GAL'];

  // ─── SVG ICONS ────────────────────────────────────────────────────────────
  function Icon({ name, size = 14, color = 'currentColor', style = {} }) {
    const paths = {
      check:      'M20 6L9 17l-5-5',
      sparkles:   'M9.5 2A.5.5 0 019 1.5h6a.5.5 0 010 1h-1v2.088A7.001 7.001 0 0112 21a7 7 0 01-.688-13.919L11 5.006V2.5h-1A.5.5 0 019.5 2zM12 7a5 5 0 100 10A5 5 0 0012 7z',
      alert:      'M12 9v4m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z',
      trending:   'M23 6l-9.5 9.5-5-5L1 18',
      chevron:    'M6 9l6 6 6-6',
      search:     'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z',
      x:          'M18 6L6 18M6 6l12 12',
      plus:       'M12 5v14M5 12h14',
      columns:    'M4 6h16M4 12h16M4 18h7',
      group:      'M17 8h2a2 2 0 012 2v6a2 2 0 01-2 2h-2m-4-8H9a2 2 0 00-2 2v6a2 2 0 002 2h4m-4-8V6a2 2 0 012-2h4a2 2 0 012 2v2m-4 0h4',
      download:   'M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4m4-5l5 5 5-5m-5 5V3',
      expand:     'M8 3H5a2 2 0 00-2 2v3m18 0V5a2 2 0 00-2-2h-3m0 18h3a2 2 0 002-2v-3M3 16v3a2 2 0 002 2h3',
      collapse:   'M8 3v3a2 2 0 01-2 2H3m18 0h-3a2 2 0 01-2-2V3m0 18v-3a2 2 0 012-2h3M3 16h3a2 2 0 012 2v3',
      sort_asc:   'M8 15l4-8 4 8M3 7h6m3 0h6',
      sort_desc:  'M8 9l4 8 4-8M3 17h6m3 0h6',
      'check-circle': 'M22 11.08V12a10 10 0 11-5.93-9.14M22 4L12 14.01l-3-3',
    };
    const d = paths[name] || paths.x;
    return (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
           stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
           style={style}>
        <path d={d} />
      </svg>
    );
  }

  // ─── HELPERS ──────────────────────────────────────────────────────────────
  function fmt$(n) {
    const v = parseFloat(n) || 0;
    return '$' + v.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  function fmtN(n, digits = 4) {
    const v = parseFloat(n) || 0;
    return v % 1 === 0 ? v.toString() : v.toFixed(digits).replace(/\.?0+$/, '');
  }

  function divColorFor(key, divColorMap) {
    if (!divColorMap[key]) {
      const idx = Object.keys(divColorMap).length % DIV_COLORS.length;
      divColorMap[key] = DIV_COLORS[idx];
    }
    return divColorMap[key];
  }

  // ─── COLUMN DEFINITIONS ───────────────────────────────────────────────────
  const DEFAULT_COL_VISIBILITY = {
    description: true, csi_division: true, phase: true, trade: false,
    qty: true, unit: true, labor_rate: true, mat_cost: true,
    ai_status: true, line_total: true,
  };

  const DEFAULT_COL_ORDER = [
    'description', 'csi_division', 'phase', 'trade',
    'qty', 'unit', 'labor_rate', 'mat_cost', 'ai_status', 'line_total',
  ];

  const COL_META = {
    description:  { label: 'Description',   width: 240, sortable: true,  groupable: false, editable: true,  align: 'left'   },
    csi_division: { label: 'CSI Division',  width: 150, sortable: true,  groupable: true,  editable: false, align: 'left'   },
    phase:        { label: 'Phase',         width: 110, sortable: true,  groupable: true,  editable: true,  align: 'left'   },
    trade:        { label: 'Trade',         width: 110, sortable: true,  groupable: true,  editable: true,  align: 'left'   },
    qty:          { label: 'Qty',           width: 80,  sortable: true,  groupable: false, editable: true,  align: 'right'  },
    unit:         { label: 'Unit',          width: 65,  sortable: false, groupable: true,  editable: true,  align: 'center' },
    labor_rate:   { label: 'Labor/Unit',    width: 105, sortable: true,  groupable: false, editable: true,  align: 'right'  },
    mat_cost:     { label: 'Mat/Unit',      width: 105, sortable: true,  groupable: false, editable: true,  align: 'right'  },
    ai_status:    { label: 'AI Status',     width: 130, sortable: true,  groupable: true,  editable: false, align: 'left'   },
    line_total:   { label: 'Line Total',    width: 120, sortable: true,  groupable: false, editable: false, align: 'right'  },
  };

  // ─── AI STATUS BADGE ──────────────────────────────────────────────────────
  function AiBadge({ status, confidence, note }) {
    const [tip, setTip] = useState(false);
    const cfg = AI_STATUS[status] || AI_STATUS.verified;
    const bg  = cfg.color + '1F'; // 12% opacity hex
    return (
      <div style={{ position: 'relative', display: 'inline-block' }}
           onMouseEnter={() => note && setTip(true)}
           onMouseLeave={() => setTip(false)}>
        <span style={{
          display: 'inline-flex', alignItems: 'center', gap: 4,
          padding: '2px 8px', borderRadius: 20,
          background: bg, border: `1px solid ${cfg.color}33`,
          color: cfg.color, fontSize: 11, fontWeight: 600,
          fontFamily: 'IBM Plex Sans, sans-serif', whiteSpace: 'nowrap',
        }}>
          <Icon name={cfg.icon} size={11} color={cfg.color} />
          {cfg.label}
          {confidence != null && confidence < 100 &&
            <span style={{ color: cfg.color + 'AA', fontSize: 10 }}>{confidence}%</span>
          }
        </span>
        {tip && note && (
          <div className="et-tooltip" style={{
            background: ZB.card, border: `1px solid ${cfg.color}44`,
            borderRadius: 6, padding: '8px 12px',
            boxShadow: '0 12px 40px rgba(0,0,0,0.7)',
            minWidth: 180, maxWidth: 260,
          }}>
            <div style={{ color: cfg.color, fontWeight: 700, fontSize: 11, marginBottom: 4 }}>{cfg.label}</div>
            <div style={{ color: ZB.text, fontSize: 12, lineHeight: 1.4, whiteSpace: 'normal' }}>{note}</div>
            <div className="et-tooltip-arrow" style={{ borderTopColor: ZB.card }} />
          </div>
        )}
      </div>
    );
  }

  // ─── INLINE EDIT INPUT ────────────────────────────────────────────────────
  function EditInput({ value, onCommit, onCancel, align, isNumeric }) {
    const ref = useRef(null);
    const [val, setVal] = useState(value);

    useEffect(() => { ref.current && ref.current.select(); }, []);

    function commit() { onCommit(val); }

    function onKey(e) {
      if (e.key === 'Enter') { e.preventDefault(); commit(); }
      if (e.key === 'Tab')   { e.preventDefault(); commit(); }
      if (e.key === 'Escape'){ e.preventDefault(); onCancel(); }
    }

    return (
      <input ref={ref} value={val} onChange={e => setVal(e.target.value)}
        onBlur={commit} onKeyDown={onKey}
        className="et-mono et-cell-editing"
        style={{
          width: '100%', padding: '4px 6px', fontSize: 12,
          fontFamily: isNumeric ? 'IBM Plex Mono, monospace' : 'IBM Plex Sans, sans-serif',
          background: 'rgba(45,91,255,0.12)', border: '1px solid rgba(45,91,255,0.8)',
          borderRadius: 3, color: ZB.text, outline: 'none', textAlign: align || 'left',
          boxSizing: 'border-box',
        }}
      />
    );
  }

  // ─── MAIN COMPONENT ───────────────────────────────────────────────────────
  function EstimateTable({ projectId, projectName }) {
    const STATE_KEY = `zenbid_estimate_cols_${projectId}`;

    // ── Data
    const [data, setData]     = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError]   = useState(null);

    // ── Column state
    const [columnOrder,      setColumnOrder]      = useState(DEFAULT_COL_ORDER);
    const [columnVisibility, setColumnVisibility] = useState(DEFAULT_COL_VISIBILITY);
    const [columnSizing,     setColumnSizing]     = useState(() => {
      const s = {};
      Object.entries(COL_META).forEach(([k, v]) => { s[k] = v.width; });
      return s;
    });

    // ── Table state
    const [sorting,       setSorting]       = useState([]);
    const [globalFilter,  setGlobalFilter]  = useState('');
    const [rowSelection,  setRowSelection]  = useState({});
    const [groupBy,       setGroupBy]       = useState('csi_division');
    const [collapsedGroups, setCollapsedGroups] = useState(new Set());
    const [editingCell,   setEditingCell]   = useState(null); // {rowId, colId}

    // ── UI state
    const [showColPanel,  setShowColPanel]  = useState(false);
    const [showGroupDD,   setShowGroupDD]   = useState(false);
    const [showExportDD,  setShowExportDD]  = useState(false);
    const [showAddPanel,  setShowAddPanel]  = useState(false);
    const [dragSrcCol,    setDragSrcCol]    = useState(null);
    const [dragOverCol,   setDragOverCol]   = useState(null);
    const [resizing,      setResizing]      = useState(null); // {colId, startX, startW}

    // ── Add panel form state
    const [addForm, setAddForm] = useState({
      description: '', csi_division: '', phase: '', qty: '', unit: 'SF',
      labor_rate: '', mat_cost: '',
    });

    // ── Div color map (stable ref)
    const divColorMap = useRef({});

    // ─── Load from localStorage
    useEffect(() => {
      try {
        const saved = JSON.parse(localStorage.getItem(STATE_KEY) || '{}');
        if (saved.columnOrder)      setColumnOrder(saved.columnOrder);
        if (saved.columnVisibility) setColumnVisibility(saved.columnVisibility);
        if (saved.columnWidths) {
          setColumnSizing(prev => ({ ...prev, ...saved.columnWidths }));
        }
      } catch (_) {}
    }, []);

    // ─── Save to localStorage
    useEffect(() => {
      try {
        localStorage.setItem(STATE_KEY, JSON.stringify({
          columnOrder, columnVisibility, columnWidths: columnSizing,
        }));
      } catch (_) {}
    }, [columnOrder, columnVisibility, columnSizing]);

    // ─── Fetch line items
    useEffect(() => {
      setLoading(true);
      fetch(`/api/projects/${projectId}/line_items`)
        .then(r => r.ok ? r.json() : Promise.reject(r.status))
        .then(d => { setData(d.items || []); setLoading(false); })
        .catch(e => { setError(`Failed to load items (${e})`); setLoading(false); });
    }, [projectId]);

    // ─── Build TanStack columns
    const columns = useMemo(() => columnOrder
      .filter(id => id in COL_META)
      .map(id => {
        const meta = COL_META[id];
        return {
          id,
          accessorKey: id,
          header: meta.label,
          size: columnSizing[id] || meta.width,
          minSize: 60,
          enableSorting: meta.sortable,
          cell: ({ row, column }) => {
            const val = row.original[id];
            const isEditing = editingCell &&
              editingCell.rowId === row.id && editingCell.colId === id;

            if (isEditing && meta.editable) {
              const isNum = ['qty', 'labor_rate', 'mat_cost'].includes(id);
              return (
                <EditInput
                  value={String(val ?? '')}
                  isNumeric={isNum}
                  align={meta.align}
                  onCommit={newVal => commitEdit(row.original.id, id, newVal)}
                  onCancel={() => setEditingCell(null)}
                />
              );
            }

            if (id === 'ai_status') {
              return (
                <AiBadge
                  status={row.original.ai_status}
                  confidence={row.original.ai_confidence}
                  note={row.original.ai_note}
                />
              );
            }

            if (id === 'line_total') {
              const isGap = row.original.ai_status === 'gap';
              return (
                <span className="et-mono"
                  style={{ color: isGap ? ZB.coral : ZB.text, fontWeight: 500 }}>
                  {fmt$(val)}
                </span>
              );
            }

            if (id === 'qty') {
              return <span className="et-mono" style={{ color: ZB.text }}>{fmtN(val)}</span>;
            }

            if (id === 'labor_rate' || id === 'mat_cost') {
              return <span className="et-mono" style={{ color: ZB.text }}>{fmt$(val)}</span>;
            }

            return <span style={{ color: ZB.text }}>{val || ''}</span>;
          },
        };
      }), [columnOrder, columnSizing, editingCell]);

    // ─── TanStack table instance
    const table = useReactTable({
      data,
      columns,
      state: {
        sorting,
        globalFilter,
        rowSelection,
        columnVisibility,
      },
      onSortingChange:       setSorting,
      onGlobalFilterChange:  setGlobalFilter,
      onRowSelectionChange:  setRowSelection,
      onColumnVisibilityChange: setColumnVisibility,
      getCoreRowModel:       getCoreRowModel(),
      getSortedRowModel:     getSortedRowModel(),
      getFilteredRowModel:   getFilteredRowModel(),
      enableRowSelection:    true,
      enableMultiRowSelection: true,
      getRowId: row => String(row.id),
    });

    // ─── Grouped rows (manual grouping)
    const GROUPABLE_COLS = Object.entries(COL_META)
      .filter(([, m]) => m.groupable)
      .map(([k]) => k);

    const groupedSections = useMemo(() => {
      const rows = table.getRowModel().rows;
      if (!groupBy) return [{ key: '__all__', rows, color: ZB.muted }];

      const seen = {};
      const order = [];
      rows.forEach(row => {
        const key = row.original[groupBy] || '(Unassigned)';
        if (!seen[key]) { seen[key] = []; order.push(key); }
        seen[key].push(row);
      });

      return order.map(key => ({
        key,
        rows: seen[key],
        color: divColorFor(key, divColorMap.current),
      }));
    }, [table.getRowModel().rows, groupBy]);

    // ─── Grand total (filtered rows only)
    const grandTotal = useMemo(() =>
      table.getRowModel().rows.reduce((s, r) => s + (parseFloat(r.original.line_total) || 0), 0),
      [table.getRowModel().rows]
    );

    const selectedCount = Object.keys(rowSelection).length;
    const gapCount = data.filter(d => d.ai_status === 'gap').length;

    // ─── INLINE EDIT ──────────────────────────────────────────────────────
    function commitEdit(itemId, field, rawValue) {
      setEditingCell(null);
      const isNum = ['qty', 'labor_rate', 'mat_cost'].includes(field);
      const newVal = isNum ? parseFloat(rawValue) || 0 : rawValue;

      // Optimistic update
      const prevData = data;
      setData(prev => prev.map(row => {
        if (row.id !== itemId) return row;
        const updated = { ...row, [field]: newVal };
        if (['qty', 'labor_rate', 'mat_cost'].includes(field)) {
          updated.line_total =
            (field === 'qty'        ? newVal : row.qty)        *
            ((field === 'labor_rate' ? newVal : row.labor_rate) +
             (field === 'mat_cost'   ? newVal : row.mat_cost));
        }
        return updated;
      }));

      fetch(`/api/line_items/${itemId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ [field]: newVal }),
      })
        .then(r => r.ok ? r.json() : Promise.reject(r.status))
        .then(updated => {
          setData(prev => prev.map(row => row.id === itemId ? { ...row, ...updated } : row));
        })
        .catch(() => {
          setData(prevData); // rollback
          alert('Save failed — changes reverted.');
        });
    }

    function handleCellDblClick(rowId, colId) {
      if (!COL_META[colId]?.editable) return;
      setEditingCell({ rowId, colId });
    }

    // ─── COLUMN DRAG REORDER ──────────────────────────────────────────────
    function onColDragStart(e, colId) { setDragSrcCol(colId); e.dataTransfer.effectAllowed = 'move'; }
    function onColDragOver(e, colId)  { e.preventDefault(); setDragOverCol(colId); }
    function onColDragLeave()         { setDragOverCol(null); }
    function onColDrop(e, targetId)   {
      e.preventDefault();
      setDragOverCol(null);
      if (!dragSrcCol || dragSrcCol === targetId) return;
      setColumnOrder(prev => {
        const next = prev.filter(id => id !== dragSrcCol);
        const at   = next.indexOf(targetId);
        next.splice(at, 0, dragSrcCol);
        return next;
      });
      setDragSrcCol(null);
    }

    // ─── COLUMN RESIZE ────────────────────────────────────────────────────
    function onResizerMouseDown(e, colId) {
      e.preventDefault();
      e.stopPropagation();
      const startX = e.clientX;
      const startW = columnSizing[colId] || COL_META[colId]?.width || 100;
      setResizing({ colId, startX, startW });

      function onMove(ev) {
        const delta = ev.clientX - startX;
        setColumnSizing(prev => ({
          ...prev,
          [colId]: Math.max(60, startW + delta),
        }));
      }
      function onUp() {
        setResizing(null);
        window.removeEventListener('mousemove', onMove);
        window.removeEventListener('mouseup', onUp);
      }
      window.addEventListener('mousemove', onMove);
      window.addEventListener('mouseup', onUp);
    }

    // ─── ADD ITEM ────────────────────────────────────────────────────────
    function submitAddItem(e) {
      e.preventDefault();
      const body = {
        description:  addForm.description,
        csi_division: addForm.csi_division,
        phase:        addForm.phase,
        qty:          parseFloat(addForm.qty) || 0,
        unit:         addForm.unit,
        labor_rate:   parseFloat(addForm.labor_rate) || 0,
        mat_cost:     parseFloat(addForm.mat_cost) || 0,
      };

      fetch(`/api/projects/${projectId}/line_items`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
        .then(r => r.ok ? r.json() : Promise.reject(r.status))
        .then(item => {
          setData(prev => [{ ...item, _new: true }, ...prev]);
          setAddForm({ description: '', csi_division: '', phase: '', qty: '', unit: 'SF', labor_rate: '', mat_cost: '' });
          setShowAddPanel(false);
        })
        .catch(e => alert(`Failed to add item (${e})`));
    }

    // ─── EXPORT ──────────────────────────────────────────────────────────
    function buildExportRows() {
      const visibleCols = columnOrder.filter(id => columnVisibility[id] !== false);
      const headers = visibleCols.map(id => COL_META[id]?.label || id);
      const filteredRows = table.getRowModel().rows;
      const rows = filteredRows.map(row =>
        visibleCols.map(id => {
          const v = row.original[id];
          if (id === 'line_total' || id === 'labor_rate' || id === 'mat_cost') return parseFloat(v) || 0;
          return v ?? '';
        })
      );
      return { headers, rows };
    }

    function exportCSV() {
      const { headers, rows } = buildExportRows();
      const date = new Date().toISOString().slice(0, 10);
      const name = `zenbid-estimate-${projectName.replace(/\s+/g, '-')}-${date}`;
      const ws = XLSX.utils.aoa_to_sheet([headers, ...rows]);
      const wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, 'Estimate');
      XLSX.writeFile(wb, `${name}.csv`);
      setShowExportDD(false);
    }

    function exportXLSX() {
      const { headers, rows } = buildExportRows();
      const date = new Date().toISOString().slice(0, 10);
      const name = `zenbid-estimate-${projectName.replace(/\s+/g, '-')}-${date}`;
      const ws = XLSX.utils.aoa_to_sheet([headers, ...rows]);

      // Bold headers
      const headerRange = XLSX.utils.decode_range(ws['!ref'] || 'A1');
      for (let c = headerRange.s.c; c <= headerRange.e.c; c++) {
        const cell = ws[XLSX.utils.encode_cell({ r: 0, c })];
        if (cell) cell.s = { font: { bold: true } };
      }

      // Currency format for $-columns
      const currencyCols = columnOrder
        .filter(id => columnVisibility[id] !== false)
        .reduce((acc, id, i) => {
          if (['line_total', 'labor_rate', 'mat_cost'].includes(id)) acc.push(i);
          return acc;
        }, []);
      rows.forEach((_, ri) => {
        currencyCols.forEach(ci => {
          const cell = ws[XLSX.utils.encode_cell({ r: ri + 1, c: ci })];
          if (cell) cell.z = '$#,##0.00';
        });
      });

      const wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, 'Estimate');
      XLSX.writeFile(wb, `${name}.xlsx`);
      setShowExportDD(false);
    }

    // ─── HEADER ROW ──────────────────────────────────────────────────────
    function renderHeader() {
      const headerGroups = table.getHeaderGroups();
      return (
        <thead>
          {headerGroups.map(hg => (
            <tr key={hg.id}>
              {/* Selection checkbox column */}
              <th style={{
                width: 32, minWidth: 32, background: ZB.input,
                borderRight: `1px solid ${ZB.border}`,
                position: 'sticky', top: 0, zIndex: 3,
                textAlign: 'center', padding: '0 4px',
              }}>
                <input type="checkbox" className="et-checkbox"
                  checked={table.getIsAllRowsSelected()}
                  onChange={table.getToggleAllRowsSelectedHandler()}
                />
              </th>
              {hg.headers.map(header => {
                const colId = header.column.id;
                const meta  = COL_META[colId] || {};
                const isSorted = header.column.getIsSorted();
                const isDragOver = dragOverCol === colId;
                return (
                  <th key={header.id}
                    draggable
                    onDragStart={e => onColDragStart(e, colId)}
                    onDragOver={e  => onColDragOver(e, colId)}
                    onDragLeave={onColDragLeave}
                    onDrop={e => onColDrop(e, colId)}
                    onClick={meta.sortable ? header.column.getToggleSortingHandler() : undefined}
                    className={isDragOver ? 'et-th-drag-over' : ''}
                    style={{
                      width: columnSizing[colId] || meta.width,
                      minWidth: 60,
                      background: ZB.input,
                      color: ZB.muted,
                      fontSize: 10,
                      textTransform: 'uppercase',
                      letterSpacing: '0.07em',
                      padding: '8px 8px',
                      textAlign: meta.align || 'left',
                      borderRight: `1px solid ${ZB.border}`,
                      cursor: meta.sortable ? 'pointer' : 'default',
                      userSelect: 'none',
                      position: 'sticky',
                      top: 0,
                      zIndex: 2,
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      position: 'relative',
                    }}>
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                      {flexRender(header.column.columnDef.header, header.getContext())}
                      {isSorted === 'asc'  && <Icon name="sort_asc"  size={10} color={ZB.blue} />}
                      {isSorted === 'desc' && <Icon name="sort_desc" size={10} color={ZB.blue} />}
                    </span>
                    {/* Resize handle */}
                    <div
                      className={`et-resizer ${resizing?.colId === colId ? 'isResizing' : ''}`}
                      onMouseDown={e => onResizerMouseDown(e, colId)}
                    />
                  </th>
                );
              })}
            </tr>
          ))}
        </thead>
      );
    }

    // ─── BODY ROWS ────────────────────────────────────────────────────────
    function renderBody() {
      if (loading) {
        return (
          <tbody>
            <tr>
              <td colSpan={columnOrder.filter(id => columnVisibility[id] !== false).length + 1}
                style={{ padding: '40px', textAlign: 'center', color: ZB.muted }}>
                Loading estimate…
              </td>
            </tr>
          </tbody>
        );
      }
      if (error) {
        return (
          <tbody>
            <tr>
              <td colSpan={columnOrder.filter(id => columnVisibility[id] !== false).length + 1}
                style={{ padding: '40px', textAlign: 'center', color: ZB.danger }}>
                {error}
              </td>
            </tr>
          </tbody>
        );
      }
      if (groupedSections.length === 0 || (groupedSections.length === 1 && groupedSections[0].rows.length === 0)) {
        return (
          <tbody>
            <tr>
              <td colSpan={columnOrder.filter(id => columnVisibility[id] !== false).length + 1}
                style={{ padding: '50px', textAlign: 'center', color: ZB.muted, fontSize: 15 }}>
                No line items yet. Click <strong style={{ color: ZB.coral }}>+ Add Item</strong> to get started.
              </td>
            </tr>
          </tbody>
        );
      }

      const visibleColIds = columnOrder.filter(id => columnVisibility[id] !== false);
      const colSpan = visibleColIds.length + 1;

      const bodyRows = [];
      groupedSections.forEach(({ key, rows: gRows, color }) => {
        const isCollapsed = collapsedGroups.has(key);

        // Group header
        if (groupBy) {
          const groupTotal = gRows.reduce((s, r) => s + (parseFloat(r.original.line_total) || 0), 0);
          const gapRows    = gRows.filter(r => r.original.ai_status === 'gap');

          bodyRows.push(
            <tr key={`grp-${key}`}
              onClick={() => setCollapsedGroups(prev => {
                const next = new Set(prev);
                next.has(key) ? next.delete(key) : next.add(key);
                return next;
              })}
              style={{ cursor: 'pointer' }}>
              <td colSpan={colSpan} style={{
                borderLeft: `3px solid ${color}`,
                background: ZB.input,
                color: ZB.text,
                fontWeight: 700,
                fontSize: 12,
                padding: '8px 12px',
                borderTop: `1px solid ${ZB.border}`,
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <Icon name="chevron" size={12} color={ZB.muted}
                      style={{ transform: isCollapsed ? 'rotate(-90deg)' : 'none', transition: 'transform 0.2s' }} />
                    <span style={{ color }}>{key}</span>
                    <span style={{ color: ZB.muted, fontWeight: 400, fontSize: 11 }}>
                      {gRows.length} {gRows.length === 1 ? 'item' : 'items'}
                    </span>
                    {gapRows.length > 0 &&
                      <span style={{
                        background: ZB.coral + '22', border: `1px solid ${ZB.coral}44`,
                        color: ZB.coral, fontSize: 10, padding: '1px 6px', borderRadius: 10,
                      }}>
                        {gapRows.length} gap{gapRows.length > 1 ? 's' : ''}
                      </span>
                    }
                  </span>
                  <span className="et-mono" style={{ color, fontSize: 13 }}>{fmt$(groupTotal)}</span>
                </div>
              </td>
            </tr>
          );
        }

        // Data rows
        if (!isCollapsed) {
          gRows.forEach(row => {
            const isSelected = row.getIsSelected();
            bodyRows.push(
              <tr key={row.id} className={isSelected ? 'et-row-selected' : ''}
                style={{ borderBottom: `1px solid ${ZB.border}` }}>
                {/* Checkbox */}
                <td style={{
                  width: 32, textAlign: 'center', padding: '0 4px',
                  background: isSelected ? 'rgba(45,91,255,0.1)' : 'transparent',
                  borderRight: `1px solid ${ZB.border}`,
                }}>
                  <input type="checkbox" className="et-checkbox"
                    checked={isSelected}
                    onChange={row.getToggleSelectedHandler()}
                  />
                </td>
                {row.getVisibleCells().map(cell => {
                  const colId = cell.column.id;
                  const meta  = COL_META[colId] || {};
                  const isEditable = meta.editable;
                  const isEditing  = editingCell?.rowId === row.id && editingCell?.colId === colId;
                  return (
                    <td key={cell.id}
                      onDoubleClick={() => handleCellDblClick(row.id, colId)}
                      style={{
                        width: columnSizing[colId] || meta.width,
                        minWidth: 60,
                        padding: isEditing ? '2px 4px' : '6px 8px',
                        verticalAlign: 'middle',
                        borderRight: `1px solid ${ZB.border}`,
                        textAlign: meta.align || 'left',
                        cursor: isEditable && !isEditing ? 'text' : 'default',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: isEditing ? 'normal' : 'nowrap',
                        fontSize: 12,
                        fontFamily: ['qty', 'labor_rate', 'mat_cost', 'line_total'].includes(colId)
                          ? 'IBM Plex Mono, monospace' : 'IBM Plex Sans, sans-serif',
                        background: isSelected ? 'rgba(45,91,255,0.05)' : 'transparent',
                      }}>
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  );
                })}
              </tr>
            );
          });
        }
      });

      return <tbody>{bodyRows}</tbody>;
    }

    // ─── GRAND TOTAL ROW ──────────────────────────────────────────────────
    function renderGrandTotal() {
      const visibleColIds = columnOrder.filter(id => columnVisibility[id] !== false);
      const colSpan       = visibleColIds.length; // no +1 for checkbox
      const totalItems    = table.getRowModel().rows.length;

      return (
        <tfoot>
          <tr style={{ borderTop: `2px solid ${ZB.border}` }}>
            <td style={{ padding: '10px 12px', background: ZB.card }}>
              {/* Checkbox spacer */}
            </td>
            <td colSpan={colSpan} style={{ padding: '10px 12px', background: ZB.card }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{
                  color: ZB.muted, fontSize: 11, textTransform: 'uppercase',
                  letterSpacing: '0.07em', fontWeight: 600,
                }}>
                  ESTIMATE TOTAL — {totalItems} line item{totalItems !== 1 ? 's' : ''}
                </span>
                <span className="et-mono" style={{
                  color: ZB.coral, fontSize: 15, fontWeight: 700,
                }}>
                  {fmt$(grandTotal)}
                </span>
              </div>
            </td>
          </tr>
        </tfoot>
      );
    }

    // ─── TALLY FOOTER BANNER ──────────────────────────────────────────────
    function renderTallyBanner() {
      return (
        <div className="et-tally-footer" style={{
          borderRadius: '0 0 6px 6px', padding: '12px 16px',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12,
        }}>
          <div>
            <div style={{
              display: 'flex', alignItems: 'center', gap: 6,
              color: ZB.text, fontSize: 12, marginBottom: 3,
            }}>
              <Icon name="sparkles" size={13} color={ZB.blue} />
              <span>
                Tally found <strong style={{ color: ZB.coral }}>{gapCount}</strong> scope gap{gapCount !== 1 ? 's' : ''} ·
                Hover any badge for details · Double-click any cell to edit
              </span>
            </div>
            <div style={{ color: ZB.muted, fontSize: 11 }}>
              Drag column headers to reorder · Columns menu to show/hide · Group by any column
            </div>
          </div>
          <a href="#" style={{
            background: ZB.coral, color: '#fff', fontSize: 12, fontWeight: 600,
            padding: '6px 14px', borderRadius: 4, textDecoration: 'none', whiteSpace: 'nowrap',
          }}>
            Review All →
          </a>
        </div>
      );
    }

    // ─── COLUMN PANEL ─────────────────────────────────────────────────────
    function renderColumnPanel() {
      return (
        <div className="et-col-dropdown">
          {DEFAULT_COL_ORDER.map(id => {
            const meta    = COL_META[id];
            const visible = columnVisibility[id] !== false;
            return (
              <label key={id} style={{
                display: 'flex', alignItems: 'center', gap: 8,
                padding: '7px 14px', cursor: 'pointer', color: ZB.text, fontSize: 13,
              }}>
                <input type="checkbox" className="et-checkbox"
                  checked={visible}
                  onChange={() => setColumnVisibility(prev => ({ ...prev, [id]: !visible }))}
                />
                {meta.label}
              </label>
            );
          })}
        </div>
      );
    }

    // ─── GROUP-BY PANEL ───────────────────────────────────────────────────
    function renderGroupPanel() {
      const options = [
        { key: null,         label: 'None (flat list)' },
        ...GROUPABLE_COLS.map(k => ({ key: k, label: COL_META[k].label })),
      ];
      return (
        <div className="et-group-dropdown">
          {options.map(({ key, label }) => (
            <button key={String(key)} onClick={() => { setGroupBy(key); setShowGroupDD(false); }}
              style={{
                display: 'block', width: '100%', textAlign: 'left',
                padding: '8px 14px', background: 'none', border: 'none',
                color: groupBy === key ? ZB.blue : ZB.text,
                fontSize: 13, cursor: 'pointer',
              }}>
              {label}
            </button>
          ))}
        </div>
      );
    }

    // ─── EXPORT PANEL ─────────────────────────────────────────────────────
    function renderExportPanel() {
      return (
        <div className="et-col-dropdown" style={{ right: 0, left: 'auto' }}>
          <button onClick={exportCSV}
            style={{ display:'block', width:'100%', textAlign:'left', padding:'8px 14px',
              background:'none', border:'none', color: ZB.text, fontSize:13, cursor:'pointer' }}>
            Export as CSV
          </button>
          <button onClick={exportXLSX}
            style={{ display:'block', width:'100%', textAlign:'left', padding:'8px 14px',
              background:'none', border:'none', color: ZB.text, fontSize:13, cursor:'pointer' }}>
            Export as Excel (.xlsx)
          </button>
        </div>
      );
    }

    // ─── ADD PANEL ────────────────────────────────────────────────────────
    function renderAddPanel() {
      // Gather unique CSI divisions from current data
      const divOptions = [...new Set(data.map(d => d.csi_division).filter(Boolean))];

      const fieldStyle = {
        width: '100%', padding: '8px 10px', borderRadius: 4,
        background: ZB.input, border: `1px solid ${ZB.border}`,
        color: ZB.text, fontSize: 13, outline: 'none', boxSizing: 'border-box',
        fontFamily: 'IBM Plex Sans, sans-serif',
      };
      const labelStyle = { display: 'block', color: ZB.muted, fontSize: 11,
        fontWeight: 700, marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.04em' };

      return (
        <div className="et-add-panel" style={{
          position: 'fixed', top: 0, right: 0, width: 320, height: '100vh',
          background: ZB.card, borderLeft: `1px solid ${ZB.border}`,
          boxShadow: '-8px 0 24px rgba(0,0,0,0.4)',
          zIndex: 200, overflowY: 'auto', padding: 24,
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
            <span style={{ color: ZB.text, fontWeight: 700, fontSize: 15 }}>Add Line Item</span>
            <button onClick={() => setShowAddPanel(false)}
              style={{ background: 'none', border: 'none', color: ZB.muted, cursor: 'pointer', padding: 4 }}>
              <Icon name="x" size={18} color={ZB.muted} />
            </button>
          </div>

          <form onSubmit={submitAddItem}>
            {/* Description */}
            <div style={{ marginBottom: 14 }}>
              <label style={labelStyle}>Description *</label>
              <input style={fieldStyle} value={addForm.description} required
                onChange={e => setAddForm(p => ({ ...p, description: e.target.value }))} />
            </div>

            {/* CSI Division */}
            <div style={{ marginBottom: 14 }}>
              <label style={labelStyle}>CSI Division</label>
              <select style={fieldStyle} value={addForm.csi_division}
                onChange={e => setAddForm(p => ({ ...p, csi_division: e.target.value }))}>
                <option value="">— Select or leave blank —</option>
                {divOptions.map(d => <option key={d} value={d}>{d}</option>)}
                <option value="Other">Other</option>
              </select>
            </div>

            {/* Phase */}
            <div style={{ marginBottom: 14 }}>
              <label style={labelStyle}>Phase</label>
              <input style={fieldStyle} value={addForm.phase}
                onChange={e => setAddForm(p => ({ ...p, phase: e.target.value }))} />
            </div>

            {/* Qty + Unit */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 14 }}>
              <div>
                <label style={labelStyle}>Qty</label>
                <input type="number" step="any" style={{ ...fieldStyle, fontFamily: 'IBM Plex Mono, monospace' }}
                  value={addForm.qty}
                  onChange={e => setAddForm(p => ({ ...p, qty: e.target.value }))} />
              </div>
              <div>
                <label style={labelStyle}>Unit</label>
                <select style={fieldStyle} value={addForm.unit}
                  onChange={e => setAddForm(p => ({ ...p, unit: e.target.value }))}>
                  {UNIT_OPTIONS.map(u => <option key={u}>{u}</option>)}
                </select>
              </div>
            </div>

            {/* Labor/Unit + Mat/Unit */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 20 }}>
              <div>
                <label style={labelStyle}>Labor/Unit ($)</label>
                <input type="number" step="any" min="0"
                  style={{ ...fieldStyle, fontFamily: 'IBM Plex Mono, monospace' }}
                  value={addForm.labor_rate}
                  onChange={e => setAddForm(p => ({ ...p, labor_rate: e.target.value }))} />
              </div>
              <div>
                <label style={labelStyle}>Mat/Unit ($)</label>
                <input type="number" step="any" min="0"
                  style={{ ...fieldStyle, fontFamily: 'IBM Plex Mono, monospace' }}
                  value={addForm.mat_cost}
                  onChange={e => setAddForm(p => ({ ...p, mat_cost: e.target.value }))} />
              </div>
            </div>

            {/* Live total preview */}
            {(addForm.qty || addForm.labor_rate || addForm.mat_cost) && (
              <div style={{
                background: ZB.input, borderRadius: 4, padding: '8px 12px',
                marginBottom: 16, display: 'flex', justifyContent: 'space-between',
              }}>
                <span style={{ color: ZB.muted, fontSize: 12 }}>Preview total</span>
                <span className="et-mono" style={{ color: ZB.coral, fontSize: 13, fontWeight: 600 }}>
                  {fmt$((parseFloat(addForm.qty) || 0) *
                    ((parseFloat(addForm.labor_rate) || 0) + (parseFloat(addForm.mat_cost) || 0)))}
                </span>
              </div>
            )}

            <button type="submit" style={{
              width: '100%', padding: '10px', background: ZB.blue, color: '#fff',
              border: 'none', borderRadius: 4, fontWeight: 600, fontSize: 14, cursor: 'pointer',
            }}>
              Save Line Item
            </button>
          </form>
        </div>
      );
    }

    // ─── TOOLBAR ──────────────────────────────────────────────────────────
    function renderToolbar() {
      const hasGrouping = !!groupBy;
      const groupLabel  = groupBy ? COL_META[groupBy]?.label || groupBy : 'None';

      return (
        <div style={{
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          marginBottom: 10, gap: 8, flexWrap: 'wrap',
        }}>
          {/* Left side */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>

            {/* Search */}
            <div style={{ position: 'relative' }}>
              <Icon name="search" size={13} color={ZB.muted}
                style={{ position: 'absolute', left: 8, top: '50%', transform: 'translateY(-50%)' }} />
              <input
                value={globalFilter}
                onChange={e => setGlobalFilter(e.target.value)}
                placeholder="Search items…"
                style={{
                  paddingLeft: 28, paddingRight: globalFilter ? 28 : 10,
                  padding: '7px 28px 7px 28px',
                  background: ZB.input, border: `1px solid ${ZB.border}`,
                  borderRadius: 4, color: ZB.text, fontSize: 13, width: 200,
                  fontFamily: 'IBM Plex Sans, sans-serif', outline: 'none',
                }}
              />
              {globalFilter && (
                <button onClick={() => setGlobalFilter('')}
                  style={{
                    position: 'absolute', right: 6, top: '50%', transform: 'translateY(-50%)',
                    background: 'none', border: 'none', cursor: 'pointer', padding: 2,
                  }}>
                  <Icon name="x" size={12} color={ZB.muted} />
                </button>
              )}
            </div>

            {/* Group by */}
            <div style={{ position: 'relative' }}>
              <button onClick={() => { setShowGroupDD(!showGroupDD); setShowColPanel(false); setShowExportDD(false); }}
                style={toolbarBtnStyle}>
                <Icon name="group" size={13} color={ZB.muted} />
                Group: {groupLabel}
              </button>
              {showGroupDD && renderGroupPanel()}
            </div>

            {/* Expand/Collapse all (only when grouped) */}
            {hasGrouping && (
              <>
                <button onClick={() => setCollapsedGroups(new Set())}
                  style={toolbarBtnStyle}>
                  <Icon name="expand" size={13} color={ZB.muted} /> Expand All
                </button>
                <button
                  onClick={() => setCollapsedGroups(new Set(groupedSections.map(g => g.key)))}
                  style={toolbarBtnStyle}>
                  <Icon name="collapse" size={13} color={ZB.muted} /> Collapse All
                </button>
              </>
            )}

            {/* Selected rows badge */}
            {selectedCount > 0 && (
              <div style={{
                display: 'flex', alignItems: 'center', gap: 6,
                background: ZB.blue + '22', border: `1px solid ${ZB.blue}44`,
                borderRadius: 4, padding: '5px 10px',
              }}>
                <span style={{ color: ZB.blue, fontSize: 12 }}>{selectedCount} selected</span>
                <button onClick={() => setRowSelection({})}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}>
                  <Icon name="x" size={12} color={ZB.blue} />
                </button>
              </div>
            )}
          </div>

          {/* Right side */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>

            {/* Columns */}
            <div style={{ position: 'relative' }}>
              <button onClick={() => { setShowColPanel(!showColPanel); setShowGroupDD(false); setShowExportDD(false); }}
                style={toolbarBtnStyle}>
                <Icon name="columns" size={13} color={ZB.muted} /> Columns
              </button>
              {showColPanel && renderColumnPanel()}
            </div>

            {/* Export */}
            <div style={{ position: 'relative' }}>
              <button onClick={() => { setShowExportDD(!showExportDD); setShowColPanel(false); setShowGroupDD(false); }}
                style={toolbarBtnStyle}>
                <Icon name="download" size={13} color={ZB.muted} /> Export
              </button>
              {showExportDD && renderExportPanel()}
            </div>

            {/* Add Item */}
            <button onClick={() => setShowAddPanel(true)} style={{
              display: 'flex', alignItems: 'center', gap: 6,
              padding: '7px 14px', background: ZB.blue, color: '#fff',
              border: 'none', borderRadius: 4, cursor: 'pointer', fontSize: 13, fontWeight: 600,
            }}>
              <Icon name="plus" size={13} color="#fff" /> Add Item
            </button>
          </div>
        </div>
      );
    }

    const toolbarBtnStyle = {
      display: 'flex', alignItems: 'center', gap: 5,
      padding: '7px 12px', background: ZB.input, border: `1px solid ${ZB.border}`,
      color: ZB.muted, borderRadius: 4, cursor: 'pointer', fontSize: 12,
      fontFamily: 'IBM Plex Sans, sans-serif', whiteSpace: 'nowrap',
    };

    // ─── CLOSE DROPDOWNS ON OUTSIDE CLICK ────────────────────────────────
    useEffect(() => {
      function onOutsideClick(e) {
        if (!e.target.closest('.et-col-dropdown, .et-group-dropdown, [data-dd-anchor]')) {
          setShowColPanel(false);
          setShowGroupDD(false);
          setShowExportDD(false);
        }
      }
      document.addEventListener('mousedown', onOutsideClick);
      return () => document.removeEventListener('mousedown', onOutsideClick);
    }, []);

    // ─── RENDER ───────────────────────────────────────────────────────────
    return (
      <div style={{ fontFamily: 'IBM Plex Sans, sans-serif', position: 'relative' }}
        onClick={() => { setShowColPanel(false); setShowGroupDD(false); setShowExportDD(false); }}>

        {renderToolbar()}

        {/* Table */}
        <div className="et-scroll" style={{
          overflowX: 'auto', overflowY: 'auto',
          border: `1px solid ${ZB.border}`, borderRadius: '6px 6px 0 0',
          maxHeight: '65vh',
        }}>
          <table style={{
            width: '100%', borderCollapse: 'collapse',
            tableLayout: 'fixed',
            minWidth: columnOrder
              .filter(id => columnVisibility[id] !== false)
              .reduce((s, id) => s + (columnSizing[id] || COL_META[id]?.width || 100), 32) + 'px',
          }}>
            {renderHeader()}
            {renderBody()}
            {renderGrandTotal()}
          </table>
        </div>

        {/* Tally footer */}
        {renderTallyBanner()}

        {/* Add panel overlay */}
        {showAddPanel && (
          <>
            <div onClick={() => setShowAddPanel(false)} style={{
              position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', zIndex: 199,
            }} />
            {renderAddPanel()}
          </>
        )}
      </div>
    );
  }

  // ─── MOUNT ────────────────────────────────────────────────────────────────
  const rootEl = document.getElementById('estimate-root');
  if (rootEl) {
    const projectId   = rootEl.getAttribute('data-project-id');
    const projectName = rootEl.getAttribute('data-project-name') || 'Estimate';
    const root = ReactDOM.createRoot(rootEl);
    root.render(
      <EstimateTable
        projectId={parseInt(projectId, 10)}
        projectName={projectName}
      />
    );
  }
})();
