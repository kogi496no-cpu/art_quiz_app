document.addEventListener('DOMContentLoaded', () => {
    const genre = document.body.dataset.genre;
    if (!genre) {
        console.error('ジャンルが指定されていません。');
        const container = document.querySelector('.container');
        if(container) {
            container.innerHTML = '<h1>エラー</h1><p>ジャンルが指定されていません。トップページからやり直してください。</p><a href="/" class="btn">トップに戻る</a>';
        }
        return;
    }

    fetch(`/quiz/stats/${genre}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`サーバーエラーが発生しました (ステータス: ${response.status})`);
            }
            return response.json();
        })
        .then(data => {
            if (!data || data.field_stats === undefined) {
                throw new Error('サーバーから無効な統計データが返されました。');
            }
            renderOverallAccuracyChart(data);
            renderFieldAccuracyChart(data.field_stats);
            renderFieldAttemptsChart(data.field_stats);
            renderRecentResults(data.recent_results);
        })
        .catch(error => {
            console.error('統計データの取得に失敗しました:', error);
            const container = document.querySelector('.container');
            if(container) {
                container.innerHTML = `<h1>エラー</h1><p>統計データの読み込みに失敗しました。</p><p class="error-message">理由: ${error.message}</p><p>クイズに一度でも回答してから、再度お試しください。</p><a href="/" class="btn">トップに戻る</a>`;
            }
        });

    const resetBtn = document.getElementById('reset-stats-btn');
    if (resetBtn) {
        resetBtn.addEventListener('click', () => {
            if (confirm('本当にこのジャンルの統計データをリセットしますか？元に戻すことはできません。')) {
                fetch(`/api/${genre}/quiz/reset`, {
                    method: 'POST',
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('リセットに失敗しました。');
                    }
                    return response.json();
                })
                .then(data => {
                    alert('統計データをリセットしました。');
                    location.reload();
                })
                .catch(error => {
                    console.error('リセットエラー:', error);
                    alert(`エラーが発生しました: ${error.message}`);
                });
            }
        });
    }
});

function renderOverallAccuracyChart(data) {
    const ctx = document.getElementById('overallAccuracyChart').getContext('2d');
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['正解', '不正解'],
            datasets: [{
                data: [data.correct_attempts, data.total_attempts - data.correct_attempts],
                backgroundColor: [
                    'rgba(75, 192, 192, 0.7)',
                    'rgba(255, 99, 132, 0.7)'
                ],
                borderColor: [
                    'rgba(75, 192, 192, 1)',
                    'rgba(255, 99, 132, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.label || '';
                            if (label) {
                                label += ': ';
                            }
                            const value = context.raw;
                            const total = context.chart.getDatasetMeta(0).total;
                            const percentage = total > 0 ? ((value / total) * 100).toFixed(1) + '%' : '0%';
                            label += `${value}問 (${percentage})`;
                            return label;
                        }
                    }
                }
            }
        }
    });
}

function renderFieldAccuracyChart(fieldStats) {
    const ctx = document.getElementById('fieldAccuracyChart').getContext('2d');
    const labels = fieldStats.map(stat => stat.field);
    const accuracyData = fieldStats.map(stat => stat.accuracy);

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: '正解率 (%)',
                data: accuracyData,
                backgroundColor: 'rgba(54, 162, 235, 0.7)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        callback: function(value) {
                            return value + '%'
                        }
                    }
                }
            }
        }
    });
}

function renderFieldAttemptsChart(fieldStats) {
    const ctx = document.getElementById('fieldAttemptsChart').getContext('2d');
    const labels = fieldStats.map(stat => stat.field);
    const totalData = fieldStats.map(stat => stat.total);
    const correctData = fieldStats.map(stat => stat.correct);

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: '正解数',
                    data: correctData,
                    backgroundColor: 'rgba(75, 192, 192, 0.7)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 1
                },
                {
                    label: '不正解数',
                    data: totalData.map((total, i) => total - correctData[i]),
                    backgroundColor: 'rgba(255, 99, 132, 0.7)',
                    borderColor: 'rgba(255, 99, 132, 1)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    stacked: true,
                },
                y: {
                    stacked: true,
                    beginAtZero: true
                }
            }
        }
    });
}

function renderRecentResults(recentResults) {
    const tableBody = document.querySelector('#recentResultsTable tbody');
    tableBody.innerHTML = ''; // Clear existing rows

    if (recentResults.length === 0) {
        const row = document.createElement('tr');
        const cell = document.createElement('td');
        cell.colSpan = 5;
        cell.textContent = 'まだ回答履歴がありません。';
        cell.style.textAlign = 'center';
        row.appendChild(cell);
        tableBody.appendChild(row);
        return;
    }

    recentResults.forEach(result => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${result.question_field}</td>
            <td>${result.correct_answer}</td>
            <td>${result.user_answer}</td>
            <td class="${result.is_correct ? 'correct' : 'incorrect'}">${result.is_correct ? '正解' : '不正解'}</td>
            <td>${new Date(result.created_at).toLocaleString()}</td>
        `;
        tableBody.appendChild(row);
    });
}