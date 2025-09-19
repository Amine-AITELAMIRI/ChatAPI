# Custom ChatGPT API

A custom API server that wraps ChatGPT's web interface, allowing you to use ChatGPT without paying for their API. Runs on Raspberry Pi 4 and is accessible from the internet.

## Features

- **REST API** with `/chat` endpoint
- **Web automation** using Playwright to interact with ChatGPT
- **Internet accessible** with proper port forwarding
- **Raspberry Pi 4 optimized** with headless browser support
- **Simple setup** with no authentication required

## API Usage

### Endpoints

- `GET /` - Health check
- `POST /chat` - Send prompt to ChatGPT
- `GET /health` - Detailed health check
- `GET /docs` - API documentation (Swagger UI)

### Example Request

```bash
curl -X POST "http://your-raspberry-pi-ip:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Hello, how are you?"}'
```

### Example Response

```json
{
  "response": "Hello! I'm doing well, thank you for asking. How can I help you today?",
  "success": true,
  "error_message": null
}
```

## Installation

### Prerequisites

- Raspberry Pi 4 with Raspberry Pi OS
- Python 3.8 or higher
- Internet connection
- ChatGPT Plus account (for web access)

### Step 1: Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install python3 python3-pip -y

# Install system dependencies for Playwright
sudo apt install -y \
    libnss3 \
    libnspr4 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libxss1 \
    libasound2

# Clone or download this project
cd /home/pi/
# (Place all project files here)
```

### Step 2: Install Python Dependencies

```bash
# Install Python packages
pip3 install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### Step 3: Configure Port Forwarding

To make your API accessible from the internet:

1. **Find your Raspberry Pi's local IP:**
   ```bash
   hostname -I
   ```

2. **Configure your router:**
   - Access your router's admin panel (usually 192.168.1.1)
   - Go to Port Forwarding/Virtual Server settings
   - Add a rule:
     - External Port: 8000 (or any port you prefer)
     - Internal IP: Your Pi's IP (e.g., 192.168.1.100)
     - Internal Port: 8000
     - Protocol: TCP

3. **Find your public IP:**
   ```bash
   curl ifconfig.me
   ```

### Step 4: Run the Server

```bash
# Make the startup script executable
chmod +x start_server.py

# Run the server
python3 start_server.py
```

The server will start and you'll see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 5: Initial Login Setup

On first run, the browser will open (or run in headless mode). You'll need to:

1. Navigate to ChatGPT in the browser
2. Log in with your ChatGPT Plus account
3. The automation will detect when you're logged in

**Note:** For headless mode on Raspberry Pi, you may need to run the first setup with `HEADLESS_MODE = False` in `config.py`.

## Usage Examples

### Using curl

```bash
# Test the API
curl -X POST "http://YOUR_PUBLIC_IP:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Write a Python function to calculate fibonacci numbers"}'
```

### Using Python

```python
import requests

response = requests.post(
    "http://YOUR_PUBLIC_IP:8000/chat",
    json={"prompt": "Explain quantum computing in simple terms"}
)

if response.json()["success"]:
    print(response.json()["response"])
else:
    print("Error:", response.json()["error_message"])
```

### Using JavaScript/Node.js

```javascript
const response = await fetch('http://YOUR_PUBLIC_IP:8000/chat', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        prompt: 'Create a recipe for chocolate chip cookies'
    })
});

const data = await response.json();
console.log(data.response);
```

## Configuration

Edit `config.py` to customize:

- `PORT`: Change the server port (default: 8000)
- `HEADLESS_MODE`: Set to `False` for debugging
- `MAX_RETRIES`: Number of retry attempts
- `RESPONSE_TIMEOUT`: Timeout for ChatGPT responses

## Troubleshooting

### Common Issues

1. **Browser fails to start:**
   ```bash
   # Install additional dependencies
   sudo apt install -y libx11-xcb1 libxcb-dri3-0
   ```

2. **Login issues:**
   - Set `HEADLESS_MODE = False` in config.py
   - Run the server and complete login manually
   - Set back to `True` after successful login

3. **Port forwarding not working:**
   - Check router firewall settings
   - Verify port forwarding rules
   - Test with `telnet YOUR_PUBLIC_IP 8000`

4. **Memory issues on Pi:**
   ```bash
   # Increase swap space
   sudo dphys-swapfile swapoff
   sudo nano /etc/dphys-swapfile
   # Change CONF_SWAPSIZE=100 to CONF_SWAPSIZE=2048
   sudo dphys-swapfile setup
   sudo dphys-swapfile swapon
   ```

### Logs

Check the log file for debugging:
```bash
tail -f chatgpt_api.log
```

## Security Considerations

- This API has no authentication - only use on trusted networks
- Consider adding API keys or IP whitelisting for production use
- Monitor usage to avoid rate limiting from ChatGPT

## Running as a Service

To run the server automatically on boot:

```bash
# Create systemd service
sudo nano /etc/systemd/system/chatgpt-api.service
```

Add this content:
```ini
[Unit]
Description=Custom ChatGPT API
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/ChatAPI
ExecStart=/usr/bin/python3 /home/pi/ChatAPI/start_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable chatgpt-api.service
sudo systemctl start chatgpt-api.service
sudo systemctl status chatgpt-api.service
```

## License

This project is for educational and personal use only. Please respect OpenAI's terms of service.
