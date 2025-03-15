import random

import questionary

import settings
from modules.config import q_style

from .logger import logger
from .odos import Odos
from .utils import random_sleep
from .velodrome import Velodrome
from .xerc20 import HypXERC20


class ActionHandler:
    def __init__(self, account):
        self.account = account
        self.current_chain = None

    def get_random_dex(self, chain):
        """Helper method to select a random DEX."""
        return Velodrome(**self.account, chain=chain) if random.randint(0, 1) else Odos(**self.account, chain=chain)

    def swap(self, chain="base", to_eth=False):
        """Perform a swap on the specified chain."""
        dex = self.get_random_dex(chain)
        return dex.swap_erc20() if to_eth else dex.swap_eth()

    def bridge(self, chain, dest_name=None):
        """Bridge tokens to a destination chain."""
        try:
            bridge = HypXERC20(**self.account, chain=chain)
            if dest_name:
                dest_id = bridge.get_dest_id_by_name(dest_name)
            else:
                dest_name, dest_id = bridge.get_random_dest()

            if not bridge.transfer_remote(dest_id):
                return False

            return dest_name
        except Exception as e:
            logger.error(f"Error during transfer from {chain}: {e}")
            return False

    def swap_and_bridge(self):
        """Perform a sequence of swaps and bridges."""
        hops = random.randint(*settings.HOPS)
        self.current_chain = random.choice(settings.STARTING_CHAIN)

        if not self.swap(chain=self.current_chain):
            return False
        random_sleep(*settings.SLEEP_BETWEEN_ACTIONS)

        for _ in range(hops - 1):
            next_dest = self.bridge(self.current_chain)
            if not next_dest:
                return False

            self.current_chain = next_dest
            random_sleep(*settings.SLEEP_BETWEEN_ACTIONS)

        final_options = ["base", "optimism"]
        match self.current_chain:
            case "base":
                final_dest = "optimism"
            case "optimism":
                final_dest = "base"
            case _:
                final_dest = random.choice(final_options)

        self.bridge(self.current_chain, dest_name=final_dest)
        random_sleep(*settings.SLEEP_BETWEEN_ACTIONS)

        if not self.swap(chain=final_dest, to_eth=True):
            return False

        return True

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
