export function createOrUpdateChart(data) {
    const width = 425;
    const height = 425;

    d3.select("#chart-container").selectAll("svg").remove();
    
    const color = d3.scaleLinear()
        .domain([0, 5])
        .range(["hsl(152,80%,80%)", "hsl(228,30%,40%)"])
        .interpolate(d3.interpolateHcl);

    const chartDiv = d3.select("#chart-container").append("div")
        .attr("class", "chart-container")
        .style("overflow", "auto")
        .style("width", "100%")
        .style("height", "100%");

    const pack = data => d3.pack()
        .size([width, height])
        .padding(3)
        (d3.hierarchy(data)
        .sum(d => d.children ? 0 : 1)
        .sort((a, b) => b.value - a.value));

   const svg = chartDiv.append("svg")
   .attr("viewBox", `-${width / 2} -${height / 2} ${width} ${height}`)
   .attr("width", width)
   .attr("height", height)
   .attr("style", `max-width: 100%; height: auto; display: block; margin: 0 auto; background: ${color(0)}; cursor: pointer;`);

    const node = svg.selectAll("g")
        .data(pack(data).descendants().slice(1))
        .join("g")
        .attr("transform", d => `translate(${d.x},${d.y})`);

        node.append("circle")
    .attr("fill", d => {
        if (d.data.type === "method") {
            return "white";
        } else if (d.data.type === "attribute") {
            return "#FFC0CB";
        } else {
            return color(d.depth);
        }
    })
    .attr("r", d => d.r)
    .on("mouseover", function() { d3.select(this).attr("stroke", "#FF0000"); })
    .on("mouseout", function() { d3.select(this).attr("stroke", null); })
    .on("click", (event, d) => {
        focus !== d && (zoom(event, d), event.stopPropagation());
        d3.select(this.parentNode).select("text").style("display", "block");
    });


    function createOrUpdateNumberDisplay(container, label, value) {
    let display = container.select(`#display-${label.replace(/\s+/g, '-')}`);

    if (display.empty()) {
        display = container.append('div')
            .attr('id', `display-${label.replace(/\s+/g, '-')}`)
            .attr('class', 'attribute-display');
        display.append('div').attr('class', 'label').text(label);
        display.append('div').attr('class', 'value');
    }

    
    display.select('.value').text(value);
    }


    node.on("mouseover", (event, d) => {
    const text = d.data.name; 
    createOrUpdateNumberDisplay(d3.select("body"), "Member name", text); 
    });


    node.on("mouseout", () => {
    
    d3.select(".attribute-display").remove();
    });

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
            }).on("end", () => {
                if (focus !== focus0) {
                    node.select("text").remove(); 
                    if (!focus.children) { 
                        node.filter(node => node === focus)
                            .append("text")
                            .attr("dy", "0.3em")
                            .style("text-anchor", "middle")
                            .style("fill", "black")
                            .style("font-size", "16px")
                            .text(d => d.data.type);
                    }
                }
            });
    }
}
