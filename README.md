<img src="https://www.upload.ee/image/19807908/2026-10-02_082256.png" border="0" alt="2026-10-02_082256.png" />

# WhatsApp Link Generator

A desktop WhatsApp link generator built with Python and PyQt5.

## Features

- Generate a WhatsApp link for a single phone number.
- Generate multiple WhatsApp links at once.
- Optional pre-filled messages with automatic URL encoding.
- `wa.me` format or the WhatsApp API URL format.
- Optional `web.whatsapp.com` desktop links.
- Live link preview.
- Clipboard copy support.
- Advanced message placeholders.
- Persistent settings and last-session state via `setting_wa.ini`.
- Dark and light/custom color themes.
- Multilingual interface with 17 languages.
- Runs locally on the user's computer.

## Requirements

- Python 3.9+
- PyQt5

## Installation

```bash
python -m venv .venv
```

### Windows

```powershell
.venv\Scripts\activate
pip install -r requirements.txt
```

### Linux / macOS

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python -m src.whatsapp_link_generator
```

Or:

```bash
python src/whatsapp_link_generator.py
```

## Usage

Enter a phone number using its international country code, without `+` or `00`.

Example:

```text
628123456789
```

A message is optional. The application URL-encodes the message before placing it into the generated WhatsApp link.

The advanced generator accepts one phone number per line and can generate multiple links in one operation.

## Settings

The application stores preferences and the last session in:

```text
setting_wa.ini
```

This file is generated at runtime and is intentionally excluded from Git by `.gitignore`.

Do not commit personal phone numbers, generated links, or other private data.

## Development

Install development dependencies:

```bash
pip install -r requirements-dev.txt
```

Run the test suite:

```bash
pytest
```

Compile-check the application:

```bash
python -m py_compile src/whatsapp_link_generator.py
```

## Project Structure

```text
.
├── .github/
│   └── workflows/
│       └── ci.yml
├── src/
│   ├── __init__.py
│   └── whatsapp_link_generator.py
├── tests/
│   └── test_link_generation.py
├── .gitignore
├── CHANGELOG.md
├── CONTRIBUTING.md
├── pyproject.toml
├── README.md
├── requirements-dev.txt
├── requirements.txt
└── SECURITY.md
```

## Privacy

The application is designed to run locally. It does not require a backend service to generate links. Remember that generated WhatsApp URLs can contain phone numbers and message text, so treat copied or shared links as potentially sensitive.

## License

No open-source license was specified in the original project source. Until a license is added by the copyright holder, all rights remain with the copyright holder.

Copyright © ECOMTECH 2025.
