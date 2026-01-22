"""Constants for the Octopus Energy Japan integration."""

DOMAIN = "octopus_energy_jp"

# API Configuration
API_URL = "https://api.oejp-kraken.energy/v1/graphql/"

# Config keys
CONF_EMAIL = "email"
CONF_PASSWORD = "password"
CONF_ACCOUNT_NUMBER = "account_number"

# Default values
DEFAULT_SCAN_INTERVAL = 30  # minutes

# GraphQL Queries
QUERY_OBTAIN_TOKEN = """
mutation obtainKrakenToken($input: ObtainJSONWebTokenInput!) {
  obtainKrakenToken(input: $input) {
    token
    refreshToken
    refreshExpiresIn
    payload
  }
}
"""

QUERY_ACCOUNT_VIEWER = """
query accountViewer {
  viewer {
    accounts {
      number
    }
  }
}
"""

QUERY_HALF_HOURLY_READINGS = """
query halfHourlyReadings($accountNumber: String!, $fromDatetime: DateTime, $toDatetime: DateTime) {
  account(accountNumber: $accountNumber) {
    properties {
      electricitySupplyPoints {
        halfHourlyReadings(fromDatetime: $fromDatetime, toDatetime: $toDatetime) {
          startAt
          endAt
          value
        }
      }
    }
  }
}
"""

QUERY_REFRESH_TOKEN = """
mutation refreshKrakenToken($refreshToken: String!) {
  refreshKrakenToken(refreshToken: $refreshToken) {
    token
    refreshToken
    refreshExpiresIn
  }
}
"""
