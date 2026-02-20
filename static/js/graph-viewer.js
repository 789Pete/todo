// static/js/graph-viewer.js
// Story 3.1: Uses sample data. Story 3.2 will replace with /api/graph/data/ fetch.

document.addEventListener('DOMContentLoaded', function () {
    const container = document.getElementById('network-graph');
    if (!container) return;  // Safety: container not present on this page

    try {
        // Sample data matching Story 3.2 API format
        const sampleNodes = [
            {
                id: 'task-1', label: 'Complete project\nproposal', group: 'todo', shape: 'box',
                color: { background: '#e3f2fd', border: '#2196f3' }, title: 'Priority: high'
            },
            {
                id: 'task-2', label: 'Review security\naudit', group: 'in_progress', shape: 'box',
                color: { background: '#fff8e1', border: '#ff9800' }, title: 'Priority: medium'
            },
            {
                id: 'task-3', label: 'Write tests', group: 'done', shape: 'box',
                color: { background: '#e8f5e9', border: '#4caf50' }, title: 'Priority: low'
            },
            {
                id: 'tag-1', label: 'Work', group: 'tag', shape: 'ellipse',
                color: { background: '#FF6B6B', border: '#d32f2f' }, title: '2 tasks'
            },
            {
                id: 'tag-2', label: 'Personal', group: 'tag', shape: 'ellipse',
                color: { background: '#4ECDC4', border: '#00897b' }, title: '1 task'
            },
        ];

        const sampleEdges = [
            { from: 'task-1', to: 'tag-1', color: '#999999', width: 1 },
            { from: 'task-2', to: 'tag-1', color: '#999999', width: 1 },
            { from: 'task-3', to: 'tag-2', color: '#999999', width: 1 },
        ];

        const data = {
            nodes: new vis.DataSet(sampleNodes),
            edges: new vis.DataSet(sampleEdges),
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
                // AC5: touch and mouse events — native to vis-network, enabled by default
                zoomView: true,
                dragView: true,
                dragNodes: true,
                tooltipDelay: 200,
                multiselect: false,
            },
            layout: { improvedLayout: true },
        };

        const network = new vis.Network(container, data, options);

        // AC4: Responsive canvas on window resize
        window.addEventListener('resize', function () {
            network.setSize('100%', container.offsetHeight + 'px');
            network.fit();
        });

        // AC6: Performance test helper — call window.testGraphPerformance() in console
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
                network.setData(data);  // Restore sample data
            });
        };

    } catch (e) {
        // AC7: Error fallback when vis-network fails
        console.error('Graph initialization failed:', e);
        container.innerHTML =
            '<div class="alert alert-danger m-3">' +
            'Failed to load the graph visualization. Please refresh the page.' +
            '</div>';
    }
});
