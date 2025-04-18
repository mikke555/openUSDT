import random

from eth_abi import encode

import settings
from modules.config import HYPERLANE_DOMAINS, HYPERLANE_ROUTER, OUSDT, XERC20_ABI
from modules.logger import logger
from modules.wallet import Wallet


class HypXERC20(Wallet):
    def __init__(self, pk, _id, proxy, chain):
        super().__init__(pk, _id, chain)
        self.label += "OpenUSDT |"
        self.router = self.get_contract(HYPERLANE_ROUTER[self.chain.name], abi=XERC20_ABI)

    @property
    def local_domain(self) -> int:
        return self.router.functions.localDomain().call()

    def get_random_dest(self) -> tuple:
        """Select a random destination from AVAILABLE_CHAINS, excluding current chain."""
        available_destinations = [
            (name, id)
            for name, id in HYPERLANE_DOMAINS.items()
            if name in settings.AVAILABLE_CHAINS and id != self.local_domain
        ]
        if not available_destinations:
            raise ValueError("No available destination chains")

        return random.choice(available_destinations)[0]

    def get_dest_id_by_name(self, dest_name: str) -> int:
        return HYPERLANE_DOMAINS.get(dest_name.lower())

    def _quote_gas(self, dest_id: int) -> int:
        return self.router.functions.quoteGasPayment(dest_id).call()

    def _encode_recipient(self) -> bytes:
        return encode(["address"], [self.address])

    def _get_network_name_by_id(self, _id: int) -> str:
        for network_name, id in HYPERLANE_DOMAINS.items():
            if id == _id:
                return network_name
        return None

    def transfer_remote(self, dest_id, token_in=OUSDT):
        """Function: transferRemote(uint32 _destination,bytes32 _recipient,uint256 _amountOrId)"""
        balance, decimals, symbol = self.get_token_info(token_in)

        if balance == 0:
            logger.warning(f"{self.label} No balance to transfer \n")
            return False

        amount_in = balance
        value = self._quote_gas(dest_id)
        recipient = self._encode_recipient()

        self.approve(token_in, self.router.address, amount_in)

        contract_tx = self.router.functions.transferRemote(dest_id, recipient, balance).build_transaction(
            self.get_tx_data(value=value)
        )

        src_chain = self._get_network_name_by_id(self.local_domain)
        dest_chain = self._get_network_name_by_id(dest_id)

        status = self.send_tx(
            contract_tx,
            tx_label=f"{self.label} Bridge {amount_in / 10**decimals:.4f} {symbol} {src_chain.title()} -> {dest_chain.title()}",
            gas_multiplier=1.2,
        )

        if not status:
            return False

        return self.await_token_balance(OUSDT, chain_name=dest_chain)
