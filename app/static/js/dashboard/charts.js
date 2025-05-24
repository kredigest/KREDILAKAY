// KREDILAKAY/app/static/js/dashboard/chart.js
document.addEventListener('DOMContentLoaded', function() {
    // Configuration globale
    Chart.defaults.font.family = "'Nunito Sans', sans-serif";
    Chart.defaults.color = '#718096';
    Chart.defaults.borderColor = 'rgba(226, 232, 240, 0.5)';

    // Sélecteurs
    const ctxLoanStatus = document.getElementById('loanStatusChart');
    const ctxPaymentTrends = document.getElementById('paymentTrendsChart');
    const ctxPortfolioRisk = document.getElementById('portfolioRiskChart');

    // 1. Graphique de statut des prêts (Doughnut)
    if (ctxLoanStatus) {
        const loanStatusData = {
            labels: [
                'Approuvés',
                'En retard',
                'Payés',
                'En défaut'
            ],
            datasets: [{
                data: JSON.parse(ctxLoanStatus.dataset.values),
                backgroundColor: [
                    '#38a169', // Vert
                    '#dd6b20', // Orange
                    '#3182ce', // Bleu
                    '#e53e3e'  // Rouge
                ],
                borderWidth: 0,
                cutout: '70%'
            }]
        };

        new Chart(ctxLoanStatus, {
            type: 'doughnut',
            data: loanStatusData,
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            boxWidth: 12,
                            padding: 20,
                            usePointStyle: true
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const value = context.raw;
                                const percentage = Math.round((value / total) * 100);
                                return `${context.label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                },
                animation: {
                    animateScale: true,
                    animateRotate: true
                }
            }
        });
    }

    // 2. Tendances de paiement (Line)
    if (ctxPaymentTrends) {
        const paymentData = JSON.parse(ctxPaymentTrends.dataset.values);
        
        new Chart(ctxPaymentTrends, {
            type: 'line',
            data: {
                labels: paymentData.dates,
                datasets: [
                    {
                        label: 'Montant Payé (HTG)',
                        data: paymentData.amounts,
                        borderColor: '#4fd1c5',
                        backgroundColor: 'rgba(79, 209, 197, 0.1)',
                        tension: 0.3,
                        fill: true,
                        borderWidth: 2
                    },
                    {
                        label: 'Prêts Délivrés (HTG)',
                        data: paymentData.loans_issued,
                        borderColor: '#f6ad55',
                        backgroundColor: 'rgba(246, 173, 85, 0.1)',
                        tension: 0.3,
                        borderWidth: 2,
                        borderDash: [5, 5]
                    }
                ]
            },
            options: {
                responsive: true,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return new Intl.NumberFormat('ht-HT', {
                                    style: 'currency',
                                    currency: 'HTG'
                                }).format(value);
                            }
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                label += new Intl.NumberFormat('ht-HT', {
                                    style: 'currency',
                                    currency: 'HTG'
                                }).format(context.raw);
                                return label;
                            }
                        }
                    }
                }
            }
        });
    }

    // 3. Risque du portefeuille (Bar)
    if (ctxPortfolioRisk) {
        const riskData = JSON.parse(ctxPortfolioRisk.dataset.values);
        
        new Chart(ctxPortfolioRisk, {
            type: 'bar',
            data: {
                labels: riskData.labels,
                datasets: [{
                    label: 'Score de Risque',
                    data: riskData.scores,
                    backgroundColor: function(context) {
                        const value = context.raw;
                        if (value >= 0.7) return '#e53e3e'; // Rouge
                        if (value >= 0.4) return '#f6ad55'; // Orange
                        return '#38a169'; // Vert
                    },
                    borderWidth: 0,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        min: 0,
                        max: 1,
                        ticks: {
                            callback: function(value) {
                                return Math.round(value * 100) + '%';
                            }
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `Risque: ${Math.round(context.raw * 100)}%`;
                            }
                        }
                    },
                    legend: {
                        display: false
                    }
                }
            }
        });
    }

    // Fonction de mise à jour responsive
    function resizeCharts() {
        Chart.getChart('loanStatusChart')?.resize();
        Chart.getChart('paymentTrendsChart')?.resize();
        Chart.getChart('portfolioRiskChart')?.resize();
    }

    window.addEventListener('resize', resizeCharts);
});
