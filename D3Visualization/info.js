// Load data from info.json
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
