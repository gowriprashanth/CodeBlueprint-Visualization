// Function to update visualization based on slider value
function updateVisualization(commitNumber) {
    // Make an AJAX call to fetch data based on the commit number
    // Replace 'transform.json' with your endpoint to fetch data dynamically
    d3.json(`transform_${commitNumber}.json`).then(data => {
        createOrUpdateChart(data);
    });
}

// Modified D3 code for circular packing chart based on the provided JSON data
// Modified D3 code for circular packing chart based on the provided JSON data
function createOrUpdateChart(data) {
    // Specify the chart’s dimensions.
    const width = 800;
    const height = 500;

    // Create the color scale.
    const color = d3.scaleLinear()
        .domain([0, 5])
        .range(["hsl(45, 80%, 60%)", "hsl(228, 30%, 40%)"])
        .interpolate(d3.interpolateHcl);

    // Compute the layout.
    const pack = data => d3.pack()
        .size([width, height])
        .padding(3)
        (d3.hierarchy(data)
        .sum(d => d.children ? 0 : 1)
        .sort((a, b) => b.value - a.value));

    // Create the SVG container.
    const svg = d3.select("#chart-container").selectAll("svg")
        .data([data])
        .join("svg")
        .attr("viewBox", `-${width / 2} -${height / 2} ${width} ${height}`)
        .attr("width", width)
        .attr("height", height)
        .attr("style", `max-width: 100%; height: auto; display: block; margin: 0 auto; background: ${color(0)}; cursor: pointer;`);

    // Append the nodes.
    const node = svg.selectAll("g")
        .data(pack(data).descendants().slice(1))
        .join("g")
        .attr("transform", d => `translate(${d.x},${d.y})`);

    node.append("circle")
        .attr("fill", d => d.children ? color(d.depth) : "white")
        .attr("r", d => d.r)
        .on("mouseover", function() { d3.select(this).attr("stroke", "#000"); })
        .on("mouseout", function() { d3.select(this).attr("stroke", null); });

    // Add text labels near the circles.
    node.append("text")
        .style("font-size", "15px")
        .style("text-anchor", "middle")
        .style("pointer-events", "none")
        .style("fill", "black")
        .style("display", "none")
        .text(d => d.data.name)
        .attr("dx", function(d) { return -d.r; })
        .attr("dy", function(d) { return -d.r; });

    // Create the zoom behavior and zoom immediately into the initial focus node.
    svg.on("click", (event) => zoom(event, pack(data)));
    let focus = pack(data);
    let view;
    zoomTo([focus.x, focus.y, focus.r * 2]);

    function zoomTo(v) {
        const k = width / v[2];
        view = v;
        node.attr("transform", d => `translate(${(d.x - v[0]) * k},${(d.y - v[1]) * k})`);
        node.select("circle").attr("r", d => d.r * k);
    }

    function zoom(event, d) {
        const focus0 = focus;
        focus = d;
        const transition = svg.transition()
            .duration(event.altKey ? 7500 : 750)
            .tween("zoom", d => {
                const i = d3.interpolateZoom(view, [focus.x, focus.y, focus.r * 2]);
                return t => zoomTo(i(t));
            });
    }
}


// Create a slider input element
const slider = d3.select("#sliderContainer")
    .append("input")
    .attr("type", "range")
    .attr("min", 1)
    .attr("max", 6270)
    .attr("value", 1)
    .attr("id", "commitSlider");

// Add event listener for slider input
slider.on("input", function() {
    const commitNumber = this.value;
    updateVisualization(commitNumber);
});

// Initial visualization update with default slider value
updateVisualization(1);
