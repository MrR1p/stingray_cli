import requests
import json
from stingray.base import StingrayBase


class StingrayAPI(StingrayBase):
    """
    Class for interact with Stingray system through REST API
    """

    def __init__(self, base_url, login, password):
        super().__init__(base_url)
        self.headers = {}
        self.login = login
        self.password = password
        self.current_context = {}

        self._auth()
        self._current_context()

    def _auth(self):
        """
        Get method for Stingray REST API.
        Made 3 attempts before fail the script
        :return: response
        """
        self.headers['Content-Type'] = 'application/json'
        payload = {'username': self.login, 'password': self.password}

        resp = requests.post(f'{self.url}/login/', headers=self.headers, data=json.dumps(payload, indent=4))
        resp_body = resp.json()

        self.headers['Authorization'] = 'Bearer {0}'.format(resp_body['access'])

    def _current_context(self):
        current_context_resp = requests.get(f'{self.url}/currentuser/', headers=self.headers)
        self.current_context = current_context_resp.json()