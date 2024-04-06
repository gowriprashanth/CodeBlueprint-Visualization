export function createOrUpdateDashboard(data) {
    const { lines_of_code, num_classes, num_methods, num_variables } = data;

    // Select the container element where you want to create the dashboard
    const container = d3.select('#dashboard-container');

    // Creating or updating number displays for each metric
    createOrUpdateNumberDisplay(container, 'Lines of Code', lines_of_code);
    createOrUpdateNumberDisplay(container, 'Number of Classes', num_classes);
    createOrUpdateNumberDisplay(container, 'Number of Methods', num_methods);
    createOrUpdateNumberDisplay(container, 'Number of Variables', num_variables);
}

// Function to create or update number display for a metric
function createOrUpdateNumberDisplay(container, label, value) {
    let display = container.select(`#display-${label.replace(/\s+/g, '-')}`);

    // If display does not exist, create it
    if (display.empty()) {
        display = container.append('div')
            .attr('id', `display-${label.replace(/\s+/g, '-')}`)
            .attr('class', 'number-display');
        display.append('div').attr('class', 'label').text(label);
        display.append('div').attr('class', 'value');
    }

    // Update the value
    display.select('.value').text(value);
}
