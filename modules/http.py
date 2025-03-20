import requests
from fake_useragent import UserAgent

from modules.utils import retry


class HttpClient(requests.Session):
    def __init__(self, base_url="", proxy=None):
        super().__init__()
        self.proxy = proxy
        self.base_url = base_url
        self.headers.update({"User-Agent": UserAgent().random})

        if proxy:
            self.proxies.update({"http": proxy, "https": proxy})

    @retry(retries=3, delay=10)
    def _request(self, method, endpoint, *args, **kwargs):
        url = f"{self.base_url}{endpoint}"
        resp = super().request(method, url, *args, **kwargs)

        if resp.status_code not in [200, 201]:
            raise Exception(f"{resp.status_code} {resp.text}")

        return resp

    def get(self, endpoint, *args, **kwargs):
        return self._request("GET", endpoint, *args, **kwargs)

    def post(self, endpoint, *args, **kwargs):
        return self._request("POST", endpoint, *args, **kwargs)
