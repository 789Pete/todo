// static/js/graph-viewer.js
// Story 3.2: Fetches real graph data from /api/graph/data/

function loadGraphView() {
    if (typeof fetch === 'undefined' || typeof URLSearchParams === 'undefined') {
        var fb = document.getElementById('network-graph');
        if (fb) {
            fb.innerHTML = '<div class="alert alert-warning m-3">Your browser does not support the graph visualization. Please upgrade to a modern browser (Chrome 90+, Firefox 88+, Safari 14+).</div>';
        }
        return;
    }

    const container = document.getElementById('network-graph');
    if (!container) return;

    // Show loading state while fetch is in progress
    container.innerHTML =
        '<div class="d-flex justify-content-center align-items-center h-100">' +
        '<div class="spinner-border text-secondary" role="status">' +
        '<span class="visually-hidden">Loading graph...</span></div></div>';

    var graphParams = new URLSearchParams();
    var pageParams = new URLSearchParams(window.location.search);
    ['filter_tag', 'filter_status'].forEach(function (key) {
        var val = pageParams.get(key);
        if (val) graphParams.set(key, val);
    });
    // AC7: Persist filter state across sessions (only for the dedicated graph view)
    var persistFilters = !container.dataset.noFilters;
    if (graphParams.toString()) {
        if (persistFilters) {
            localStorage.setItem('graph_filters', graphParams.toString());
        }
    } else if (persistFilters) {
        var savedFilters = localStorage.getItem('graph_filters');
        if (savedFilters) {
            var restoredParams = new URLSearchParams(savedFilters);
            ['filter_tag', 'filter_status'].forEach(function (key) {
                var val = restoredParams.get(key);
                if (val) graphParams.set(key, val);
            });
        }
    }
    var apiUrl = '/api/graph/data/';
    if (graphParams.toString()) { apiUrl += '?' + graphParams.toString(); }

    fetch(apiUrl, {
        credentials: 'same-origin',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Accept': 'application/json',
        },
    })
        .then(function (response) {
            if (!response.ok) {
                throw new Error('API returned ' + response.status);
            }
            return response.json();
        })
        .then(function (graphData) {
            container.innerHTML = '';
            initializeGraph(container, graphData);
            if (graphData.stats && graphData.stats.truncated) {
                container.insertAdjacentHTML(
                    'afterend',
                    '<div class="alert alert-warning alert-sm mt-2 py-2 mb-0" role="alert">' +
                    'Showing the first 500 tasks. Apply a status or tag filter to see more detail.' +
                    '</div>'
                );
            }
        })
        .catch(function (e) {
            console.error('Graph data fetch failed:', e);
            container.innerHTML =
                '<div class="alert alert-danger m-3">' +
                'Failed to load the graph visualization (' + e.message + '). Please refresh the page.' +
                '</div>';
        });
}

document.addEventListener('DOMContentLoaded', loadGraphView);

// Reinitialize the graph when the page is restored from the browser's
// Back-Forward Cache (BFCache). The network was destroyed on pagehide, so the
// container is empty; loadGraphView() re-fetches and rebuilds it.
window.addEventListener('pageshow', function (e) {
    if (e.persisted) {
        loadGraphView();
    }
});

var LAYOUT_KEY = 'graph_layout_v1';

function saveLayout(network) {
    var positions = network.getPositions();
    try {
        localStorage.setItem(LAYOUT_KEY, JSON.stringify(positions));
    } catch (e) {
        // localStorage quota exceeded — silently ignore
    }
}

function loadLayout() {
    try {
        var raw = localStorage.getItem(LAYOUT_KEY);
        return raw ? JSON.parse(raw) : null;
    } catch (e) {
        return null;
    }
}

function clearLayout() {
    localStorage.removeItem(LAYOUT_KEY);
}

function resetLayout() {
    clearLayout();
    localStorage.removeItem('graph_filters');
    location.reload();
}

function initializeGraph(container, graphData) {
    try {
        var savedPositions = loadLayout();
        var rawNodes = graphData.nodes;
        if (savedPositions) {
            rawNodes = rawNodes.map(function (node) {
                if (savedPositions[node.id]) {
                    return Object.assign({}, node, {
                        x: savedPositions[node.id].x,
                        y: savedPositions[node.id].y,
                        physics: false,
                    });
                }
                return node;
            });
        }
        const data = {
            nodes: new vis.DataSet(rawNodes),
            edges: new vis.DataSet(graphData.edges),
        };

        const options = {
            nodes: { font: { size: 12 } },
            edges: {
                color: { color: '#999999' },
                smooth: { type: 'continuous' },
            },
            physics: {
                enabled: true,
                solver: 'barnesHut',
                barnesHut: { gravitationalConstant: -3000, springLength: 120, damping: 0.3 },
                stabilization: { iterations: 150, fit: true, updateInterval: 25 },
                adaptiveTimestep: true,
            },
            interaction: {
                zoomView: true,
                dragView: true,
                dragNodes: true,
                tooltipDelay: 200,
                multiselect: false,
                keyboard: {
                    enabled: true,
                    bindToWindow: false,
                    speed: { x: 10, y: 10, zoom: 0.02 },
                },
            },
            layout: { improvedLayout: true },
        };

        const network = new vis.Network(container, data, options);

        network.on('stabilized', function () {
            network.setOptions({ physics: false });
            saveLayout(network);
        });

        network.on('dragEnd', function () {
            saveLayout(network);
        });

        // AC1, AC2: Single-click navigation for task and tag nodes
        // AC3: Double-click relationship highlighting
        // clickTimeout prevents single-click navigation from firing during a double-click
        var clickTimeout = null;

        network.on('click', function (params) {
            if (params.nodes.length === 0) return;
            var nodeId = params.nodes[0];
            clickTimeout = setTimeout(function () {
                if (nodeId.indexOf('task-') === 0) {
                    window.location.href = '/tasks/' + nodeId.slice(5) + '/?from_graph=1';
                } else if (nodeId.indexOf('tag-') === 0) {
                    window.location.href = '/tasks/?tags=' + nodeId.slice(4);
                }
            }, 250);
        });

        network.on('doubleClick', function (params) {
            if (clickTimeout) { clearTimeout(clickTimeout); clickTimeout = null; }
            if (params.nodes.length === 0) return;
            var nodeId = params.nodes[0];
            var connectedNodes = network.getConnectedNodes(nodeId);
            var connectedEdges = network.getConnectedEdges(nodeId);
            network.selectNodes(connectedNodes);
            network.selectEdges(connectedEdges);
        });

        // AC4: Right-click context menu for task nodes
        var contextMenu = document.getElementById('graph-context-menu');
        var ctxView = document.getElementById('ctx-view');
        var ctxEdit = document.getElementById('ctx-edit');
        var ctxTags = document.getElementById('ctx-tags');
        var ctxDelete = document.getElementById('ctx-delete');

        function showContextMenu(clientX, clientY, nodeId) {
            if (!nodeId || nodeId.indexOf('task-') !== 0) return;
            var uuid = nodeId.slice(5);
            ctxView.href = '/tasks/' + uuid + '/?from_graph=1';
            ctxEdit.href = '/tasks/' + uuid + '/edit/';
            ctxTags.href = '/tasks/' + uuid + '/edit/';
            ctxDelete.href = '/tasks/' + uuid + '/delete/';
            // Clamp menu position within viewport
            var menuWidth = 160;
            var menuHeight = 120;
            var left = Math.min(clientX, window.innerWidth - menuWidth);
            var top = Math.min(clientY, window.innerHeight - menuHeight);
            contextMenu.style.left = left + 'px';
            contextMenu.style.top = top + 'px';
            contextMenu.style.display = 'block';
            document.addEventListener('click', function () {
                contextMenu.style.display = 'none';
            }, { once: true });
        }

        network.on('oncontext', function (params) {
            params.event.preventDefault();
            if (params.nodes.length === 0) return;
            showContextMenu(params.event.clientX, params.event.clientY, params.nodes[0]);
        });

        // AC3: Long-press on touch devices opens context menu (replaces right-click)
        var longPressTimer = null;
        var LONG_PRESS_MS = 500;

        container.addEventListener('touchstart', function (e) {
            if (e.touches.length !== 1) return;
            var touch = e.touches[0];
            var rect = container.getBoundingClientRect();
            var canvasX = touch.clientX - rect.left;
            var canvasY = touch.clientY - rect.top;
            var nodeId = network.getNodeAt({ x: canvasX, y: canvasY });
            if (!nodeId) return;
            longPressTimer = setTimeout(function () {
                showContextMenu(touch.clientX, touch.clientY, nodeId);
            }, LONG_PRESS_MS);
        }, { passive: true });

        container.addEventListener('touchend', function () {
            clearTimeout(longPressTimer);
        });

        container.addEventListener('touchmove', function () {
            clearTimeout(longPressTimer);
        });

        // AC5 (keyboard): Enter key opens the selected node
        container.addEventListener('keydown', function (e) {
            if (e.key === 'Enter') {
                var selected = network.getSelectedNodes();
                if (selected.length > 0) {
                    var nodeId = selected[0];
                    if (nodeId.indexOf('task-') === 0) {
                        window.location.href = '/tasks/' + nodeId.slice(5) + '/?from_graph=1';
                    } else if (nodeId.indexOf('tag-') === 0) {
                        window.location.href = '/tasks/?tags=' + nodeId.slice(4);
                    }
                }
            }
        });

        // AC5: Cluster task nodes by status when graph is dense (50+ nodes)
        var nodeCount = graphData.nodes.length;
        if (nodeCount > 50) {
            var groupConfig = {
                todo:        {label: 'To Do tasks',      color: {background: '#e3f2fd', border: '#2196f3'}},
                in_progress: {label: 'In Progress tasks', color: {background: '#fff8e1', border: '#ff9800'}},
                done:        {label: 'Done tasks',        color: {background: '#e8f5e9', border: '#4caf50'}},
            };
            Object.keys(groupConfig).forEach(function (group) {
                var cfg = groupConfig[group];
                network.cluster({
                    joinCondition: function (nodeOptions) {
                        return nodeOptions.group === group;
                    },
                    clusterNodeProperties: {
                        id: 'cluster-' + group,
                        label: cfg.label,
                        shape: 'box',
                        color: cfg.color,
                        borderWidth: 2,
                        font: {size: 14},
                    },
                });
            });
        }

        window.addEventListener('resize', function () {
            network.setSize('100%', container.offsetHeight + 'px');
            network.fit();
        });

        // Use pagehide (not beforeunload) so the page remains BFCache-eligible.
        // pagehide fires for both normal navigation and BFCache entry.
        window.addEventListener('pagehide', function () {
            network.destroy();
        });

        // Performance test helper — call window.testGraphPerformance() in console
        window.testGraphPerformance = function () {
            const perfNodes = [];
            const perfEdges = [];
            for (let i = 0; i < 110; i++) {
                perfNodes.push({ id: 'p-' + i, label: 'Node ' + i, shape: 'box' });
            }
            for (let j = 0; j < 210; j++) {
                perfEdges.push({ from: 'p-' + (j % 110), to: 'p-' + ((j + 1) % 110) });
            }
            const start = performance.now();
            network.setData({
                nodes: new vis.DataSet(perfNodes),
                edges: new vis.DataSet(perfEdges),
            });
            network.once('stabilized', function () {
                const elapsed = performance.now() - start;
                console.log(
                    'Performance: ' + perfNodes.length + ' nodes, ' +
                    perfEdges.length + ' edges stabilized in ' + elapsed.toFixed(0) + 'ms'
                );
                network.setData(data);
            });
        };
    } catch (e) {
        console.error('Graph initialization failed:', e);
        container.innerHTML =
            '<div class="alert alert-danger m-3">' +
            'Failed to initialize the graph (' + e.message + '). Please refresh the page.' +
            '</div>';
    }
}
