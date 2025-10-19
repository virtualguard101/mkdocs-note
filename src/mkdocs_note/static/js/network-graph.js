/**
 * Network Graph Visualization using D3.js
 * 
 * This script provides interactive network graph visualization for MkDocs Note plugin.
 * It creates an interactive graph showing relationships between notes.
 */

(function() {
    'use strict';

    // Global configuration
    const CONFIG = {
        width: 800,
        height: 600,
        nodeRadius: 8,
        linkDistance: 100,
        chargeStrength: -300,
        colors: {
            note: '#1976d2',
            asset: '#757575',
            index: '#ff5722',
            hover: '#1565c0',
            current: '#ff5722'
        }
    };

    /**
     * Initialize network graph
     * @param {string} containerId - ID of the container element
     * @param {Object} graphData - Graph data with nodes and links
     */
    function initializeNetworkGraph(containerId, graphData) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error('Network graph container not found:', containerId);
            return;
        }

        // Create SVG element
        const svg = d3.select(container).select('#graph-svg')
            .attr('width', CONFIG.width)
            .attr('height', CONFIG.height);

        // Clear any existing content
        svg.selectAll('*').remove();

        // Create main group for zoom/pan
        const g = svg.append('g');

        // Set up zoom behavior
        const zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .on('zoom', function(event) {
                g.attr('transform', event.transform);
            });

        svg.call(zoom);

        // Create force simulation
        const simulation = d3.forceSimulation(graphData.nodes)
            .force('link', d3.forceLink(graphData.links).id(d => d.id).distance(CONFIG.linkDistance))
            .force('charge', d3.forceManyBody().strength(CONFIG.chargeStrength))
            .force('center', d3.forceCenter(CONFIG.width / 2, CONFIG.height / 2))
            .force('collision', d3.forceCollide().radius(CONFIG.nodeRadius + 5));

        // Create links
        const link = g.append('g')
            .attr('class', 'links')
            .selectAll('line')
            .data(graphData.links)
            .enter().append('line')
            .attr('stroke', '#999')
            .attr('stroke-opacity', 0.6)
            .attr('stroke-width', d => Math.sqrt(d.weight) * 2);

        // Create nodes
        const node = g.append('g')
            .attr('class', 'nodes')
            .selectAll('circle')
            .data(graphData.nodes)
            .enter().append('circle')
            .attr('r', d => CONFIG.nodeRadius + (d.size - 1) * 2)
            .attr('fill', d => CONFIG.colors[d.node_type] || CONFIG.colors.note)
            .attr('stroke', '#fff')
            .attr('stroke-width', 2)
            .style('cursor', 'pointer')
            .call(d3.drag()
                .on('start', dragstarted)
                .on('drag', dragged)
                .on('end', dragended));

        // Add labels
        const label = g.append('g')
            .attr('class', 'labels')
            .selectAll('text')
            .data(graphData.nodes)
            .enter().append('text')
            .text(d => d.label)
            .attr('font-size', '12px')
            .attr('font-family', 'Arial, sans-serif')
            .attr('text-anchor', 'middle')
            .attr('dy', '.35em')
            .style('pointer-events', 'none')
            .style('user-select', 'none');

        // Add tooltips
        const tooltip = d3.select('body').append('div')
            .attr('class', 'graph-tooltip')
            .style('opacity', 0)
            .style('position', 'absolute')
            .style('background', 'rgba(0, 0, 0, 0.8)')
            .style('color', 'white')
            .style('padding', '8px')
            .style('border-radius', '4px')
            .style('font-size', '12px')
            .style('pointer-events', 'none')
            .style('z-index', '1000');

        // Add event listeners
        node
            .on('mouseover', function(event, d) {
                // Highlight connected nodes
                const connectedNodes = new Set();
                graphData.links.forEach(link => {
                    if (link.source.id === d.id) connectedNodes.add(link.target.id);
                    if (link.target.id === d.id) connectedNodes.add(link.source.id);
                });

                node.style('opacity', n => 
                    n.id === d.id || connectedNodes.has(n.id) ? 1 : 0.3);
                link.style('opacity', l => 
                    l.source.id === d.id || l.target.id === d.id ? 1 : 0.1);

                // Show tooltip
                tooltip.transition().duration(200).style('opacity', .9);
                tooltip.html(`
                    <strong>${d.label}</strong><br/>
                    Type: ${d.node_type}<br/>
                    URL: ${d.url}<br/>
                    ${d.metadata ? Object.entries(d.metadata).map(([k, v]) => `${k}: ${v}`).join('<br/>') : ''}
                `)
                .style('left', (event.pageX + 10) + 'px')
                .style('top', (event.pageY - 28) + 'px');
            })
            .on('mouseout', function() {
                // Reset opacity
                node.style('opacity', 1);
                link.style('opacity', 0.6);

                // Hide tooltip
                tooltip.transition().duration(500).style('opacity', 0);
            })
            .on('click', function(event, d) {
                // Navigate to the note
                if (d.url && d.url !== '#') {
                    window.location.href = d.url;
                }
            });

        // Update positions on simulation tick
        simulation.on('tick', function() {
            link
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);

            node
                .attr('cx', d => d.x)
                .attr('cy', d => d.y);

            label
                .attr('x', d => d.x)
                .attr('y', d => d.y);
        });

        // Add control buttons
        setupControls(containerId, svg, zoom, simulation);

        // Drag functions
        function dragstarted(event, d) {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }

        function dragged(event, d) {
            d.fx = event.x;
            d.fy = event.y;
        }

        function dragended(event, d) {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }
    }

    /**
     * Setup control buttons
     * @param {string} containerId - Container ID
     * @param {Object} svg - SVG element
     * @param {Object} zoom - Zoom behavior
     * @param {Object} simulation - Force simulation
     */
    function setupControls(containerId, svg, zoom, simulation) {
        const container = document.getElementById(containerId);
        
        // Reset zoom button
        const resetButton = container.querySelector('#reset-zoom');
        if (resetButton) {
            resetButton.addEventListener('click', function() {
                svg.transition().duration(750).call(
                    zoom.transform,
                    d3.zoomIdentity
                );
            });
        }

        // Toggle labels button
        const toggleButton = container.querySelector('#toggle-labels');
        if (toggleButton) {
            let labelsVisible = true;
            toggleButton.addEventListener('click', function() {
                labelsVisible = !labelsVisible;
                const labels = svg.selectAll('.labels text');
                labels.style('opacity', labelsVisible ? 1 : 0);
                toggleButton.textContent = labelsVisible ? 'Hide Labels' : 'Show Labels';
            });
        }
    }

    // Make function globally available
    window.initializeNetworkGraph = initializeNetworkGraph;

    // Auto-initialize if D3.js is available
    if (typeof d3 !== 'undefined') {
        console.log('Network Graph: D3.js detected, ready for initialization');
    } else {
        console.warn('Network Graph: D3.js not found. Please include D3.js library.');
    }

})();
