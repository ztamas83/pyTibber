"""Library to handle connection with Tibber API."""
import logging

import asyncio
import aiohttp
import async_timeout
from gql import gql
from graphql.language.printer import print_ast

DEFAULT_TIMEOUT = 10
DEMO_TOKEN = 'd1007ead2dc84a2b82f0de19451c5fb22112f7ae11d19bf2bedb224a003ff74a'
API_ENDPOINT = 'https://api.tibber.com/v1-beta/gql'
_LOGGER = logging.getLogger(__name__)


class Tibber(object):
    """Class to comunicate with the Tibber api."""

    def __init__(self, access_token=DEMO_TOKEN,
                 timeout=DEFAULT_TIMEOUT,
                 websession=aiohttp.ClientSession()):
        """Initialize the Tibber connection."""
        self.websession = websession
        self._timeout = timeout
        self._headers = {'Authorization': 'Bearer ' + access_token}
        self._name = None
        self._home_ids = []
        self._homes = {}

    @asyncio.coroutine
    def _execute(self, document, variable_values=None):
        query_str = print_ast(document)
        payload = {
            'query': query_str,
            'variables': variable_values or {}
        }

        post_args = {
            'headers': self._headers,
            'data': payload
        }

        try:
            with async_timeout.timeout(self._timeout):
                resp = yield from self.websession.post(API_ENDPOINT,
                                                       **post_args)
            if resp.status != 200:
                return
            result = yield from resp.json()
        except (asyncio.TimeoutError, aiohttp.ClientError) as err:
            _LOGGER.warning("Error connecting to Tibber: %s", err)
            return
        assert 'errors' in result or 'data' in result,\
            'Received non-compatible response "{}"'.format(result)
        return result.get('data')

    @asyncio.coroutine
    def update_info(self, *_):
        """Update home info."""
        query = gql('''
        {
          viewer {
            name
            homes {
              id
            }
          }
        }
        ''')

        res = yield from self._execute(query)
        viewer = res.get('viewer')
        if not viewer:
            return
        self._name = viewer.get('name')
        homes = viewer.get('homes', [])
        for _home in homes:
            home_id = _home.get('id')
            if not home_id:
                continue
            self._home_ids += [home_id]

    @property
    def name(self):
        """Return name of user."""
        return self._name

    @property
    def home_ids(self):
        """Return list of home ids."""
        return self._home_ids

    def get_homes(self):
        """Return list of Tibber homes."""
        return [self.get_home(home_id) for home_id in self.home_ids]

    def get_home(self, home_id):
        """Retun an instance of TibberHome for given home id."""
        if home_id not in self._home_ids:
            _LOGGER.warning("Could not find any Tibber home with id: %s",
                            home_id)
            return None
        if home_id not in self._homes.keys():
            self._homes[home_id] = TibberHome(home_id, self._execute)
        return self._homes[home_id]


class TibberHome(object):
    """Instance of Tibber home."""

    def __init__(self, home_id, execute):
        """Initialize the Tibber home class."""
        self._execute = execute
        self._home_id = home_id
        self._current_price_total = None
        self._current_price_info = {}
        self.info = {}

    @asyncio.coroutine
    def update_info(self):
        """Update current price info."""
        query = gql('''
        {
          viewer {
            home(id: "%s") {
              address {
                address1
                address2
                address3
                city
                postalCode
                country
                latitude
                longitude
              }
              meteringPointData {
                consumptionEan
                gridCompany
                productionEan
                energyTaxType
                vatType
              }
              owner {
                name
                isCompany
                language
                contactInfo {
                  email
                  mobile
                }
              }
              timeZone
              subscriptions {
                id
                status
                validFrom
                validTo
                statusReason
              }
            }
          }
        }
        ''' % (self._home_id))
        self.info = yield from self._execute(query)

    @asyncio.coroutine
    def update_current_price_info(self):
        """Update current price info."""
        query = gql('''
        {
          viewer {
            home(id: "%s") {
              currentSubscription {
                priceInfo {
                  current {
                    energy
                    tax
                    total
                    startsAt
                  }
                }
              }
            }
          }
        }
        ''' % (self.home_id))
        price_info_temp = yield from self._execute(query)
        print(price_info_temp)
        if not price_info_temp:
            return
        try:
            home = price_info_temp['viewer']['home']
            current_subscription = home['currentSubscription']
            price_info = current_subscription['priceInfo']['current']
        except KeyError:
            return
        self._current_price_info = price_info

    @property
    def current_price_total(self):
        """Get current price total."""
        return self._current_price_info.get('total')

    @property
    def current_price_info(self):
        """Get current price info."""
        return self._current_price_info

    @property
    def home_id(self):
        """Return home id."""
        return self._home_id

    @property
    def address1(self):
        """Return the home adress1."""
        try:
            return self.info['viewer']['home']['address']['address1']
        except KeyError:
            _LOGGER.warning("Could not find address1.")
            return None