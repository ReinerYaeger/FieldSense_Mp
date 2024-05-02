document.addEventListener("DOMContentLoaded", function () {
            // WebSocket setup
            const url = `ws://${window.location.host}/ws/socket-server/`;
            const dataSocket = new WebSocket(url);

            // Chart configuration
            const avgChartConfig = {
                type: 'scatter',
                data: {
                    labels: [],  // Array to store date-time labels
                    datasets: [{
                        data: [],  // Array to store average data for A0
                        label: "Average Data",
                        backgroundColor: "#699dbe",
                        radius: 0,
                        tension: 0,
                        fill: false,
                    }]
                },
                options: {
                     radius: 0,
                    legend: {
                        display: true,
                        position: "bottom",
                        labels: {
                            fontColor: 'rgb(185,23,23)'
                        }
                    },
                    scales: {
                        yAxes: [{
                            ticks: {
                                beginAtZero: true
                            }
                        }]
                    }
                }
            };

            // Initialize the chart
            const ctx = document.getElementById('acquisitions').getContext('2d');
            const avgChart = new Chart(ctx, avgChartConfig);

            // WebSocket event listener
            dataSocket.addEventListener('message', function (e) {
                const graphData = JSON.parse(e.data);
                console.log(graphData);

                // Update labels and data arrays
                avgChart.data.labels.push(graphData.label);
                avgChart.data.datasets[0].data.push(graphData.avg_sensor_data);


                // Maintain a maximum number of data points
                const maxDataPoints = 100;
                if (avgChart.data.labels.length > maxDataPoints) {
                    avgChart.data.labels.shift();
                    avgChart.data.datasets[0].data.shift();
                    avgChart.data.datasets[1].data.shift();
                    avgChart.data.datasets[2].data.shift();
                }

                avgChart.update();
            });
        });