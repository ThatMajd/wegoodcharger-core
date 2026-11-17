<div align="center">
  <a href="https://apps.apple.com/app/wegoodcharger/id6466698087">
    <img src="https://is1-ssl.mzstatic.com/image/thumb/Purple126/v4/7b/5e/21/7b5e2190-7c74-9476-1348-debf34fffbfa/AppIcon-1x_U007emarketing-0-5-0-85-220.png/512x512bb.jpg" width="120" alt="WeGoodCharger app icon">
  </a>

  <h1>WeGood Charger Core</h1>
  <p>An unofficial Python client for interacting with WeGood-compatible EV chargers through the WeGu cloud service.</p>
</div>

This is a hobby project built around an undocumented API, so expect rough edges and occasional breaking changes.

## What it can do

- Log in with a WeGood account or an existing token
- Check whether your charger is online
- Read live charger and mainboard status
- Fetch charging history
- Restart the charger mainboard

## Setup

Requires Python 3.8 or newer.

```bash
git clone https://github.com/ThatMajd/wegoodcharger-core.git
cd wegoodcharger-core
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```python
from client import CloudClient

# Prompts for your email and password.
client = CloudClient()

# Or reuse an existing token instead:
# client = CloudClient(token="your-session-token")

# Basic information about the registered charger.
device = client.device_payload
print(device)  # dict with IDs, creation time, last seen time, and online state

# Whether the charger was online when its data was last fetched.
online = client.is_online()
print(online)  # bool

# Live port, mainboard, and WebSocket data. The charger must be online.
status = client.status()
print(status)  # formatted JSON string

# Paginated charging history.
records = client.charge_records(page_num=1, page_size=10)
print(records)  # raw API response as a dict

# Account information returned by the service.
info = client.get_info()
print(info)  # raw API response as a dict

# Remotely restart the physical charger's mainboard.
restart = client.restart_mainboard()
print(restart)  # raw API response as a dict
```

Keep tokens and credentials out of source control. If you store a token, load it from an environment variable or another private location.

## Current limitations

- Only accounts with one registered charger are supported.
- Some status data is only available while the charger is online or charging.
- The cloud API is undocumented and may change at any time.
- This has not been tested for production use.

This project is not affiliated with or endorsed by WeGood or WeGu. Use it at your own risk, especially when calling commands that affect the physical charger.
