import { debounce } from './debounce.js';
import { createOrUpdateChart } from './chart.js';
import { createOrUpdateDashboard } from './dashboard.js';

// Debounced updateVisualization function
export const UpdateVisualization = debounce(function(commitNumber) {
    // Make an AJAX call to fetch data based on the commit number from Flask endpoint
    axios.post('https://codeblueprint-deployment-4dd83ce64f5a.herokuapp.com/get_d3_data', { commit_number: commitNumber })
    .then(response => {
        createOrUpdateChart(response.data);
        createOrUpdateDashboard(response.data);
    })
    .catch(error => {
        console.error('Error fetching data:', error);
    });
}, 500);


UpdateVisualization(6270);
updateSliderValues(6270, 1);


document.getElementById("commitNumberSlider").addEventListener("input", function() {
    const sliderMax = 6270; 
    const sliderValue = +document.getElementById("commitNumberSlider").value;
    
  
    var commitNumber = sliderMax - sliderValue + 1;
    
    UpdateVisualization(commitNumber);
    updateSliderValues(sliderMax, sliderValue);
});

function updateSliderValues(max, value) {
    const sliderValuesContainer = document.getElementById("sliderValues");
    sliderValuesContainer.innerHTML = '';


    const step = Math.floor(max / 10);


    for (let i = 0; i <= max; i += step) {
        const span = document.createElement('span');
        span.textContent = i;
        sliderValuesContainer.appendChild(span);
    }
}
