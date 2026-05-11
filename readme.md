# aiolocknalert

Async Python client for LocknAlert bridge onboarding and MQTT bootstrap.

This library is used by the Home Assistant LocknAlert integration to securely retrieve MQTT connection details from a LocknAlert bridge over HTTPS during onboarding.

---

## Features

- Async `aiohttp`-based API client
- HTTPS bridge communication
- MQTT bootstrap credential retrieval
- Simple onboarding flow
- Typed exceptions for Home Assistant config flows
- Lightweight with minimal dependencies

---

## Installation

```bash
pip install aiolocknalert
```

---

## Example

```python
from aiohttp import ClientSession

from aiolocknalert import (
    LocknAlertBridgeApi,
    LocknAlertCannotConnect,
    LocknAlertInvalidAuth,
)

async def main() -> None:
    api = LocknAlertBridgeApi("192.168.1.50")

    async with ClientSession() as session:
        try:
            bootstrap = await api.async_bootstrap(
                session,
                serial_number="LNA123456",
            )

            print(bootstrap)

        except LocknAlertCannotConnect:
            print("Bridge unreachable")

        except LocknAlertInvalidAuth:
            print("Invalid serial number")
```

---

## Bridge Onboarding Flow

1. Home Assistant discovers or connects to the bridge
2. User enters the LocknAlert bridge serial number
3. Bridge validates the serial number against the hardware identity
4. Bridge returns MQTT bootstrap credentials
5. Home Assistant stores the credentials securely

---

## Security Notes

The bridge never exposes stored MQTT credentials publicly.

MQTT bootstrap credentials are only returned when:
- The provided serial number matches the physical bridge identity
- The bridge onboarding window is active

All bridge communication occurs over HTTPS.

---

## Requirements

- Python 3.12+
- aiohttp 3.9+

---

## Development

Clone the repository:

```bash
git clone https://github.com/LocknAlert-Pty-LTD/aiolocknalert.git
cd aiolocknalert
```

Install development dependencies:

```bash
pip install -e .
pip install pytest pytest-asyncio
```

Run tests:

```bash
pytest
```

Build package:

```bash
python -m build
```

---

## License

MIT License
