import numpy as np
import yfinance as yf
from flask import Flask, request, jsonify
from flask_cors import CORS
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input, decode_predictions
from tensorflow.keras.preprocessing import image
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from io import BytesIO
from PIL import Image
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)
CORS(app)

# --- EXPERIMENT 1: CLASSIFICATION ---
model_cnn = MobileNetV2(weights='imagenet')

def prepare_image(img_bytes):
    img = Image.open(BytesIO(img_bytes)).resize((224, 224))
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    return preprocess_input(img_array)

@app.route('/classify', methods=['POST'])
def classify_image():
    if 'file' not in request.files: return jsonify({'error': 'No file'}), 400
    file = request.files['file']
    preds = model_cnn.predict(prepare_image(file.read()))
    results = decode_predictions(preds, top=1)[0]
    return jsonify({'label': results[0][1], 'confidence': f"{results[0][2]*100:.2f}%"})

# --- EXPERIMENT 2: REGRESSION (Linear + LSTM) ---
@app.route('/predict_stock', methods=['POST'])
def predict_stock():
    data = request.json
    ticker = data.get('ticker', 'AAPL')
    
    # 1. Fetch Data
    stock = yf.download(ticker, period='2y', interval='1d')
    if stock.empty: return jsonify({'error': 'Invalid Ticker'}), 400

    # Get 'Close' prices
    values = stock['Close'].values.reshape(-1, 1)
    
    # --- MODEL A: LINEAR REGRESSION ---
    # Prepare simple X (days) and y (price)
    X_lin = np.arange(len(values)).reshape(-1, 1)
    y_lin = values
    X_train_lin, X_test_lin, y_train_lin, y_test_lin = train_test_split(X_lin, y_lin, test_size=0.2, shuffle=False)
    
    lr = LinearRegression()
    lr.fit(X_train_lin, y_train_lin)
    lr_preds = lr.predict(X_test_lin).flatten()

    # --- MODEL B: LSTM ---
    # LSTM requires data scaling (0 to 1) and "lookback" windows
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(values)
    
    look_back = 60  # Look at past 60 days to predict next day
    X_lstm, y_lstm = [], []
    
    for i in range(look_back, len(scaled_data)):
        X_lstm.append(scaled_data[i-look_back:i, 0])
        y_lstm.append(scaled_data[i, 0])
        
    X_lstm, y_lstm = np.array(X_lstm), np.array(y_lstm)
    X_lstm = np.reshape(X_lstm, (X_lstm.shape[0], X_lstm.shape[1], 1)) # Reshape for LSTM [samples, time steps, features]
    
    # Split for LSTM (keeping the same time range as Linear Regression for comparison)
    split_idx = int(len(X_lstm) * 0.8)
    X_train_lstm, X_test_lstm = X_lstm[:split_idx], X_lstm[split_idx:]
    y_train_lstm, y_test_lstm = y_lstm[:split_idx], y_lstm[split_idx:]

    # Build LSTM Model
    model = Sequential()
    model.add(LSTM(units=50, return_sequences=False, input_shape=(X_train_lstm.shape[1], 1)))
    model.add(Dense(1))
    model.compile(optimizer='adam', loss='mean_squared_error')
    
    # Train (batch_size=32, epochs=5 is enough for a quick demo)
    model.fit(X_train_lstm, y_train_lstm, batch_size=32, epochs=5, verbose=0)
    
    # Predict
    lstm_preds_scaled = model.predict(X_test_lstm)
    lstm_preds = scaler.inverse_transform(lstm_preds_scaled).flatten()

    # --- PREPARE RESPONSE ---
    # We align the data so the graph matches up.
    # Note: LSTM cuts off the first 60 days (look_back), so we must adjust indices.
    
    # Total dates available
    all_dates = stock.index.strftime('%Y-%m-%d').tolist()
    
    # Padding Linear Regression to match chart
    # (The test set is the last 20% of the data)
    test_start_idx = len(values) - len(lr_preds)
    
    # Padding LSTM to match chart
    # (LSTM test set is shorter because of look_back, but covers same date range roughly)
    lstm_padding = [None] * (len(values) - len(lstm_preds))
    lr_padding = [None] * (len(values) - len(lr_preds))

    return jsonify({
        'dates': all_dates,
        'actual': values.flatten().tolist(),
        'linear_preds': lr_padding + lr_preds.tolist(),
        'lstm_preds': lstm_padding + lstm_preds.tolist()
    })
@app.route('/')
def home():
    return render_template('index.html')
if __name__ == '__main__':
    app.run(debug=True, port=5000)