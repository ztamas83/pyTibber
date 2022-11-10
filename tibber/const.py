"""Constants used by pyTibber"""

from __future__ import annotations

from http import HTTPStatus
from typing import Final

__version__ = "0.25.7b"

RESOLUTION_HOURLY: Final = "HOURLY"
RESOLUTION_DAILY: Final = "DAILY"
RESOLUTION_WEEKLY: Final = "WEEKLY"
RESOLUTION_MONTHLY: Final = "MONTHLY"
RESOLUTION_ANNUAL: Final = "ANNUAL"

DEMO_TOKEN: Final = "5K4MVS-OjfWhK_4yrjOlFe1F6kJXPVf7eQYggo8ebAE"
API_ENDPOINT: Final = "https://api.tibber.com/v1-beta/gql"

API_ERR_UNAUTH = "UNAUTHENTICATED"
HTTP_CODES_RETRIABLE = [HTTPStatus.TOO_MANY_REQUESTS, HTTPStatus.PRECONDITION_REQUIRED]
HTTP_CODES_FATAL = [HTTPStatus.BAD_REQUEST]
