"""API client for Octopus Energy Japan GraphQL API."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

import aiohttp

from .const import (
    API_URL,
    QUERY_OBTAIN_TOKEN,
    QUERY_REFRESH_TOKEN,
    QUERY_ACCOUNT_VIEWER,
    QUERY_HALF_HOURLY_READINGS,
)

_LOGGER = logging.getLogger(__name__)


class OctopusEnergyJPApiError(Exception):
    """Base exception for API errors."""


class OctopusEnergyJPAuthError(OctopusEnergyJPApiError):
    """Authentication error."""


class OctopusEnergyJPConnectionError(OctopusEnergyJPApiError):
    """Connection error."""


class OctopusEnergyJPApi:
    """API client for Octopus Energy Japan."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        email: str,
        password: str,
    ) -> None:
        """Initialize the API client."""
        self._session = session
        self._email = email
        self._password = password
        self._token: str | None = None
        self._refresh_token: str | None = None
        self._account_number: str | None = None

    async def _execute_query(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
        authenticated: bool = True,
        retry_on_auth_error: bool = True,
    ) -> dict[str, Any]:
        """Execute a GraphQL query."""
        headers = {"Content-Type": "application/json"}
        
        if authenticated and self._token:
            headers["Authorization"] = f"JWT {self._token}"

        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        try:
            async with self._session.post(
                API_URL,
                json=payload,
                headers=headers,
            ) as response:
                if response.status != 200:
                    text = await response.text()
                    _LOGGER.error("API request failed: %s - %s", response.status, text)
                    raise OctopusEnergyJPApiError(f"API request failed: {response.status}")
                
                result = await response.json()
                
                if "errors" in result:
                    error_message = result["errors"][0].get("message", "Unknown error")
                    
                    # Check if the error is due to JWT expiration
                    if "expired" in error_message.lower() and authenticated and retry_on_auth_error:
                        _LOGGER.debug("JWT token expired, attempting to refresh")
                        if await self._refresh_or_reauthenticate():
                            # Retry the query with the new token
                            return await self._execute_query(
                                query, variables, authenticated, retry_on_auth_error=False
                            )
                    
                    _LOGGER.error("GraphQL error: %s", error_message)
                    raise OctopusEnergyJPApiError(error_message)
                
                return result.get("data", {})
                
        except aiohttp.ClientError as err:
            _LOGGER.error("Connection error: %s", err)
            raise OctopusEnergyJPConnectionError(f"Connection error: {err}") from err

    async def _refresh_or_reauthenticate(self) -> bool:
        """Try to refresh the token, or re-authenticate if refresh fails."""
        # First, try to refresh the token
        if self._refresh_token:
            try:
                await self._refresh_access_token()
                return True
            except OctopusEnergyJPApiError:
                _LOGGER.debug("Token refresh failed, attempting full re-authentication")
        
        # If refresh fails or no refresh token, try full re-authentication
        try:
            await self.authenticate()
            return True
        except OctopusEnergyJPAuthError:
            _LOGGER.error("Re-authentication failed")
            return False

    async def _refresh_access_token(self) -> None:
        """Refresh the access token using the refresh token."""
        if not self._refresh_token:
            raise OctopusEnergyJPAuthError("No refresh token available")

        variables = {"refreshToken": self._refresh_token}

        try:
            # Execute without authentication since we're refreshing
            headers = {"Content-Type": "application/json"}
            payload = {"query": QUERY_REFRESH_TOKEN, "variables": variables}

            async with self._session.post(
                API_URL,
                json=payload,
                headers=headers,
            ) as response:
                if response.status != 200:
                    raise OctopusEnergyJPAuthError("Token refresh request failed")
                
                result = await response.json()
                
                if "errors" in result:
                    error_message = result["errors"][0].get("message", "Unknown error")
                    raise OctopusEnergyJPAuthError(f"Token refresh failed: {error_message}")
                
                token_data = result.get("data", {}).get("refreshKrakenToken")
                if not token_data or not token_data.get("token"):
                    raise OctopusEnergyJPAuthError("Failed to refresh token")
                
                self._token = token_data["token"]
                self._refresh_token = token_data.get("refreshToken", self._refresh_token)
                
                _LOGGER.debug("Successfully refreshed access token")

        except aiohttp.ClientError as err:
            raise OctopusEnergyJPConnectionError(f"Connection error during refresh: {err}") from err

    async def authenticate(self) -> bool:
        """Authenticate with email and password to obtain JWT token."""
        variables = {
            "input": {
                "email": self._email,
                "password": self._password,
            }
        }

        try:
            data = await self._execute_query(
                QUERY_OBTAIN_TOKEN,
                variables,
                authenticated=False,
            )
            
            token_data = data.get("obtainKrakenToken")
            if not token_data or not token_data.get("token"):
                raise OctopusEnergyJPAuthError("Failed to obtain token")
            
            self._token = token_data["token"]
            self._refresh_token = token_data.get("refreshToken")
            
            _LOGGER.debug("Successfully authenticated")
            return True
            
        except OctopusEnergyJPApiError as err:
            _LOGGER.error("Authentication failed: %s", err)
            raise OctopusEnergyJPAuthError(f"Authentication failed: {err}") from err

    async def get_account_number(self) -> str:
        """Get the account number for the authenticated user."""
        if self._account_number:
            return self._account_number

        if not self._token:
            await self.authenticate()

        data = await self._execute_query(QUERY_ACCOUNT_VIEWER)
        
        accounts = data.get("viewer", {}).get("accounts", [])
        if not accounts:
            raise OctopusEnergyJPApiError("No accounts found")
        
        self._account_number = accounts[0]["number"]
        _LOGGER.debug("Account number: %s", self._account_number)
        return self._account_number

    async def get_half_hourly_readings(
        self,
        from_datetime: datetime | None = None,
        to_datetime: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """Get half-hourly electricity readings."""
        if not self._token:
            await self.authenticate()

        account_number = await self.get_account_number()

        # Default to last 48 hours if not specified
        if to_datetime is None:
            to_datetime = datetime.now()
        if from_datetime is None:
            from_datetime = to_datetime - timedelta(hours=48)

        variables = {
            "accountNumber": account_number,
            "fromDatetime": from_datetime.isoformat(),
            "toDatetime": to_datetime.isoformat(),
        }

        data = await self._execute_query(QUERY_HALF_HOURLY_READINGS, variables)

        # Extract readings from nested structure
        readings = []
        properties = data.get("account", {}).get("properties", [])
        
        for prop in properties:
            supply_points = prop.get("electricitySupplyPoints", [])
            for supply_point in supply_points:
                hh_readings = supply_point.get("halfHourlyReadings", [])
                readings.extend(hh_readings)

        _LOGGER.debug("Retrieved %d readings", len(readings))
        return readings

    @property
    def token(self) -> str | None:
        """Return the current JWT token."""
        return self._token

    @property
    def account_number(self) -> str | None:
        """Return the account number."""
        return self._account_number
