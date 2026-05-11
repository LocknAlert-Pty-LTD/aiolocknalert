"""HTTPS API client for LocknAlert bridge bootstrap."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

from aiohttp import ClientError, ClientSession, ClientTimeout

from .const import DEFAULT_API_PORT, DEFAULT_TIMEOUT

_LOGGER = logging.getLogger(__name__)


class LocknAlertApiError(Exception):
    """Base API error."""


class LocknAlertCannotConnect(LocknAlertApiError):
    """Bridge is unreachable."""


class LocknAlertInvalidAuth(LocknAlertApiError):
    """Bridge rejected credentials or token."""


class LocknAlertPairingRequired(LocknAlertApiError):
    """Bridge requires pairing mode or onboarding window."""


class LocknAlertInvalidResponse(LocknAlertApiError):
    """Bridge returned an invalid response."""


@dataclass(slots=True)
class LocknAlertBridgeApi:
    """API wrapper for LocknAlert bridge onboarding."""

    host: str
    port: int = DEFAULT_API_PORT
    verify_ssl: bool = False
    timeout: int = DEFAULT_TIMEOUT

    @property
    def base_url(self) -> str:
        """Return base bridge URL."""
        return f"https://{self.host}:{self.port}"

    async def _request(
        self,
        session: ClientSession,
        method: str,
        path: str,
        *,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make a request to the LocknAlert bridge."""
        url = f"{self.base_url}{path}"

        _LOGGER.debug(
            "HTTP %s %s json_data=%s",
            method,
            url,
            "<redacted>" if json_data else None,
        )

        try:
            async with session.request(
                method,
                url,
                json=json_data,
                ssl=self.verify_ssl,
                timeout=ClientTimeout(total=self.timeout),
            ) as response:
                if response.status in (401, 403):
                    raise LocknAlertInvalidAuth

                if response.status == 409:
                    raise LocknAlertPairingRequired

                if response.status >= 400:
                    raise LocknAlertCannotConnect(f"HTTP {response.status}")

                try:
                    data = await response.json()
                except Exception as err:
                    text = await response.text()
                    _LOGGER.debug("Non-JSON response from %s: %s", url, text)
                    raise LocknAlertInvalidResponse("Expected JSON response") from err

        except ClientError as err:
            raise LocknAlertCannotConnect from err

        if not isinstance(data, dict):
            _LOGGER.debug("Unexpected response type from %s: %s", url, type(data))
            raise LocknAlertInvalidResponse("Expected JSON object")

        _LOGGER.debug("Received response from %s: keys=%s", url, list(data.keys()))
        return data

    async def async_get_info(self, session: ClientSession) -> dict[str, Any]:
        """Fetch bridge identity and capabilities."""
        return await self._request(session, "GET", "/api/info")

    async def async_pair(
        self,
        session: ClientSession,
        serial_number: str,
    ) -> dict[str, Any]:
        """Pair with the bridge using the unit serial number."""
        return await self._request(
            session,
            "POST",
            "/api/pair",
            json_data={"serial_number": serial_number},
        )

    async def async_get_mqtt_bootstrap(
        self,
        session: ClientSession,
        serial_number: str,
    ) -> dict[str, Any]:
        """Fetch MQTT host, credentials, and topic prefix."""
        bootstrap = await self._request(
            session,
            "POST",
            "/api/mqtt/bootstrap",
            json_data={"serial_number": serial_number},
        )

        required = {"host", "port", "username", "password"}

        if not required.issubset(bootstrap):
            missing = required - set(bootstrap)
            _LOGGER.debug(
                "Invalid MQTT bootstrap payload: missing=%s payload_keys=%s",
                missing,
                list(bootstrap.keys()),
            )
            raise LocknAlertInvalidResponse("Missing required MQTT fields")

        safe_bootstrap = {
            key: "<redacted>" if key == "password" else value
            for key, value in bootstrap.items()
        }
        _LOGGER.debug("MQTT bootstrap received: %s", safe_bootstrap)

        return bootstrap

    async def async_bootstrap(
        self,
        session: ClientSession,
        serial_number: str,
    ) -> dict[str, Any]:
        """Validate bridge identity and fetch MQTT credentials."""
        await self.async_get_info(session)
        return await self.async_get_mqtt_bootstrap(session, serial_number)