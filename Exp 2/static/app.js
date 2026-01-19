// Managing Tabs
function switchTab(tabId) {
    // Hide all sections
    document.querySelectorAll('.content-section').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));

    // Show selected
    document.getElementById(tabId).classList.add('active');
    
    // Highlight button (simple logic finding button by text content for demo)
    const buttons = document.querySelectorAll('.tab-btn');
    if(tabId === 'classification') buttons[0].classList.add('active');
    else buttons[1].classList.add('active');
}

// --- Experiment 1: Classification Logic ---
async function uploadImage() {
    const fileInput = document.getElementById('imageInput');
    const file = fileInput.files[0];

    if (!file) {
        alert("Please select an image first!");
        return;
    }

    // Show preview
    const preview = document.getElementById('preview');
    preview.src = URL.createObjectURL(file);
    document.getElementById('result-container').classList.remove('hidden');
    
    document.getElementById('prediction-text').innerText = "Analyzing...";
    document.getElementById('confidence-text').innerText = "";

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('http://127.0.0.1:5000/classify', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        
        document.getElementById('prediction-text').innerText = data.label;
        document.getElementById('confidence-text').innerText = data.confidence;
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('prediction-text').innerText = "Error connecting to backend.";
    }
}


// --- Experiment 2: Regression Logic ---
let myChart = null;

async function predictStock() {
    const ticker = document.getElementById('tickerInput').value;
    const btn = document.querySelector('.input-group button');
    
    if (!ticker) return alert("Please enter a ticker!");

    // Visual feedback that it's working (LSTM takes time)
    btn.innerText = "Training Models...";
    btn.disabled = true;

    try {
        const response = await fetch('http://127.0.0.1:5000/predict_stock', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ticker: ticker })
        });
        
        const data = await response.json();
        if (data.error) { alert(data.error); return; }

        renderChart(data);

    } catch (error) {
        console.error("Error:", error);
        alert("Failed to fetch prediction.");
    } finally {
        btn.innerText = "Predict";
        btn.disabled = false;
    }
}

function renderChart(data) {
    const ctx = document.getElementById('stockChart').getContext('2d');
    
    if (myChart) myChart.destroy();

    myChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.dates,
            datasets: [
                {
                    label: 'Actual Price',
                    data: data.actual,
                    borderColor: '#333', // Dark Grey
                    borderWidth: 2,
                    pointRadius: 0,
                    tension: 0.1
                },
                {
                    label: 'Linear Regression',
                    data: data.linear_preds,
                    borderColor: '#dc3545', // Red
                    borderDash: [5, 5],
                    borderWidth: 2,
                    pointRadius: 0,
                    fill: false
                },
                {
                    label: 'LSTM Prediction',
                    data: data.lstm_preds,
                    borderColor: '#28a745', // Green
                    borderWidth: 2,
                    pointRadius: 0,
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                title: { display: true, text: 'Linear Regression vs LSTM Accuracy' }
            }
        }
    });
}