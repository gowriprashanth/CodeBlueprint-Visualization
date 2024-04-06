import { debounce } from './debounce.js';
import { createOrUpdateChart } from './chart.js';
import { createOrUpdateDashboard } from './dashboard.js';

// Debounced updateVisualization function
export const UpdateVisualization = debounce(function(commitNumber) {
    // Make an AJAX call to fetch data based on the commit number from Flask endpoint
    axios.post('http://127.0.0.1:5000/get_d3_data', { commit_number: commitNumber })
    .then(response => {
        createOrUpdateChart(response.data);
        createOrUpdateDashboard(response.data);
    })
    .catch(error => {
        console.error('Error fetching data:', error);
    });
}, 500); // Adjust the delay as needed

// Initial visualization update with default input value
UpdateVisualization(6270);

// Add event listener for slider input change
document.getElementById("commitNumberSlider").addEventListener("input", function() {
    const sliderMax = 6270; // Maximum value of the slider
    const sliderValue = +document.getElementById("commitNumberSlider").value;
    
    // Calculate the corresponding commit number
    const commitNumber = sliderMax - sliderValue + 1;
    
    UpdateVisualization(commitNumber);
});