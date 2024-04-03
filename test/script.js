import { debounce } from './debounce.js';
import { createOrUpdateChart } from './chart.js';

// Debounced updateVisualization function
export const UpdateVisualization = debounce(function(commitNumber) {
    // Make an AJAX call to fetch data based on the commit number from Flask endpoint
    axios.post('http://127.0.0.1:5000/get_d3_data', { commit_number: commitNumber })
    .then(response => {
        createOrUpdateChart(response.data);
    })
    .catch(error => {
        console.error('Error fetching data:', error);
    });
}, 500); // Adjust the delay as needed

// Initial visualization update with default input value
UpdateVisualization(1);

// Add event listener for input box value change
document.getElementById("updateButton").addEventListener("click", function() {
    const commitNumber = +document.getElementById("commitNumberInput").value;
    UpdateVisualization(commitNumber);
});