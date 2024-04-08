export function createOrUpdateDashboard(data) {
    var { lines_of_code, num_classes, num_methods, num_variables, commit_message, title, commit_number } = data;

    const container = d3.select('#dashboard-container');
    commit_number = 6270 - commit_number + 1;

    createOrUpdateNumberDisplay(container, 'Github Repository', title);
    createOrUpdateNumberDisplay(container, 'Commit Number', commit_number);
    createOrUpdateNumberDisplay(container, 'Lines of Code', lines_of_code);
    createOrUpdateNumberDisplay(container, 'Total Classes', num_classes);
    createOrUpdateNumberDisplay(container, 'Total Methods', num_methods);
    createOrUpdateNumberDisplay(container, 'Total Variables', num_variables);
    createOrUpdateNumberDisplay(container, 'Commit Message', commit_message);
}

function createOrUpdateNumberDisplay(container, label, value) {
    let display = container.select(`#display-${label.replace(/\s+/g, '-')}`);

    if (display.empty()) {
        display = container.append('div')
            .attr('id', `display-${label.replace(/\s+/g, '-')}`)
            .attr('class', 'number-display');
        display.append('div').attr('class', 'label').text(label);
        display.append('div').attr('class', 'value');
    }

    display.select('.value').text(value);
}
