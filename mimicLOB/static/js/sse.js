$(document).ready(function () {
    const config = {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: "best bid",
                backgroundColor: 'rgb(101, 99, 132)',
                borderColor: 'rgb(101, 99, 132)',
                data: [],
                fill: true,
            },
            {
                label: "best Ask",
                backgroundColor: 'rgb(19, 99, 132)',
                borderColor: 'rgb(19, 99, 132)',
                data: [],
                fill: true,
            }],
        },
        options: {
            responsive: true,
            title: {
                display: true,
                text: 'Live Lob Prices'
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

    const context = document.getElementById('canvas').getContext('2d');

    const lineChart = new Chart(context, config);

    const sourceBID = new EventSource("/chart-pricesBID");
    const sourceASK = new EventSource("/chart-pricesASK");
    sourceASK.onmessage = function (event) {
        const data = JSON.parse(event.data);
        
        if (config.data.labels.length === 100) {
            config.data.labels.shift();
            config.data.datasets[1].data.shift();
        }
        config.data.labels.push(data.time);
        config.data.datasets[1].data.push(data.value);
        
        lineChart.update();
    }

    sourceBID.onmessage = function (event) {
        const data = JSON.parse(event.data);
        
        if (config.data.labels.length === 100) {
            config.data.labels.shift();
            config.data.datasets[0].data.shift();
        }
        config.data.labels.push(data.time);
        config.data.datasets[0].data.push(data.value);
        
        lineChart.update();
    }













});