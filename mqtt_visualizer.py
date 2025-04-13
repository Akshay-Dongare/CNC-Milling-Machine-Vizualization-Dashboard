import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import paho.mqtt.client as mqtt
import json
import queue
import threading
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
import joblib
import os

# Config - Using environment variables for deployment
MQTT_BROKER = os.getenv('MQTT_BROKER', 'localhost')
MQTT_PORT = int(os.getenv('MQTT_PORT', '1883'))
MQTT_TOPIC = os.getenv('MQTT_TOPIC', 'machine/data')
MQTT_USERNAME = os.getenv('MQTT_USERNAME', '')
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD', '')
VOLTAGE = 220
WINDOW_SIZE = 60  # 60 minutes
SLIDE_STEP = 5    # 5 minutes

# Temperature thresholds for color changes
TEMP_THRESHOLDS = {
    "normal": 60,  # Below this is normal (green)
    "warning": 80, # Below this is warning (yellow)
    # Above warning is danger (red)
}

# Load the trained model
@st.cache_resource
def load_model():
    try:
        model = joblib.load('random_forest_model.joblib')
        print("Model loaded successfully!")
        return model
    except Exception as e:
        print(f"Error loading model: {e}")
        return None

# Page config
st.set_page_config(
    page_title="Machine Monitoring Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
    <style>
        .main {
            padding: 0rem 1rem;
        }
        .element-container {
            margin-bottom: 0.5rem;
        }
        [data-testid="stMetricValue"] {
            font-size: 2rem;
        }
        div[data-testid="stHorizontalBlock"] > div {
            width: 50% !important;
            flex: 1 1 calc(50% - 1rem) !important;
            min-width: calc(50% - 1rem) !important;
        }
        .stMarkdown {
            margin-bottom: 0rem;
        }
        [data-testid="stMetricLabel"] {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        .failure-warning {
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 1rem 0;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { background-color: rgba(255, 0, 0, 0.1); }
            50% { background-color: rgba(255, 0, 0, 0.3); }
            100% { background-color: rgba(255, 0, 0, 0.1); }
        }
    </style>
""", unsafe_allow_html=True)

# MQTT Setup
data_queue = queue.Queue()

def on_connect(client, userdata, flags, rc, properties=None):
    client.subscribe(MQTT_TOPIC)
    print(f"Connected with result code {rc}")

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        data_queue.put(data)
        print(f"Received data: {data}")
    except Exception as e:
        print(f"Error processing message: {e}")

client = mqtt.Client(protocol=mqtt.MQTTv5)
client.on_connect = on_connect
client.on_message = on_message

def start_mqtt_client():
    try:
        if MQTT_USERNAME and MQTT_PASSWORD:
            client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_forever()
    except Exception as e:
        print(f"Error connecting to MQTT broker: {e}")

threading.Thread(target=start_mqtt_client, daemon=True).start()

# Initialize session state
if 'data' not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=['timestamp', 'temperature', 'vibration', 'pressure', 'motor_current', 'power', 'failure'])
    st.session_state.last_slide = datetime.now()
    st.session_state.model = load_model()

# Layout
st.title("Machine Monitoring Dashboard")

# Create 2x2 grid layout
row1_col1, row1_col2 = st.columns(2)
row2_col1, row2_col2 = st.columns(2)

# Add failure prediction section
failure_section = st.container()

def create_temperature_bar(value, min_val, max_val, num_segments=12):
    # Normalize the value
    norm_value = (value - min_val) / (max_val - min_val) * 100
    
    # Calculate segment width
    segment_width = 100 / num_segments
    
    fig = go.Figure()
    
    # Add background shapes to create capsule
    # Center rectangle
    fig.add_shape(
        type="rect",
        x0=0,
        y0=-0.4,
        x1=100,
        y1=0.4,
        fillcolor="rgba(50, 50, 50, 0.2)",
        line=dict(color="rgba(50, 50, 50, 0.5)", width=2),
        layer="below"
    )
    
    # Left cap
    fig.add_shape(
        type="circle",
        x0=-0.4,
        y0=-0.4,
        x1=0.4,
        y1=0.4,
        fillcolor="rgba(50, 50, 50, 0.2)",
        line=dict(color="rgba(50, 50, 50, 0.5)", width=2),
        layer="below"
    )
    
    # Right cap
    fig.add_shape(
        type="circle",
        x0=99.6,
        y0=-0.4,
        x1=100.4,
        y1=0.4,
        fillcolor="rgba(50, 50, 50, 0.2)",
        line=dict(color="rgba(50, 50, 50, 0.5)", width=2),
        layer="below"
    )
    
    # Create segments
    for i in range(num_segments):
        segment_start = i * segment_width
        
        # Determine if segment should be filled
        is_filled = norm_value >= segment_start
        
        if is_filled:
            # Calculate color based on segment position
            # Start with cool green, transition through yellow to hot red
            progress = i / (num_segments - 1)
            if progress < 0.5:  # First half - green to yellow
                green = 255
                red = int(255 * (progress * 2))
                blue = 0
            else:  # Second half - yellow to red
                green = int(255 * (1 - (progress - 0.5) * 2))
                red = 255
                blue = 0
                
            color = f"rgb({red}, {green}, {blue})"
            
            # Add segment with rounded corners for first and last segments
            if i == 0:  # First segment
                fig.add_shape(
                    type="circle",  # Left cap of first segment
                    x0=segment_start,
                    y0=-0.3,
                    x1=segment_start + 0.6,
                    y1=0.3,
                    fillcolor=color,
                    line=dict(color=color, width=0),
                    layer="above"
                )
            
            # Add main segment rectangle
            fig.add_shape(
                type="rect",
                x0=segment_start + (0.3 if i == 0 else 0),
                y0=-0.3,
                x1=segment_start + segment_width * 0.95,
                y1=0.3,
                fillcolor=color,
                line=dict(color=color, width=0),
                layer="above"
            )
            
            if i == num_segments - 1 and norm_value >= 100:  # Last segment if filled
                fig.add_shape(
                    type="circle",  # Right cap of last segment
                    x0=segment_start + segment_width * 0.95 - 0.6,
                    y0=-0.3,
                    x1=segment_start + segment_width * 0.95,
                    y1=0.3,
                    fillcolor=color,
                    line=dict(color=color, width=0),
                    layer="above"
                )
    
    # Add temperature value with color based on level
    progress = norm_value / 100
    if progress < 0.5:
        text_color = "green"
    elif progress < 0.75:
        text_color = "orange"
    else:
        text_color = "red"
    
    # Update layout
    fig.update_layout(
        title={
            'text': f"Temperature: {value:.1f}°C",
            'y':0.85,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(size=16, color=text_color)
        },
        height=100,
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            range=[-1, 101],
            fixedrange=True
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            range=[-0.5, 0.5],
            fixedrange=True
        ),
        showlegend=False
    )
    
    return fig

def create_line_chart(df, y_col, title, height=300):
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df[y_col],
        mode='lines',
        name=y_col,
        line=dict(width=2)
    ))
    
    fig.update_layout(
        title=title,
        height=height,
        margin=dict(l=10, r=10, t=50, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='LightGray',
            title="Time"
        ),
        yaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='LightGray',
            title=y_col
        )
    )
    
    return fig

# Initialize placeholder containers
if 'placeholder' not in st.session_state:
    with row1_col1:
        st.session_state['vib_chart'] = st.empty()
    with row1_col2:
        st.session_state['press_chart'] = st.empty()
    with row2_col1:
        st.session_state['power_chart'] = st.empty()
    with row2_col2:
        st.session_state['temp_container'] = st.container()
        with st.session_state['temp_container']:
            st.session_state['temp_gauge'] = st.empty()
            st.session_state['metrics'] = st.empty()
    with failure_section:
        st.session_state['failure_warning'] = st.empty()

def predict_failure(data):
    """Make failure prediction using the loaded model"""
    if st.session_state.model is None:
        return None, None
    
    # Prepare data for prediction
    features = ['temperature', 'vibration', 'pressure', 'motor_current']
    X = data[features].iloc[-1:].copy()  # Get latest readings
    
    try:
        # Make prediction
        prediction = st.session_state.model.predict(X)
        probability = st.session_state.model.predict_proba(X)[0, 1]  # Probability of failure
        return prediction[0], probability
    except Exception as e:
        print(f"Error making prediction: {e}")
        return None, None

def update_dashboard():
    try:
        # Process new data
        data_updated = False
        while not data_queue.empty():
            d = data_queue.get()
            new = pd.DataFrame([{
                'timestamp': pd.to_datetime(d['timestamp']),  # Convert the timestamp from the data
                'temperature': d['temperature'],
                'vibration': d['vibration'],
                'pressure': d['pressure'],
                'motor_current': d['motor_current'],
                'power': d['power'],
                'failure': d['failure']
            }])
            st.session_state.data = pd.concat([st.session_state.data, new], ignore_index=True)
            data_updated = True
        
        if not data_updated:
            return

        # Implement sliding window using the latest timestamp from data
        if not st.session_state.data.empty:
            latest_timestamp = st.session_state.data['timestamp'].max()
            window_start = latest_timestamp - pd.Timedelta(minutes=WINDOW_SIZE)
            st.session_state.data = st.session_state.data[
                st.session_state.data['timestamp'] >= window_start
            ].copy()

        df = st.session_state.data

        if not df.empty:
            # Make failure prediction
            prediction, probability = predict_failure(df)
            
            # Update failure warning
            if prediction is not None:
                with st.session_state['failure_warning']:
                    if prediction == 1:
                        st.markdown(
                            f"""
                            <div class="failure-warning">
                                <h3 style="color: red;">⚠️ High Risk of Failure Detected!</h3>
                                <p>Failure probability: {probability*100:.1f}%</p>
                                <p>Recommended action: Schedule immediate maintenance check</p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(
                            f"""
                            <div style="padding: 1rem; border-radius: 0.5rem; background-color: rgba(0, 255, 0, 0.1);">
                                <h3 style="color: green;">✅ System Operating Normally</h3>
                                <p>Failure probability: {probability*100:.1f}%</p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
            
            # Update temperature bar first for faster response
            current_temp = df['temperature'].iloc[-1]
            with st.session_state['temp_container']:
                st.session_state['temp_gauge'].plotly_chart(
                    create_temperature_bar(
                        current_temp,
                        df['temperature'].min(),
                        df['temperature'].max()
                    ),
                    use_container_width=True
                )
            
            # Update other charts
            st.session_state['vib_chart'].plotly_chart(
                create_line_chart(df, 'vibration', 'Vibration'),
                use_container_width=True
            )
            
            st.session_state['press_chart'].plotly_chart(
                create_line_chart(df, 'pressure', 'Pressure'),
                use_container_width=True
            )
            
            st.session_state['power_chart'].plotly_chart(
                create_line_chart(df, 'power', 'Power Consumption'),
                use_container_width=True
            )
            
            # Calculate metrics
            energy_consumption = (df['power'] * (1/3600)).sum()  # Convert to Wh
            failure_probability = probability * 100 if probability is not None else df['failure'].mean() * 100
            
            # Update metrics with emojis
            with st.session_state['temp_container']:
                with st.session_state['metrics'].container():
                    st.markdown("### Summary Metrics")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("⚡ Total Energy", f"{energy_consumption:.1f} Wh")
                    with col2:
                        st.metric("⚠️ Failure Risk", f"{failure_probability:.1f}%")
    except Exception as e:
        print(f"Error in update_dashboard: {e}")

# Main loop
if __name__ == "__main__":
    st_autorefresh(interval=1000, limit=1000, key="dashboard_refresh")
    update_dashboard()