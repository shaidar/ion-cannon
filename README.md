<div align="center">
  <img src="https://github.com/user-attachments/assets/a63da5b7-0b27-4b59-b472-2ab9a04a7f10" alt="Centered Image">
</div>

---
# ION Cannon

A high-powered content collection and analysis system that uses multiple Large Language Models (LLMs) to collect, validate, and summarize content from various sources. It helps you stay up-to-date with the latest information by automatically filtering and processing content based on your interests.

## Features

- **Multi-source Content Collection**
  - RSS feeds from major tech and security blogs
  - Reddit channel monitoring

- **Intelligent Content Processing**
  - Keyword-based content filtering
  - Date-based filtering (excludes content older than 10 days)
  - Multi-LLM validation system for relevance checking
  - Automated content summarization
  - Configurable output formats

## Prerequisites

1. Install and run Ollama locally:
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama service
ollama serve

# In a new terminal, pull required models
ollama pull mistral
```

## Installation

1. Install uv (if not already installed):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Clone the repository:
```bash
git clone https://github.com/shaidar/ion-cannon.git
cd ion_cannon
```

3. Create and activate a virtual environment:
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

4. Install the package:
```bash
uv pip install -e ".[dev]"
```

## Configuration

The system is highly configurable through the settings file. You can customize:

1. **Content Sources**
   - `RSS_FEEDS`: List of RSS feed URLs to monitor
   - `REDDIT_CHANNELS`: Reddit channels to monitor

2. **Reddit API Setup**
   1. Go to https://www.reddit.com/prefs/apps
   2. Click "create another app..." at the bottom
   3. Select "script" as the application type
   4. Fill in:
      - name: ion-cannon (or any name you prefer)
      - description: Content collection tool
      - redirect uri: http://localhost:8080
   5. Click "create app"
   6. Note your:
      - client_id (under your app name)
      - client_secret
   7. Add credentials to your settings:
   ```python
   # filepath: ion_cannon/config/settings.py
   REDDIT_CLIENT_ID = "your_client_id"
   REDDIT_CLIENT_SECRET = "your_client_secret"
   REDDIT_USER_AGENT = "ion-cannon:v1.0.0 (by /u/your_username)"
   ```

3. **Content Filtering**
   - `KEYWORDS`: List of keywords to filter content (matches both title and content)
   - Default age filter of 10 days (configurable in code)

4. **LLM Settings**
   - Configure multiple LLMs for content validation
   - Set up dedicated LLMs for summarization

Example settings:
```python
# filepath: ion_cannon/config/settings.py
RSS_FEEDS = [
    "https://www.schneier.com/blog/atom.xml",
    "https://krebsonsecurity.com/feed/"
]

KEYWORDS = [
    "security",
    "artificial intelligence",
    "machine learning"
]
```

## Usage

Basic usage:
```bash
# Collect and process content with default settings
ion-cannon collect

# Use multiple LLMs for better validation
ion-cannon collect --multi-llm

# Save processed content to a specific directory
ion-cannon collect --output ./my-reports

# Show verbose output during processing
ion-cannon collect --verbose
```

List configured sources:
```bash
# Show basic source configuration
ion-cannon sources

# Show detailed source information
ion-cannon sources --verbose
```

## Development

Set up the development environment:

```bash
# Install development dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Run linter
ruff check .

# Run formatter
ruff format .
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the GNU General Public License v3 - see the [LICENSE](LICENSE) file for details.
