# Home Clock and Weather Service

A PyQt5-based application for Raspberry Pi that displays current time and weather forecast.

## Features

- Real-time clock display with analog clock face
- Weather forecast for the next 3 days from Seniverse Weather API
- Automatic time synchronization with NTP servers
- Beautiful and user-friendly interface

## Installation

1. Install required packages:

```bash
pip install -r requirements.txt
```

2. Configure the application:
   - Get an API key from Seniverse Weather (https://www.seniverse.com/)
   - Update the `config.py` file with your API key

3. Run the application:

```bash
python main.py
```

## Requirements

- Raspberry Pi 3B or newer
- Python 3.7+
- Internet connection for weather and time synchronization
