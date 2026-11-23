/**
 * AUTONOMOUSFORGE - Table Component
 * Responsive data tables with sorting, pagination, and selection
 */

const Table = {
    create({ columns, data = [], options = {} }) {
        const {
            striped = true,
            hoverable = true,
            bordered = false,
            compact = false,
            selectable = false,
            onRowClick,
            onSelectionChange,
            emptyMessage = 'No data available',
            loading = false,
            sortColumn,
            sortDirection = 'asc',
            pagination = null,
        } = options;

        const tableId = AF.utils.generateId();
        const selectedRows = new Set();

        // Sort data if column specified
        let sortedData = [...data];
        if (sortColumn) {
            sortedData.sort((a, b) => {
                const aVal = a[sortColumn];
                const bVal = b[sortColumn];
                if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
                if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
                return 0;
            });
        }

        const handleSort = (column) => {
            if (column.sortable) {
                const newDirection = sortColumn === column.key && sortDirection === 'asc' ? 'desc' : 'asc';
                // Re-render with new sort
                tableEl.dispatchEvent(new CustomEvent('table:sort', {
                    detail: { column: column.key, direction: newDirection },
                }));
            }
        };

        const handleSelectAll = (e) => {
            const checked = e.target.checked;
            selectedRows.clear();
            if (checked) {
                sortedData.forEach(row => selectedRows.add(row.id || JSON.stringify(row)));
            }
            updateSelection();
            onSelectionChange?.([...selectedRows]);
        };

        const handleSelectRow = (rowId, checked) => {
            if (checked) selectedRows.add(rowId);
            else selectedRows.delete(rowId);
            updateSelection();
            onSelectionChange?.([...selectedRows]);
        };

        const updateSelection = () => {
            const checkboxes = tableEl.querySelectorAll('tbody input[type="checkbox"][data-row-id]');
            checkboxes.forEach(cb => {
                cb.checked = selectedRows.has(cb.dataset.rowId);
            });
            const selectAllCb = tableEl.querySelector('thead input[type="checkbox"]');
            if (selectAllCb) {
                selectAllCb.checked = sortedData.length > 0 && selectedRows.size === sortedData.length;
                selectAllCb.indeterminate = selectedRows.size > 0 && selectedRows.size < sortedData.length;
            }
        };

        const tableEl = AF.utils.create('div', { class: 'table-container overflow-x-auto' }, [
            AF.utils.create('table', { class: 'table w-full', id: tableId }, [
                // Header
                AF.utils.create('thead', { class: 'bg-forge-900/50' }, [
                    AF.utils.create('tr', {}, [
                        selectable && AF.utils.create('th', { class: 'px-4 py-3 text-left', style: 'width: 48px' }, [
                            AF.utils.create('input', {
                                type: 'checkbox',
                                class: 'w-4 h-4 rounded border-border bg-forge-800 text-accent-500 focus:ring-accent-500',
                                onchange: handleSelectAll,
                                'aria-label': 'Select all rows',
                            }),
                        ]),
                        ...columns.map(col => AF.utils.create('th', {
                            class: `px-4 py-3 text-left text-xs font-semibold text-forge-400 uppercase tracking-wider ${col.sortable ? 'cursor-pointer select-none hover:text-forge-50' : ''}`,
                            style: col.width ? `width: ${col.width}` : undefined,
                            onclick: () => handleSort(col),
                        }, [
                            AF.utils.create('div', { class: 'flex items-center gap-1' }, [
                                col.label,
                                col.sortable && AF.utils.create('svg', {
                                    class: `w-4 h-4 ${sortColumn === col.key ? 'text-accent-500' : 'text-forge-600'}`,
                                    fill: 'none',
                                    stroke: 'currentColor',
                                    viewBox: '0 0 24 24',
                                }, [
                                    AF.utils.create('path', {
                                        'stroke-linecap': 'round',
                                        'stroke-linejoin': 'round',
                                        'stroke-width': '2',
                                        d: sortColumn === col.key && sortDirection === 'asc'
                                            ? 'M5 15l7-7 7 7'
                                            : sortColumn === col.key && sortDirection === 'desc'
                                            ? 'M19 9l-7 7-7-7'
                                            : 'M7 16V4m0 0L3 8m4-4l4 4M17 8v12m0 0l4-4m-4 4l-4-4',
                                    }),
                                ]),
                            ]),
                        ])),
                    ]),
                ]),
                // Body
                AF.utils.create('tbody', { class: 'divide-y divide-forge-800' }, [
                    loading ? AF.utils.create('tr', {}, [
                        AF.utils.create('td', {
                            colSpan: columns.length + (selectable ? 1 : 0),
                            class: 'px-4 py-12 text-center text-forge-500'
                        }, [
                            AF.utils.create('div', { class: 'flex flex-col items-center gap-3' }, [
                                AF.utils.create('div', { class: 'spinner spinner-lg' }),
                                'Loading...',
                            ]),
                        ]),
                    ]) : sortedData.length === 0 ? AF.utils.create('tr', {}, [
                        AF.utils.create('td', {
                            colSpan: columns.length + (selectable ? 1 : 0),
                            class: 'px-4 py-12 text-center text-forge-500'
                        }, emptyMessage),
                    ]) : sortedData.map(row => {
                        const rowId = row.id || JSON.stringify(row);
                        const isSelected = selectedRows.has(rowId);

                        return AF.utils.create('tr', {
                            class: `${striped ? (sortedData.indexOf(row) % 2 === 0 ? 'bg-forge-900/30' : '') : ''} ${hoverable ? 'hover:bg-forge-800/50' : ''} ${compact ? '' : ''} ${isSelected ? 'bg-accent-500/10' : ''} ${onRowClick ? 'cursor-pointer' : ''}`,
                            onclick: onRowClick ? (e) => { if (!e.target.closest('button, a, input, select')) onRowClick(e, row); } : undefined,
                            'data-row-id': rowId,
                        }, [
                            selectable && AF.utils.create('td', { class: 'px-4 py-3' }, [
                                AF.utils.create('input', {
                                    type: 'checkbox',
                                    class: 'w-4 h-4 rounded border-border bg-forge-800 text-accent-500 focus:ring-accent-500',
                                    checked: isSelected,
                                    onchange: (e) => handleSelectRow(rowId, e.target.checked),
                                    'data-row-id': rowId,
                                    'aria-label': 'Select row',
                                }),
                            ]),
                            ...columns.map(col => {
                                let cellContent = row[col.key];

                                if (col.render) {
                                    cellContent = col.render(cellContent, row);
                                } else if (cellContent === null || cellContent === undefined) {
                                    cellContent = AF.utils.create('span', { class: 'text-forge-600' }, '—');
                                } else if (typeof cellContent === 'boolean') {
                                    cellContent = AF.utils.create('span', { class: cellContent ? 'text-success' : 'text-danger' }, cellContent ? 'Yes' : 'No');
                                } else if (cellContent instanceof Date) {
                                    cellContent = AF.utils.formatDate(cellContent);
                                } else if (typeof cellContent === 'object' && cellContent !== null && cellContent.render) {
                                    cellContent = cellContent.render();
                                }

                                return AF.utils.create('td', {
                                    class: `px-4 py-3 ${col.className || ''}`,
                                    style: col.width ? `width: ${col.width}` : undefined,
                                }, typeof cellContent === 'string' ? cellContent : cellContent);
                            }),
                        ]);
                    }),
                ]),
            ]),
            // Pagination
            pagination && AF.utils.create('div', { class: 'flex items-center justify-between px-4 py-3 border-t border-forge-800' }, [
                AF.utils.create('div', { class: 'text-sm text-forge-400' }, [
                    `Showing ${(pagination.page - 1) * pagination.pageSize + 1} to ${Math.min(pagination.page * pagination.pageSize, pagination.total)} of ${pagination.total} results`,
                ]),
                AF.utils.create('div', { class: 'flex items-center gap-2' }, [
                    AF.utils.create('button', {
                        class: 'btn btn-ghost btn-sm',
                        disabled: pagination.page === 1,
                        onclick: () => tableEl.dispatchEvent(new CustomEvent('table:page', { detail: { page: pagination.page - 1 } })),
                    }, [
                        AF.utils.create('svg', { class: 'w-4 h-4', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
                            AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M15 19l-7-7 7-7' }),
                        ]),
                    ]),
                    AF.utils.create('button', {
                        class: 'btn btn-ghost btn-sm',
                        disabled: pagination.page * pagination.pageSize >= pagination.total,
                        onclick: () => tableEl.dispatchEvent(new CustomEvent('table:page', { detail: { page: pagination.page + 1 } })),
                    }, [
                        AF.utils.create('svg', { class: 'w-4 h-4', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
                            AF.utils.create('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M9 5l7 7-7 7' }),
                        ]),
                    ]),
                ]),
            ]),
        ]);

        // Store reference for external updates
        tableEl._tableData = { selectedRows, sortedData };
        tableEl.updateData = (newData) => {
            data = newData;
            sortedData = [...data];
            if (sortColumn) {
                sortedData.sort((a, b) => {
                    const aVal = a[sortColumn];
                    const bVal = b[sortColumn];
                    if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
                    if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
                    return 0;
                });
            }
            const tbody = tableEl.querySelector('tbody');
            if (tbody) {
                tbody.innerHTML = '';
                if (loading) {
                    tbody.appendChild(AF.utils.create('tr', {}, [
                        AF.utils.create('td', {
                            colSpan: columns.length + (selectable ? 1 : 0),
                            class: 'px-4 py-12 text-center text-forge-500'
                        }, [
                            AF.utils.create('div', { class: 'flex flex-col items-center gap-3' }, [
                                AF.utils.create('div', { class: 'spinner spinner-lg' }),
                                'Loading...',
                            ]),
                        ]),
                    ]));
                } else if (sortedData.length === 0) {
                    tbody.appendChild(AF.utils.create('tr', {}, [
                        AF.utils.create('td', {
                            colSpan: columns.length + (selectable ? 1 : 0),
                            class: 'px-4 py-12 text-center text-forge-500'
                        }, emptyMessage),
                    ]));
                } else {
                    sortedData.forEach(row => {
                        const rowId = row.id || JSON.stringify(row);
                        const isSelected = selectedRows.has(rowId);
                        tbody.appendChild(AF.utils.create('tr', {
                            class: `${striped ? (sortedData.indexOf(row) % 2 === 0 ? 'bg-forge-900/30' : '') : ''} ${hoverable ? 'hover:bg-forge-800/50' : ''} ${isSelected ? 'bg-accent-500/10' : ''} ${onRowClick ? 'cursor-pointer' : ''}`,
                            onclick: onRowClick ? (e) => { if (!e.target.closest('button, a, input, select')) onRowClick(e, row); } : undefined,
                            'data-row-id': rowId,
                        }, [
                            selectable && AF.utils.create('td', { class: 'px-4 py-3' }, [
                                AF.utils.create('input', {
                                    type: 'checkbox',
                                    class: 'w-4 h-4 rounded border-border bg-forge-800 text-accent-500 focus:ring-accent-500',
                                    checked: isSelected,
                                    onchange: (e) => handleSelectRow(rowId, e.target.checked),
                                    'data-row-id': rowId,
                                }),
                            ]),
                            ...columns.map(col => {
                                let cellContent = row[col.key];
                                if (col.render) cellContent = col.render(cellContent, row);
                                else if (cellContent === null || cellContent === undefined) cellContent = '—';
                                else if (typeof cellContent === 'boolean') cellContent = cellContent ? 'Yes' : 'No';
                                else if (cellContent instanceof Date) cellContent = AF.utils.formatDate(cellContent);
                                return AF.utils.create('td', { class: `px-4 py-3 ${col.className || ''}` }, cellContent);
                            }),
                        ]));
                    });
                }
            }
        };

        tableEl.getSelectedRows = () => [...selectedRows];

        return tableEl;
    },
};

export default Table;