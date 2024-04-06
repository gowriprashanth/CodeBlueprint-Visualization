export function createOrUpdateChart(data) {
    // Compute width and height dynamically based on data.
    //const diameter = Math.max(document.documentElement.clientWidth, window.innerWidth || 0);
    const width = 500;
    const height = 500;

    // Remove existing chart if it exists.
    d3.select("#chart-container").selectAll("svg").remove();
    
    //Create the color scale.
    const color = d3.scaleLinear()
        .domain([0, 5])
        .range(["hsl(152,80%,80%)", "hsl(228,30%,40%)"])
        .interpolate(d3.interpolateHcl);

    // Create a div for scrolling.
    const chartDiv = d3.select("#chart-container").append("div")
        .attr("class", "chart-container")
        .style("overflow", "auto")
        .style("width", "100%")
        .style("height", "100%");

    // Define the pack function.
    const pack = data => d3.pack()
        .size([width, height])
        .padding(3)
        (d3.hierarchy(data)
        .sum(d => d.children ? 0 : 1)
        .sort((a, b) => b.value - a.value));

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
        .on("mouseover", function() { d3.select(this).attr("stroke", "#FF0000"); })
        .on("mouseout", function() { d3.select(this).attr("stroke", null); })
        .on("click", (event, d) => {
            focus !== d && (zoom(event, d), event.stopPropagation());
            d3.select(this.parentNode).select("text").style("display", "block");
        });

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
    node.on("mouseover", (event, d) => {
        const text = d.data.name;
        tooltip.transition()
            .duration(200)
            .style("opacity", .9);
        tooltip.html(text) 
            .style("left", (event.pageX) + "px")
            .style("top", (event.pageY) + "px");
    })

    // Hide tooltip on mouseout
    .on("mouseout", () => {
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
