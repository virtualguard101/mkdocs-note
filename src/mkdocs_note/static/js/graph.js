document$.subscribe(function() {
    const graphContainer = document.getElementById("graph");
    if (!graphContainer) {
        const sidebar = document.querySelector('[data-md-component="sidebar"][data-md-type="toc"] .md-sidebar__inner');
        if (sidebar) {
            const newGraphContainer = document.createElement("nav");
            newGraphContainer.id = "graph";
            newGraphContainer.className = "graph md-nav md-nav--graph";
            sidebar.appendChild(newGraphContainer);
        }
    }

    const graphOptions = window.graph_options || {};

    const VIEWBOX_SIZE = 24;

    const ICONS = {
        fullscreen: '<path d="M7,2H2v5l1.8-1.8L6.5,8L8,6.5L5.2,3.8L7,2z M13,2l1.8,1.8L12,6.5L13.5,8l2.7-2.7L18,7V2H13z M13.5,12L12,13.5l2.7,2.7L13,18h5v-5l-1.8,1.8L13.5,12z M6.5,12l-2.7,2.7L2,13v5h5l-1.8-1.8L8,13.5L6.5,12z"/>',
        fullscreen_exit: '<path d="M5 16h3v3h2v-5H5v2zm3-8H5v2h5V5H8v3zm6 11h2v-3h3v-2h-5v5zm2-11V5h-2v5h5V8h-3z"></path>',
        close: '<path d="M19 6.41 17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12 19 6.41z"></path>',
        whole_network: '<circle cx="12" cy="5" r="3"></circle><circle cx="5" cy="12" r="3"></circle><circle cx="19" cy="12" r="3"></circle><circle cx="12" cy="19" r="3"></circle><line x1="12" y1="8" x2="12" y2="16"></line><line x1="8" y1="12" x2="16" y2="12"></line><line x1="7" y1="10" x2="10" y2="7"></line><line x1="14" y1="7" x2="17" y2="10"></line><line x1="17" y1="14" x2="14" y2="17"></line><line x1="10" y1="17" x2="7" y2="14"></line>',
        next_neighbors: '<circle cx="12" cy="12" r="3"></circle><circle cx="12" cy="3" r="2"></circle><circle cx="21" cy="12" r="2"></circle><circle cx="12" cy="21" r="2"></circle><circle cx="3" cy="12" r="2"></circle><line x1="12" y1="9" x2="12" y2="5"></line><line x1="15" y1="12" x2="19" y2="12"></line><line x1="12" y1="15" x2="12" y2="19"></line><line x1="9" y1="12" x2="5" y2="12"></line>',
        graph: '<path d="M171,100 C171,106.075 166.075,111 160,111 C154.016,111 149.158,106.219 149.014,100.27 L114.105,83.503 C111.564,86.693 108.179,89.18 104.282,90.616 L108.698,124.651 C112.951,126.172 116,130.225 116,135 C116,141.075 111.075,146 105,146 C98.925,146 94,141.075 94,135 C94,131.233 95.896,127.912 98.781,125.93 L94.364,91.896 C82.94,90.82 74,81.206 74,69.5 C74,69.479 74.001,69.46 74.001,69.439 L53.719,64.759 C50.642,70.269 44.76,74 38,74 C36.07,74 34.215,73.689 32.472,73.127 L20.624,90.679 C21.499,92.256 22,94.068 22,96 C22,102.075 17.075,107 11,107 C4.925,107 0,102.075 0,96 C0,89.925 4.925,85 11,85 C11.452,85 11.895,85.035 12.332,85.089 L24.184,67.531 C21.574,64.407 20,60.389 20,56 C20,48.496 24.594,42.07 31.121,39.368 L29.111,21.279 C24.958,19.707 22,15.704 22,11 C22,4.925 26.925,0 33,0 C39.075,0 44,4.925 44,11 C44,14.838 42.031,18.214 39.051,20.182 L41.061,38.279 C49.223,39.681 55.49,46.564 55.95,55.011 L76.245,59.694 C79.889,52.181 87.589,47 96.5,47 C100.902,47 105.006,48.269 108.475,50.455 L131.538,27.391 C131.192,26.322 131,25.184 131,24 C131,17.925 135.925,13 142,13 C148.075,13 153,17.925 153,24 C153,30.075 148.075,35 142,35 C140.816,35 139.678,34.808 138.609,34.461 L115.546,57.525 C117.73,60.994 119,65.098 119,69.5 C119,71.216 118.802,72.884 118.438,74.49 L153.345,91.257 C155.193,89.847 157.495,89 160,89 C166.075,89 171,93.925 171,100"></path>',
    }

    class Icon {
        constructor(name) {
            this.name = name;
            this.viewBox = `0 0 ${VIEWBOX_SIZE} ${VIEWBOX_SIZE}`;
        }

        toSvg() {
            const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            svg.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
            svg.setAttribute('viewBox', this.viewBox);
            svg.classList.add('icon');
            svg.innerHTML = ICONS[this.name];
            return svg;
        }
    }

    const header = document.querySelector(".md-header__inner");
    if (header && !document.getElementById("graph_button")) {
        const search = document.querySelector(".md-search");
        const graphButton = document.createElement("label");
        graphButton.id = "graph_button";
        graphButton.className = "md-header__button md-icon";
        graphButton.onclick = () => open_modal_graph('full');
        graphButton.title = "Open graph";

        const graphIcon = new Icon('graph');
        graphIcon.viewBox = '0 0 171 146';
        const graphButtonSvg = graphIcon.toSvg();
        graphButton.appendChild(graphButtonSvg);

        if (search) {
            header.insertBefore(graphButton, search);
        } else {
            header.appendChild(graphButton);
        }
    }

    const DEFAULT_GRAPH_HEIGHT = 300;

    const ARROWHEAD = {
        VIEW_BOX: "-0 -5 10 10",
        REFX: 0,
        REFY: 0,
        MARKER_WIDTH: 8,
        MARKER_HEIGHT: 8,
        D: "M 0,-5 L 10,0 L 0,5",
    }

    const FORCE_CONFIG = {
        LINK_DISTANCE: 60,
        CHARGE_STRENGTH: -300,
        X_STRENGTH: 0.1,
        Y_STRENGTH: 0.1,
    }

    const NODE_CONFIG = {
        CIRCLE_RADIUS: 5,
        LABEL_X_OFFSET: 7,
        LABEL_DY_OFFSET: ".35em",
        CURRENT_NODE_MULTIPLIER: 1.5,
    }

    const LINK_CONFIG = {
        STROKE_MARGIN: 1
    }

    const SIMULATION_CONFIG = {
        ALPHA_TARGET_ACTIVE: 0.3,
        ALPHA_TARGET_INACTIVE: 0,
    }

    let currentGraph = null;
    let fullGraphData = null;

    function filterGraph(nodes, edges, startNodeId, hops) {
        if (graphOptions.debug) console.log(`Filtering graph with startNodeId: ${startNodeId} and hops: ${hops}`);
       if (hops === 'full' || !startNodeId) {
           return { nodes, edges };
       }

       const numericHops = parseInt(hops, 10);
       const adjacentNodes = new Set();
       const adjacentEdges = new Set();
       const queue = [{ nodeId: startNodeId, depth: 0 }];
       const visited = new Set([startNodeId]);

       const startNode = nodes.find(n => n.id === startNodeId)
       if(startNode) adjacentNodes.add(startNode);

       while (queue.length > 0) {
           const { nodeId, depth } = queue.shift();

           if (depth >= numericHops) continue;

           edges.forEach(edge => {
               const sourceId = edge.source.id || edge.source;
               const targetId = edge.target.id || edge.target;

               if (sourceId === nodeId || targetId === nodeId) {
                   const neighborId = sourceId === nodeId ? targetId : sourceId;
                   if (!visited.has(neighborId)) {
                       visited.add(neighborId);
                       const neighborNode = nodes.find(n => n.id === neighborId);
                       if (neighborNode) {
                           adjacentNodes.add(neighborNode);
                           queue.push({ nodeId: neighborId, depth: depth + 1 });
                       }
                   }
                   adjacentEdges.add(edge);
               }
           });
       }

        if (graphOptions.debug) console.log(`Filtered graph to ${adjacentNodes.size} nodes and ${adjacentEdges.size} edges`);
       return {
           nodes: Array.from(adjacentNodes),
           edges: Array.from(adjacentEdges)
       };
    }

    function open_modal_graph(hops) {
        if (graphOptions.debug) console.log("Opening modal graph");
        destroy_graph();
        const modalBackground = document.createElement('div');
        modalBackground.id = 'modal_background';

        const modalGraph = document.createElement('div');
        modalGraph.className = 'modal_graph';
        modalGraph.id = 'modal_graph_content';

        modalBackground.appendChild(modalGraph);
        document.body.appendChild(modalBackground);

        modalBackground.addEventListener('click', function(e) {
            if (e.target === modalBackground) {
                close_modal_graph();
            }
        });

        draw_graph('#modal_graph_content', hops);
    }

    function close_modal_graph() {
        if (graphOptions.debug) console.log("Closing modal graph");
        const modalBackground = document.getElementById('modal_background');
        if (modalBackground) {
            destroy_graph();
            modalBackground.remove();
            draw_graph('#graph');
        }
    }

    function draw_graph(container, hops) {
        if (graphOptions.debug) console.log(`Drawing graph in container: ${container} with hops: ${hops}`);
        const containerElement = document.querySelector(container);
        if (!containerElement) return;

        containerElement.innerHTML = '';
        const isModal = container === '#modal_graph_content';
        if (graphOptions.debug) console.log(`Is modal: ${isModal}`);

        if (!isModal) {
            const graphTitle = document.createElement('label');
            graphTitle.textContent = 'Connected Pages';
            graphTitle.className = 'md-nav__title';
            containerElement.appendChild(graphTitle);
        }

        const graphHeader = document.createElement('div');
        graphHeader.className = 'graph-header';
        containerElement.appendChild(graphHeader);

       if (isModal) {
           const depthSelectorContainer = document.createElement('div');
           depthSelectorContainer.className = 'hop-selector-container';

            const neighborsButton = document.createElement('button');
            neighborsButton.className = 'md-button';
            neighborsButton.title = 'Show next neighbors';
            neighborsButton.appendChild(new Icon('next_neighbors').toSvg());
            const neighborsButtonText = document.createElement('span');
            neighborsButtonText.textContent = 'Neighbors';
            neighborsButton.appendChild(neighborsButtonText);
            neighborsButton.onclick = () => {
                destroy_graph();
                draw_graph(container, '1');
            };
            depthSelectorContainer.appendChild(neighborsButton);

            const fullGraphButton = document.createElement('button');
            fullGraphButton.className = 'md-button';
            fullGraphButton.title = 'Show full graph';
            fullGraphButton.appendChild(new Icon('whole_network').toSvg());
            const fullGraphButtonText = document.createElement('span');
            fullGraphButtonText.textContent = 'Full';
            fullGraphButton.appendChild(fullGraphButtonText);
            fullGraphButton.onclick = () => {
                destroy_graph();
                draw_graph(container, 'full');
            };
            depthSelectorContainer.appendChild(fullGraphButton);

           graphHeader.appendChild(depthSelectorContainer);
       }

        if (isModal) {
            const closeButton = document.createElement('button');
            closeButton.className = 'md-button md-button--icon';
            closeButton.id = 'close-graph-modal-button';
            closeButton.title = "Close";
            closeButton.appendChild(new Icon('close').toSvg());
            closeButton.onclick = close_modal_graph;
            graphHeader.appendChild(closeButton);
        } else {
            const openModalButton = document.createElement("button");
            openModalButton.className = 'md-button md-button--icon';
            openModalButton.id = "open-graph-modal-button";
            openModalButton.title = "Open graph in modal";
            openModalButton.appendChild(new Icon('fullscreen').toSvg());
            openModalButton.onclick = () => open_modal_graph('1');
            graphHeader.appendChild(openModalButton);
        }

         const width = containerElement.clientWidth;
         const height = isModal ? containerElement.clientHeight : DEFAULT_GRAPH_HEIGHT;

         if (!isModal) {
            containerElement.style.height = height + "px";
         }

         const svg = d3.select(container).append("svg")
             .attr("width", width)
             .attr("height", height)
             .call(d3.zoom().on("zoom", function (event) {
                 g.attr("transform", event.transform);
             }));

 		const g = svg.append("g");

 		     const defs = svg.append("defs");

 		     defs.append("marker")
 		         .attr("id", "arrowhead")
 		         .attr("class", "arrowhead")
 		         .attr("viewBox", ARROWHEAD.VIEW_BOX)
 		         .attr("refX", ARROWHEAD.REFX)
 		         .attr("refY", ARROWHEAD.REFY)
 		         .attr("orient", "auto")
 		         .attr("markerWidth", ARROWHEAD.MARKER_WIDTH)
 		         .attr("markerHeight", ARROWHEAD.MARKER_HEIGHT)
 		         .attr("xoverflow", "visible")
 		         .append("svg:path")
 		         .attr("d", ARROWHEAD.D)
 		         .style("stroke", "none");

 		     defs.append("marker")
 		         .attr("id", "arrowhead-start")
 		         .attr("class", "arrowhead")
 		         .attr("viewBox", ARROWHEAD.VIEW_BOX)
 		         .attr("refX", ARROWHEAD.REFX)
 		         .attr("refY", ARROWHEAD.REFY)
 		         .attr("orient", "auto-start-reverse")
 		         .attr("markerWidth", ARROWHEAD.MARKER_WIDTH)
 		         .attr("markerHeight", ARROWHEAD.MARKER_HEIGHT)
 		         .attr("xoverflow", "visible")
 		         .append("svg:path")
 		         .attr("d", ARROWHEAD.D)
 		         .style("stroke", "none");

        const draw = function(graph) {
            if (!fullGraphData) {
                fullGraphData = graph;
            }

            const basePath = window.graph_options?.base_path || '/';
            const currentPath = window.location.pathname.replace(basePath, '').replace(/\/$/, "");
            const startNode = fullGraphData.nodes.find(n => {
                const nodeUrl = n.url.replace(/\/$/, "");
                if (currentPath === "") {
                    return nodeUrl === "" || nodeUrl === "index.html" || nodeUrl === ".";
                }
                return nodeUrl === currentPath;
            });

            const {
                nodes: nodesData,
                edges: linksData
            } = filterGraph(fullGraphData.nodes, fullGraphData.edges, startNode?.id, isModal ? hops : '1');

           const processedLinksMap = new Map();
           for (const link of linksData) {
               const sourceId = link.source.id || link.source;
               const targetId = link.target.id || link.target;
               const forwardKey = `${sourceId}-${targetId}`;
               const backwardKey = `${targetId}-${sourceId}`;

               if (processedLinksMap.has(backwardKey)) {
                   processedLinksMap.get(backwardKey).bidirectional = true;
               } else if (!processedLinksMap.has(forwardKey)) {
                   processedLinksMap.set(forwardKey, { ...link, bidirectional: false });
               }
           }
           const processedLinks = Array.from(processedLinksMap.values());

            const currentNode = nodesData.find(n => n.id === startNode?.id);
            const isTwoNodes = nodesData.length === 2;

            const simulation = d3.forceSimulation(nodesData)
                .force("link", d3.forceLink(processedLinks).id(d => d.id).distance(FORCE_CONFIG.LINK_DISTANCE))
                .force("charge", d3.forceManyBody().strength(FORCE_CONFIG.CHARGE_STRENGTH))
                .force("center", d3.forceCenter(width / 2, height / 2))
                .force("x", d3.forceX(width / 2).strength(FORCE_CONFIG.X_STRENGTH))
                .force("y", d3.forceY(height / 2).strength(FORCE_CONFIG.Y_STRENGTH))
                .force("collide", d3.forceCollide(d => (d.id === startNode?.id ? NODE_CONFIG.CIRCLE_RADIUS * NODE_CONFIG.CURRENT_NODE_MULTIPLIER : NODE_CONFIG.CIRCLE_RADIUS) + 2));

            if (isTwoNodes) {
                nodesData[0].fx = width / 2;
                nodesData[0].fy = height / 2 - FORCE_CONFIG.LINK_DISTANCE / 2;
                nodesData[1].fx = width / 2;
                nodesData[1].fy = height / 2 + FORCE_CONFIG.LINK_DISTANCE / 2;
            } else if (currentNode) {
                currentNode.fx = width / 2;
                currentNode.fy = height / 2;
            }

            const link = g.append("g")
                .attr("class", "links")
                .selectAll("line")
                .data(processedLinks)
                .enter().append("line")
                .attr("class", "link")
    .attr("marker-end", "url(#arrowhead)")
                .attr("marker-start", d => d.bidirectional ? "url(#arrowhead-start)" : null);

            const node = g.append("g")
                .attr("class", "nodes")
                .selectAll("g")
                .data(nodesData)
                .enter().append("g")
                .attr("class", d => "node" + (currentNode && d.id === currentNode.id ? " current" : ""))
                .on("mouseover", function() {
                    d3.select(this).classed("hover", true);
                })
                .on("mouseout", function() {
                    d3.select(this).classed("hover", false);
                })
                .call(d3.drag()
                    .on("start", dragstarted)
                    .on("drag", dragged)
                    .on("end", dragended));

            node.append("circle")
                .attr("class", "main-circle")
                .attr("r", d => d.id === startNode?.id ? NODE_CONFIG.CIRCLE_RADIUS * NODE_CONFIG.CURRENT_NODE_MULTIPLIER : NODE_CONFIG.CIRCLE_RADIUS)
                .on("click", function(event, d) {
                    window.location.href = new URL(d.url, window.location.origin + basePath).href;
                });

            node.append("text")
				.text(d => d.name)
				            .attr("x", d => d.id === startNode?.id ? NODE_CONFIG.LABEL_X_OFFSET * NODE_CONFIG.CURRENT_NODE_MULTIPLIER : NODE_CONFIG.LABEL_X_OFFSET)
				            .attr("dy", NODE_CONFIG.LABEL_DY_OFFSET);

				        simulation.on("tick", () => {
				            link.each(function(d) {
                    const sourceNode = nodesData.find(n => n.id === (d.source.id || d.source));
                    const targetNode = nodesData.find(n => n.id === (d.target.id || d.target));

                    if (!sourceNode || !targetNode || !sourceNode.x || !targetNode.y) {
                         return;
                    }

                    const dx = targetNode.x - sourceNode.x;
                    const dy = targetNode.y - sourceNode.y;
                    const distance = Math.sqrt(dx * dx + dy * dy);

                    if (distance === 0) {
                        return;
                    }

                    const sourceRadius = (sourceNode.id === startNode?.id ? NODE_CONFIG.CIRCLE_RADIUS * NODE_CONFIG.CURRENT_NODE_MULTIPLIER : NODE_CONFIG.CIRCLE_RADIUS) + LINK_CONFIG.STROKE_MARGIN + (d.bidirectional ? ARROWHEAD.MARKER_WIDTH : 0);
                    const targetRadius = (targetNode.id === startNode?.id ? NODE_CONFIG.CIRCLE_RADIUS * NODE_CONFIG.CURRENT_NODE_MULTIPLIER : NODE_CONFIG.CIRCLE_RADIUS) + LINK_CONFIG.STROKE_MARGIN + ARROWHEAD.MARKER_WIDTH;

                    const sourceX = sourceNode.x + (dx / distance) * sourceRadius;
                    const sourceY = sourceNode.y + (dy / distance) * sourceRadius;
                    const targetX = targetNode.x - (dx / distance) * targetRadius;
                    const targetY = targetNode.y - (dy / distance) * targetRadius;

                    d3.select(this)
                        .attr("x1", sourceX)
                        .attr("y1", sourceY)
                        .attr("x2", targetX)
                        .attr("y2", targetY);
                });

                node
                    .attr("transform", d => `translate(${d.x},${d.y})`);
            });

            currentGraph = { svg, simulation };

            function dragstarted(event, d) {
              if (!event.active) simulation.alphaTarget(SIMULATION_CONFIG.ALPHA_TARGET_ACTIVE).restart();
              d.fx = d.x;
              d.fy = d.y;
            }

            function dragged(event, d) {
              d.fx = event.x;
              d.fy = event.y;
            }

            function dragended(event, d) {
              if (!event.active) simulation.alphaTarget(SIMULATION_CONFIG.ALPHA_TARGET_INACTIVE);
              d.fx = null;
              d.fy = null;
            }
        };

        if (fullGraphData) {
            draw(fullGraphData);
        } else {
            const base_path = window.graph_options?.base_path || '/';
            const graphUrl = new URL(base_path + 'graph/graph.json', window.location.origin);
            if (graphOptions.debug) console.log(`Fetching graph data from ${graphUrl}`);
            d3.json(graphUrl).then(draw);
        }
    }

    function destroy_graph() {
        if (graphOptions.debug) console.log("Destroying graph");
        if (currentGraph) {
            currentGraph.simulation.stop();
            if (currentGraph.svg) {
                currentGraph.svg.remove();
            }
            currentGraph = null;
        }
    }

    draw_graph("#graph", '1');

    window.addEventListener('resize', () => {
       const modal = document.getElementById('modal_background');
       const container = modal ? '#modal_graph_content' : '#graph';
       destroy_graph();
       draw_graph(container, modal ? 'full' : '1');
    });
});
