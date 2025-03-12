import requests
from fake_useragent import UserAgent


class HttpClient(requests.Session):
    def __init__(self, base_url="", proxy=None):
        super().__init__()
        self.proxy = proxy
        self.base_url = base_url
        self.headers.update({"User-Agent": UserAgent().random})

        if proxy:
            self.proxies.update({"http": proxy, "https": proxy})

    def __exit__(self):
        self.close()

    def _request(self, method, endpoint, *args, **kwargs):
        url = f"{self.base_url}{endpoint}"
        return super().request(method, url, *args, **kwargs)

    def get(self, endpoint, *args, **kwargs):
        return self._request("GET", endpoint, *args, **kwargs)

    def post(self, endpoint, *args, **kwargs):
        return self._request("POST", endpoint, *args, **kwargs)
