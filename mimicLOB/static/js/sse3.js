$(document).ready(function () {
    const configQTTY = {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: "quantities",
                backgroundColor: 'rgb(101, 99, 132)',
                borderColor: 'rgb(101, 99, 132)',
                data: [],
                fill: false,
            }],
        },
        options: {
            responsive: true,
            title: {
                display: true,
                text: 'Executed Quantities'
            },
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

    const contextQTTY = document.getElementById('canvasQTTY').getContext('2d');

    const barChart = new Chart(contextQTTY, configQTTY);

    const sourceqtty = new EventSource("/chart-qtties");
    sourceqtty.onmessage = function (event) {
        const data = JSON.parse(event.data);
        
        if (configQTTY.data.labels.length === 100) {
            configQTTY.data.labels.shift();
            configQTTY.data.datasets[1].data.shift();
        }
        configQTTY.data.labels.push(data.time);
        configQTTY.data.datasets[0].data.push(data.value);
        
        barChart.update();
    }

});