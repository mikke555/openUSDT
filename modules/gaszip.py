import random

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

import settings
from models.network import Network
from modules.config import GASZIP_DIRECT_DEPOSIT_ADDRESS
from modules.http import HttpClient
from modules.logger import logger
from modules.utils import get_token_price, wei
from modules.wallet import Wallet


class PendingStatus(Exception):
    pass


class GasZip(Wallet):
    BASE_URL = "https://backend.gas.zip/v2"

    def __init__(self, pk, _id, proxy, chain, dest_chain):
        super().__init__(pk, _id, chain)
        self.label += "Gas.zip |"
        self.http = HttpClient(self.BASE_URL, proxy)

        self.src_chain: Network = self.chain
        self.dest_chain: str = dest_chain

    @property
    def amount(self) -> float:
        return random.uniform(*settings.REFUEL_AMOUNT)

    def _validate_amount(self) -> int:
        eth_price = get_token_price("ETH")
        amount_usd = self.amount * eth_price

        if amount_usd < 0.26 or amount_usd > 50.00:
            raise ValueError("Refuel amount falls outside Gas.zip limits: $0.25 - $50.00")

        return wei(self.amount)

    def _quote(self, amount: int, dest_chain_id: int) -> dict:
        url = f"/quotes/{self.chain.chain_id}/{amount}/{dest_chain_id}"
        resp = self.http.get(url, params={"to": self.address, "from": self.address})

        return resp.json()

    def _verify_deposit(self, tx_hash: str) -> bool:
        endpoint = f"/deposit/0x{tx_hash}"
        logger.info(f"{self.label} {self.http.base_url}{endpoint}")

        try:
            return self._check_deposit_status(endpoint)
        except PendingStatus:
            raise Exception("Deposit not confirmed after max attempts")

    @retry(stop=stop_after_attempt(10), wait=wait_fixed(5), retry=retry_if_exception_type(PendingStatus))
    def _check_deposit_status(self, endpoint):
        data = self.http.get(endpoint).json()

        if "deposit" in data and "status" in data["deposit"]:
            status = data["deposit"]["status"]
            usd_value = data["deposit"]["usd"]

            if status == "CONFIRMED":
                logger.debug(f"{self.label} Status <CONFIRMED>")
                logger.debug(f"{self.label} ${usd_value:.2f} in ETH received on {self.dest_chain.title()} \n")
                return True
            else:
                logger.info(f"{self.label} Status <{status.upper()}>")
                raise PendingStatus(f"Status is {status}")
        else:
            raise PendingStatus("Response does not contain 'deposit' or 'status'")

    def refuel(self):
        if self.src_chain is None or self.dest_chain is None:
            quit()

        amount = self._validate_amount()
        to_chain = self.get_chain_by_name(self.dest_chain)
        quote = self._quote(amount, to_chain.chain_id)

        tx = self.get_tx_data(
            value=amount,
            to=GASZIP_DIRECT_DEPOSIT_ADDRESS,
            data=quote["calldata"],
            get_gas=True,
        )

        self._verify_deposit(
            self.send_tx(
                tx,
                tx_label=f"{self.label} Refuel {self.amount:.6f} ETH {self.chain.name.title()} -> {to_chain.name.title()}",
                gas_multiplier=1.2,
            )
        )
