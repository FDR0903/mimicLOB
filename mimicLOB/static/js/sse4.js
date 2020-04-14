$(document).ready(function () {
    const configHISTO = {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: "Executed Prices",
                backgroundColor: 'rgb(101, 99, 132)',
                borderColor: 'rgb(101, 99, 132)',
                data: [],
                fill: true,
            }],
        },
        options: {
            responsive: true,
            tooltips: {
                mode: 'index',
                intersect: true,
            },
            hover: {
                mode: 'nearest',
                intersect: true
            },
            scales: {
                xAxes: [{
                    display: true,
                    scaleLabel: {
                        display: true,
                        labelString: 'Time'
                    }
                }],
                yAxes: [{
                    display: true,
                    scaleLabel: {
                        display: true,
                        labelString: 'Value'
                    }
                }]
            }
        }
    };

    const contextHISTO = document.getElementById('canvasHISTO').getContext('2d');

    const lineChartHISTO = new Chart(contextHISTO, configHISTO);

    const sourceHISTO = new EventSource("/chart-histo");
    sourceHISTO.onmessage = function (event) {
        const data = JSON.parse(event.data);
        
        // if (config.data.labels.length === 100) {
        //     config.data.labels.shift();
        //     config.data.datasets[0].data.shift();
        // }
        configHISTO.data.labels = data.times;
        configHISTO.data.datasets[0].data = data.value;
        
        lineChartHISTO.update();
    }




});