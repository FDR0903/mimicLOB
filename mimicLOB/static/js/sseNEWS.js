$(document).ready(function () {
    const configNEWS = {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: "Latest News",
                backgroundColor: 'rgb(101, 99, 132)',
                borderColor: 'rgb(101, 99, 132)',
                data: [],
                fill: true,
            }],
        },
        options: {
            responsive: true,
            title: {
                display: true,
                text: 'Live News'
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

    const contextNEWS = document.getElementById('canvasNEWS').getContext('2d');

    const lineChartNEWS = new Chart(contextNEWS, configNEWS);

    const sourceNEWS = new EventSource("/chart-NEWS");
    sourceNEWS.onmessage = function (event) {
        const data = JSON.parse(event.data);
        
        if (configNEWS.data.labels.length === 100) {
            configNEWS.data.labels.shift();
            configNEWS.data.datasets[0].data.shift();
        }
        configNEWS.data.labels.push(data.time);
        configNEWS.data.datasets[0].data.push(data.value);
        
        lineChartNEWS.update();
    }

});