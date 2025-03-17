import random
import time

import settings
from modules.config import GASZIP_DIRECT_DEPOSIT_ADDRESS
from modules.http import HttpClient
from modules.logger import logger
from modules.utils import get_token_price, wei
from modules.wallet import Wallet


class GasZip(Wallet):
    BASE_URL = "https://backend.gas.zip/v2"

    def __init__(self, pk, _id, proxy, chain):
        super().__init__(pk, _id, chain)
        self.label += "Gas.zip |"
        self.http = HttpClient(self.BASE_URL, proxy)

    @property
    def amount(self):
        return random.uniform(*settings.GASZIP_REFUEL_AMOUNT)

    def _validate_amount(self):
        eth_price = get_token_price("ETH")
        amount_usd = self.amount * eth_price

        if amount_usd < 0.26 or amount_usd > 50.00:
            raise ValueError("Refuel amount falls outside Gas.zip limits: $0.25 - $50.00")

        return wei(self.amount)

    def _get_quote(self, amount, dest_chain_id):
        resp = self.http.get(
            f"/quotes/{self.chain.chain_id}/{amount}/{dest_chain_id}",
            params={"to": self.address, "from": self.address},
        )

        if resp.status_code != 200:
            raise Exception(f"Failed to fetch quote: {resp.status_code} {resp.text}")

        return resp.json()

    def _verify_deposit(self, tx_hash):
        url = f"/deposit/0x{tx_hash}"

        while True:
            data = self.http.get(url).json()
            if "deposit" in data and "status" in data["deposit"]:
                break
            time.sleep(5)

        for _ in range(5):
            data = self.http.get(url).json()

            if data["deposit"]["status"] == "CONFIRMED":
                logger.debug(f"{self.label} ${data['deposit']['usd']:.2f} of gas received \n")
                return
            time.sleep(5)

        logger.warning(f"{self.label} Deposit status: <{data['deposit']['status']}>")
        raise Exception("Deposit not confirmed after 5 attempts")

    def refuel(self, dest_name: str):
        to_chain = self.get_chain_by_name(dest_name)
        amount = self._validate_amount()
        quote = self._get_quote(amount, to_chain.chain_id)

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
