import random

import questionary

import settings

from .config import q_style
from .gaszip import GasZip
from .logger import logger
from .odos import Odos
from .utils import random_sleep
from .velodrome import Velodrome
from .wallet import Wallet
from .xerc20 import HypXERC20


class Action:
    def __init__(self, method_name: str):
        self.method_name = method_name

    def __call__(self, account: dict) -> bool:
        handler = ActionHandler(account)
        method = getattr(handler, self.method_name, None)

        if method is None:
            raise AttributeError(f"No such method: {self.method_name}")

        return method()


class ActionHandler:
    def __init__(self, account):
        self.account = account
        self.current_chain = None

    def get_random_dex(self, chain):
        """Select a random DEX for the given chain."""
        dex_list = [Velodrome, Odos]
        return random.choice(dex_list)(**self.account, chain=chain)

    def swap(self, chain="base", to_eth=False):
        """Perform a swap on the specified chain."""
        dex = self.get_random_dex(chain)
        return dex.swap_erc20() if to_eth else dex.swap_eth()

    def ensure_sufficient_gas(self, dest_chain: str) -> None:
        """Ensure the destination chain has sufficient gas."""
        wallet = Wallet(pk=self.account["pk"], _id=self.account["_id"], chain=dest_chain)
        refuel_src = random.choice(settings.GASZIP_REFUEL_SOURCE)

        if wallet.get_balance(human=True) < settings.MIN_GAS_BALANCE:
            GasZip(**self.account, chain=refuel_src).refuel(dest_chain)
            random_sleep(*settings.SLEEP_BETWEEN_ACTIONS)

    def bridge(self, chain, dest_name=None):
        """Bridge tokens to a random destination after ensuring sufficient gas."""
        try:
            bridge = HypXERC20(**self.account, chain=chain)

            dest_name = dest_name or bridge.get_random_dest()
            dest_id = bridge.get_dest_id_by_name(dest_name)

            self.ensure_sufficient_gas(dest_name)

            return dest_name if bridge.transfer_remote(dest_id) else False

        except Exception as e:
            logger.error(f"Error during transfer from {chain}: {e}")
            return False

    def perform_initial_swap(self) -> bool:
        """Perform the initial swap on a random starting chain."""
        self.current_chain = random.choice(settings.STARTING_CHAIN)
        return self.swap(chain=self.current_chain)

    def perform_intermediate_bridges(self, hops: int) -> bool:
        """Perform intermediate bridges across chains."""
        for _ in range(hops - 1):
            next_dest = self.bridge(self.current_chain)

            if not next_dest:
                return False

            self.current_chain = next_dest
            random_sleep(*settings.SLEEP_BETWEEN_ACTIONS)
        return True

    def perform_final_bridge_and_swap(self) -> bool:
        """Bridge to final destination and swap to ETH."""
        match self.current_chain:
            case "base":
                final_dest = "optimism"
            case "optimism":
                final_dest = "base"
            case _:
                final_dest = random.choice(["base", "optimism"])

        self.current_chain = self.bridge(self.current_chain, dest_name=final_dest)

        if not self.current_chain:
            return False

        random_sleep(*settings.SLEEP_BETWEEN_ACTIONS)
        return self.swap(chain=final_dest, to_eth=True)

    def swap_and_bridge(self) -> bool:
        """Perform a sequence of swaps and bridges."""
        hops = random.randint(*settings.HOPS)

        if not self.perform_initial_swap():
            return False
        random_sleep(*settings.SLEEP_BETWEEN_ACTIONS)

        if hops > 1 and not self.perform_intermediate_bridges(hops):
            return False

        return self.perform_final_bridge_and_swap()

    def swap_eth_to_ousdt(self):
        """Prompt user for chain and swap ETH to oUSDT."""
        chain = questionary.select("Swap ETH -> oUSDT:", choices=["base", "optimism"], style=q_style).ask()
        if chain is None:
            quit()

        return self.swap(chain=chain, to_eth=False)

    def swap_ousdt_to_eth(self):
        """Prompt user for chain and swap oUSDT to ETH."""
        chain = questionary.select("Swap oUSDT -> ETH:", choices=["base", "optimism"], style=q_style).ask()
        if chain is None:
            quit()

        return self.swap(chain=chain, to_eth=True)
