import random

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)
from web3 import constants

import settings
from modules.config import OUSDT
from modules.http import HttpClient
from modules.utils import ether, wei
from modules.wallet import Wallet


class OdosQuoteError(Exception):
    pass


class Odos(Wallet):
    BASE_URL = "https://api.odos.xyz"

    def __init__(self, pk, _id, proxy, chain):
        super().__init__(pk, _id, chain)
        self.label += "ODOS |"
        self.http = HttpClient(self.BASE_URL, proxy)

    @retry(
        stop=stop_after_attempt(10),
        wait=wait_exponential(multiplier=1, max=60),
        retry=retry_if_exception_type(OdosQuoteError),
    )
    def _quote(self, token_in, token_out, amount_in):
        payload = {
            "chainId": self.w3.eth.chain_id,
            "inputTokens": [
                {
                    "tokenAddress": token_in,
                    "amount": str(amount_in),
                },
            ],
            "outputTokens": [
                {
                    "tokenAddress": token_out,
                    "proportion": 1,
                },
            ],
            "userAddr": self.address,
            "slippageLimitPercent": 1,
            "sourceBlacklist": [],
            "pathViz": True,
            "referralCode": 1,
            "compact": True,
            "likeAsset": True,
            "disableRFQs": False,
        }

        resp = self.http.post("/sor/quote/v2", json=payload)

        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 500 and "Error getting quote" in resp.text:
            raise OdosQuoteError(f"Error getting quote: {resp.status_code} {resp.text}")
        else:
            raise Exception(f"Failed to fetch quote: {resp.status_code} {resp.text}")

    def _assemble(self, path_id):
        payload = {
            "userAddr": self.address,
            "pathId": path_id,
            "simulate": True,
        }

        resp = self.http.post("/sor/assemble", json=payload)

        if resp.status_code != 200:
            raise Exception(f"Failed to assemble tx: {resp.status_code} {resp.text}")

        return resp.json()

    def swap_eth(self, token_in: str = constants.ADDRESS_ZERO, token_out: str = OUSDT):
        amount_in = wei(random.uniform(*settings.SWAP_AMOUNT))

        quote = self._quote(token_in, token_out, amount_in)
        transaction = self._assemble(quote["pathId"])["transaction"]

        tx = self.get_tx_data(
            value=amount_in,
            to=transaction["to"],
            data=transaction["data"],
            get_gas=True,
        )

        return self.send_tx(
            tx,
            tx_label=f"{self.label} Swap {ether(amount_in):.6f} ETH -> {quote['netOutValue']:.4f} oUSDT",
            gas_multiplier=1.2,
        )

    def swap_erc20(self, token_in: str = OUSDT, token_out: str = constants.ADDRESS_ZERO):
        balance, decimals, symbol = self.get_token_info(token_in)
        amount_in = int(balance * random.uniform(*settings.SWAP_BACK_PERCENTAGE))

        quote = self._quote(token_in, token_out, amount_in)
        transaction = self._assemble(quote["pathId"])["transaction"]

        self.approve(token_in, transaction["to"], amount_in)

        tx = self.get_tx_data(
            value=amount_in,
            to=transaction["to"],
            data=transaction["data"],
            get_gas=True,
        )

        amount_out = quote["pathViz"]["links"][-1]["out_value"]
        return self.send_tx(
            tx,
            tx_label=f"{self.label} Swap {amount_in / 10**decimals:.4f} {symbol} -> {amount_out:.6f} ETH",
            gas_multiplier=1.2,
        )
