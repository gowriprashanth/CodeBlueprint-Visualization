// Load data from the output.json file
d3.json("transform.json").then(data => {
    // Your existing D3 code for circular packing chart
    const chart = createCircularPackingChart(data);
    document.getElementById("chart-container").appendChild(chart);
});
  
// Modified D3 code for circular packing chart based on the provided JSON data
function createCircularPackingChart(data) {
    // Specify the chart’s dimensions.
    const width = 1000;
    const height = width;
  
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
    const svg = d3.create("svg")
        .attr("viewBox", `-${width / 2} -${height / 2} ${width} ${height}`)
        .attr("width", width)
        .attr("height", height)
        .attr("style", `max-width: 100%; height: auto; display: block; margin: 0 -14px; background: ${color(0)}; cursor: pointer;`);
  
    // Append the nodes.
    const node = svg.append("g")
      .selectAll("g")
      .data(pack(data).descendants().slice(1))
      .join("g")
        .attr("transform", d => `translate(${d.x},${d.y})`);
  
    node.append("circle")
      .attr("fill", d => d.children ? color(d.depth) : "white")
      //.attr("fill", d => color(d.data.name))
      //.attr("pointer-events", d => !d.children ? "none" : null)
      .attr("r", d => d.r)
      .on("mouseover", function() { d3.select(this).attr("stroke", "#000"); })
      .on("mouseout", function() { d3.select(this).attr("stroke", null); })
      .on("click", (event, d) => focus !== d && (zoom(event, d), event.stopPropagation()));
  
    // Function to determine color based on method or attribute
      function getColor(name) {
        if (name.includes("method")) {
          return "blue"; // Assign blue color to methods
        } else if (name.includes("attribute")) {
          return "red"; // Assign red color to attributes
        } else {
          return "white"; // Default color
        }
      }

    // Add text labels near the circles.
    node.append("text")
      .style("font-size", "15px")
      .style("text-anchor", "middle")
      .style("pointer-events", "none")
      .style("fill", "black")
      .style("display", "none")
      .text(d => d.data.name)
      .attr("dx", function(d) {
        return -d.r ;
      })
      .attr("dy", function(d) {
        return -d.r ;
      });
  
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
  
      //label.attr("transform", d => `translate(${(d.x - v[0]) * k},${(d.y - v[1]) * k})`);
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
  
    return svg.node();
}

// Load data from transform.json
d3.json("transform.json").then(function(data) {
    // Extract data
    const numLinesOfCode = data.lines_of_code;
    const numClasses = data.num_classes;
    const numMethods = data.num_methods;
    const numVariables = data.num_variables;

    // Set up dimensions
    const width = 800;
    const height = 500;

    // Create a container div
    const container = d3.select("#chart-container")
        .append("div")
        .style("width", `${width}px`)
        .style("height", `${height}px`)
        .style("text-align", "left")
        .style("font-family", "Arial, sans-serif")
        .style("color", "#333");

    // Create formatted text
    const formattedText = `
        
        <p><span style="color: red; font-weight: bold;">Lines of Code:</span> <span style="font-weight: bold;">${numLinesOfCode.toLocaleString()}</span></p>
        <p><span style="color: green; font-weight: bold;">Number of Classes:</span> <span style="font-weight: bold;">${numClasses.toLocaleString()}</span></p>
        <p><span style="color: orange; font-weight: bold;">Number of Methods:</span> <span style="font-weight: bold;">${numMethods.toLocaleString()}</span></p>
        <p><span style="color: purple; font-weight: bold;">Number of Variables:</span> <span style="font-weight: bold;">${numVariables.toLocaleString()}</span></p>
    `;

    // Append formatted text to the container
    container.html(formattedText);
});
