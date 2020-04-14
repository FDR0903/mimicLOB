$(document).ready(function () {
    const configLOB = {
        type: 'bar',
        // data: [
        //     {labels: [],
        //      dataPoints: [
        //                     { x: 99, y: -71},
        //                     { x: 100, y: 55},
        //                     { x: 101, y: 50 }
        //                  ]
        //     }
        // ],
        data: {
            labels: [99, 100, 101],
            datasets: [
                        {
                            label: "Quantities",
                            backgroundColor: "rgba(34,139,34,0.5)",
                            hoverBackgroundColor: "rgba(34,139,34,1)",
                            data: [-1000, -1500, 1000]
                        }
                    ]
            },

        options: {
            responsive: true,
            title: {
                display: true,
                text: 'Live Lob'
            },

            // scales: {
            //     xAxes: [{
            //     stacked: false
            //     }],
            //     yAxes: [{
            //     stacked: false
            //     }]
            //     }

            // ,
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
                        labelString: 'Prices'
                    }
                }],
                yAxes: [{
                    display: true,
                    scaleLabel: {
                        display: true,
                        labelString: 'Quantitites'
                    }
                }]
            }
        }
    };
    
    const contextLOB = document.getElementById('canvasLOB').getContext('2d');
    const stackChart = new Chart(contextLOB, configLOB);
    const sourceLOB = new EventSource("/chart-LOB");
    stackChart.render();
    sourceLOB.onmessage = function (event) {
        const data = JSON.parse(event.data);
        
        // if (configLOB.data.labels.length === 100) {
        //     configLOB.data.labels.shift();
        //     configLOB.data.datasets[1].data.shift();
        // }
        configLOB.data.labels = data.prices;
        configLOB.data.datasets[0].data = data.quantities;
        
        stackChart.update();
    }
});