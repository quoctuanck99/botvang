# Gold Price Tracking Telegram Bot

A Telegram bot that tracks gold prices from Bao Tin Manh Hai and Bao Tin Minh Chau websites and sends updates to a Telegram channel when prices change.

## Features

- Scrapes gold prices from two major Vietnamese gold dealers
- Sends consolidated price updates to a Telegram channel
- Docker support for easy deployment
- Environment variables for secure credential management

## Setup and Deployment

### Local Development

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Create a `.env` file with your credentials:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token
   TELEGRAM_CHANNEL_ID=@your_channel_id
   ```

3. Run the bot:
   ```
   python main.py
   ```

### Docker Deployment

1. Make sure your `.env` file is set up with the correct credentials

2. Build and run using Docker Compose:
   ```
   docker-compose up -d --build
   ```

3. Check logs:
   ```
   docker-compose logs -f
   ```

## Environment Variables

- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token from BotFather
- `TELEGRAM_CHANNEL_ID`: Your Telegram channel ID (e.g., @YourChannelName)

## Project Structure

- `main.py`: Main bot code
- `Dockerfile`: Docker configuration
- `docker-compose.yml`: Docker Compose configuration
- `.env`: Environment variables (do not commit to source control)
- `pyproject.toml`: Project dependencies and metadata
