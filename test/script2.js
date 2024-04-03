// Debounce function
function debounce(func, delay) {
    let timer;
    return function() {
        const context = this;
        const args = arguments;
        clearTimeout(timer);
        timer = setTimeout(() => {
            func.apply(context, args);
        }, delay);
    };
}

// Modified D3 code for circular packing chart based on the provided JSON data
function createOrUpdateChart(data) {
    // Compute the layout.
    const pack = data => d3.pack()
        .size([width, height])
        .padding(3)
        (d3.hierarchy(data)
        .sum(d => d.children ? 0 : 1)
        .sort((a, b) => b.value - a.value));

    // Compute width and height dynamically based on data.
    const diameter = Math.max(document.documentElement.clientWidth, window.innerWidth || 0);
    const width = diameter;
    const height = diameter;

    // Remove existing chart if it exists.
    d3.select("#chart-container").selectAll("svg").remove();
    
    // Create the color scale.
    const color = d3.scaleLinear()
        .domain([0, 5])
        .range(["hsl(45, 80%, 60%)", "hsl(228, 30%, 40%)"])
        .interpolate(d3.interpolateHcl);

    // Create a div for scrolling.
    const chartDiv = d3.select("#chart-container").append("div")
        .attr("class", "chart-container")
        .style("overflow", "auto")
        .style("width", "100%")
        .style("height", "100%");


   // Create the SVG container inside the div.
   const svg = chartDiv.append("svg")
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
        .on("mouseout", function() { d3.select(this).attr("stroke", null); })
        .on("click", (event, d) => focus !== d && (zoom(event, d), event.stopPropagation()));

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

    // Define the tooltip
    var tooltip = d3.select("body").append("div")
    .attr("class", "tooltip")
    .style("opacity", 0);

    // Show tooltip on mouseover
    node.on("mouseover", function(d) {
        var text = d3.select(this).select("text").text();
        tooltip.transition()
            .duration(200)
            .style("opacity", .9);
        tooltip.html(text) 
            .style("left", (d3.event.pageX ) + "px")
            .style("top", (d3.event.pageY ) + "px");
    })

    // Hide tooltip on mouseout
    .on("mouseout", function(d) {
        tooltip.transition()
            .duration(500)
            .style("opacity", 0);
    });

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


// Debounced updateVisualization function
const UpdateVisualization = debounce(function(commitNumber) {
    // Make an AJAX call to fetch data based on the commit number from Flask endpoint
    axios.post('http://127.0.0.1:5000/get_d3_data', { commit_number: commitNumber })
    .then(response => {
        createOrUpdateChart(response.data);
    })
    .catch(error => {
        console.error('Error fetching data:', error);
    });
}, 500); // Adjust the delay as needed

// Add event listener for input box value change
document.getElementById("updateButton").addEventListener("click", function() {
    const commitNumber = +document.getElementById("commitNumberInput").value;
    UpdateVisualization(commitNumber);
});

// Initial visualization update with default input value
UpdateVisualization(1);
