import random
import time

from web3 import constants

import settings
from models.network import Network
from models.responses.relay.quote import Quote
from modules.http import HttpClient
from modules.logger import logger
from modules.utils import wei
from modules.wallet import Wallet


class Relay(Wallet):
    BASE_URL = "https://api.relay.link"

    def __init__(self, pk, _id, proxy, chain, dest_chain):
        super().__init__(pk, _id, chain)
        self.label += "Relay |"
        self.http = HttpClient(self.BASE_URL, proxy)

        self.src_chain: Network = self.chain
        self.dest_chain: str = dest_chain

    @property
    def amount(self):
        return random.uniform(*settings.REFUEL_AMOUNT)

    def _quote(self, dest_id: int) -> Quote:
        payload = {
            "user": self.address,
            "originChainId": self.chain.chain_id,
            "destinationChainId": dest_id,
            "originCurrency": constants.ADDRESS_ZERO,
            "destinationCurrency": constants.ADDRESS_ZERO,
            "recipient": self.address,
            "tradeType": "EXACT_INPUT",
            "amount": str(wei(self.amount)),
            "referrer": "relay.link/swap",
            "useExternalLiquidity": False,
            "useDepositAddress": False,
        }

        resp = self.http.post("/quote", json=payload)
        return Quote(**resp.json())

    def _verify_deposit(self, request_id: str, max_attempts: int = 10) -> None:
        endpoint = f"/intents/status?requestId={request_id}"
        logger.info(f"{self.label} {self.http.base_url}{endpoint}")

        for _ in range(max_attempts):
            resp = self.http.get(endpoint)
            data = resp.json()

            if "status" in data:
                status = data["status"]
                if status == "success":
                    logger.debug(f"{self.label} Status <{status.upper()}>")
                    return
                else:
                    logger.info(f"{self.label} Status <{status.upper()}>")
            time.sleep(10)

        raise Exception(f"Deposit not confirmed after {max_attempts} attempts")

    def _get_receipt(self, id: str, max_attempts: int = 10) -> None:
        endpoint = f"/requests/v2?id={id}"

        for _ in range(max_attempts):
            resp = self.http.get(endpoint)
            data = resp.json()

            if "requests" in data:
                amount_usd = float(data["requests"][0]["data"]["metadata"]["currencyOut"]["amountUsd"])
                logger.debug(f"{self.label} ${amount_usd:.2f} in ETH received on {self.dest_chain.title()}\n")
                return
            time.sleep(10)

        raise Exception(f"Couldn't get a receipt after {max_attempts} attempts")

    def refuel(self) -> bool:
        to_chain = self.get_chain_by_name(self.dest_chain)
        quote = self._quote(dest_id=to_chain.chain_id)

        if not quote.steps or not quote.steps[0].items:
            raise ValueError("Invalid quote response: missing steps or items")

        tx_data = quote.steps[0].items[0].data
        tx = {
            "from": self.address,
            "to": self.w3.to_checksum_address(tx_data.to),
            "nonce": self.w3.eth.get_transaction_count(self.address),
            "chainId": self.chain.chain_id,
            "value": int(tx_data.value),
            "data": tx_data.data,
            "gas": int(tx_data.gas),
            "maxFeePerGas": int(tx_data.maxFeePerGas),
            "maxPriorityFeePerGas": int(tx_data.maxPriorityFeePerGas),
        }

        tx_status = self.send_tx(
            tx,
            tx_label=f"{self.label} Refuel {self.amount:.6f} ETH {self.chain.name.title()} -> {to_chain.name.title()}",
        )

        if tx_status:
            self._verify_deposit(quote.steps[0].requestId)
            self._get_receipt(quote.steps[0].requestId)
            return True

        return False
