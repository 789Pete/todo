// static/js/graph-viewer.js
// Story 3.2: Fetches real graph data from /api/graph/data/

document.addEventListener('DOMContentLoaded', function () {
    const container = document.getElementById('network-graph');
    if (!container) return;

    // Show loading state while fetch is in progress
    container.innerHTML =
        '<div class="d-flex justify-content-center align-items-center h-100">' +
        '<div class="spinner-border text-secondary" role="status">' +
        '<span class="visually-hidden">Loading graph...</span></div></div>';

    fetch('/api/graph/data/', {
        credentials: 'same-origin',
        headers: { 'X-CSRFToken': getCookie('csrftoken') },
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
        })
        .catch(function (e) {
            console.error('Graph data fetch failed:', e);
            container.innerHTML =
                '<div class="alert alert-danger m-3">' +
                'Failed to load the graph visualization. Please refresh the page.' +
                '</div>';
        });
});

function initializeGraph(container, graphData) {
    try {
        const data = {
            nodes: new vis.DataSet(graphData.nodes),
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
                stabilization: { iterations: 100, fit: true },
            },
            interaction: {
                zoomView: true,
                dragView: true,
                dragNodes: true,
                tooltipDelay: 200,
                multiselect: false,
            },
            layout: { improvedLayout: true },
        };

        const network = new vis.Network(container, data, options);

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
            'Failed to load the graph visualization. Please refresh the page.' +
            '</div>';
    }
}
