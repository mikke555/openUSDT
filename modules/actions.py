import random

from questionary import select

import settings

from .config import q_style
from .gaszip import GasZip
from .odos import Odos
from .relay import Relay
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
    BRIDGING_FEE = 0.0001138
    REFUEL_THRESHOLD = 0.00025

    def __init__(self, account):
        self.account = account
        self.current_chain = None

    @property
    def min_balance_required(self):
        return self.BRIDGING_FEE + max(settings.SWAP_AMOUNT)

    # ========================= Helper methods ========================= #

    def _get_balance_for_chain(self, chain: str) -> float:
        """Get ETH balance for a specific chain."""

        wallet = Wallet(pk=self.account["pk"], _id=self.account["_id"], chain=chain)
        return wallet.get_balance(human=True)

    def _select_starting_chain(self):
        """Select a starting chain that has a balance > the minimum required."""

        starting_chains = settings.STARTING_CHAINS.copy()
        random.shuffle(starting_chains)

        balances = {chain: self._get_balance_for_chain(chain) for chain in starting_chains}

        for chain in starting_chains:
            if balances[chain] > self.min_balance_required:
                return chain
        raise Exception("No source chain with sufficient balance")

    def _get_random_dex(self, chain):
        """Select a random DEX for the given chain."""

        dex_list = [Velodrome, Odos]
        return random.choice(dex_list)(**self.account, chain=chain)

    def _swap(self, chain="base", to_eth=False):
        """Perform a swap on the specified chain."""

        dex = self._get_random_dex(chain)
        return dex.swap_erc20() if to_eth else dex.swap_eth()

    def _ensure_gas_on_destination(self, dest_chain: str) -> None:
        """Ensure the destination chain has sufficient gas."""

        if self._get_balance_for_chain(dest_chain) < self.REFUEL_THRESHOLD:
            balances = {
                chain: self._get_balance_for_chain(chain) for chain in settings.AVAILABLE_CHAINS if chain != dest_chain
            }

            refuel_source = max(balances, key=balances.get)

            if balances[refuel_source] > max(settings.REFUEL_AMOUNT):
                dapp = self._get_random_refuel(chain=refuel_source, dest_chain=dest_chain)
                dapp.refuel()
                random_sleep(*settings.SLEEP_BETWEEN_ACTIONS)
            else:
                raise Exception(f"No refuel source with sufficient balance")

    def _get_random_refuel(self, chain=None, dest_chain=None):
        """Select a random dapp for refuel."""

        refuel_list = [GasZip, Relay]
        return random.choice(refuel_list)(**self.account, chain=chain, dest_chain=dest_chain)

    def _bridge(self, chain, dest_name=None):
        """Bridge tokens to a random destination after ensuring sufficient gas."""

        bridge = HypXERC20(**self.account, chain=chain)

        dest_name = dest_name or bridge.get_random_dest()
        dest_id = bridge.get_dest_id_by_name(dest_name)

        self._ensure_gas_on_destination(dest_name)
        return dest_name if bridge.transfer_remote(dest_id) else False

    def _perform_initial_swap(self) -> bool:
        """Perform the initial swap on a random starting chain."""

        return self._swap(chain=self.current_chain)

    def _perform_intermediate_bridges(self, hops: int) -> bool:
        """Perform intermediate bridges across chains."""

        for _ in range(hops - 1):
            next_dest = self._bridge(self.current_chain)

            if not next_dest:
                return False

            self.current_chain = next_dest
            random_sleep(*settings.SLEEP_BETWEEN_ACTIONS)
        return True

    def _perform_final_bridge_and_swap(self) -> bool:
        """Bridge to final destination and swap to ETH."""

        match self.current_chain:
            case "base":
                final_dest = "optimism"
            case "optimism":
                final_dest = "base"
            case _:
                final_dest = random.choice(["base", "optimism"])

        self.current_chain = self._bridge(self.current_chain, dest_name=final_dest)

        if not self.current_chain:
            return False

        random_sleep(*settings.SLEEP_BETWEEN_ACTIONS)
        return self._swap(chain=final_dest, to_eth=True)

    # ========================= User actions ========================= #

    def swap_and_bridge(self) -> bool:
        """Perform a sequence of swaps and bridges."""

        hops = random.randint(*settings.HOPS)
        self.current_chain = self._select_starting_chain()

        if self.current_chain in ["base", "optimism"]:
            if not self._perform_initial_swap():
                return False
            random_sleep(*settings.SLEEP_BETWEEN_ACTIONS)

        if hops > 1 and not self._perform_intermediate_bridges(hops):
            return False

        return self._perform_final_bridge_and_swap()

    def swap_eth_to_ousdt(self):
        """Prompt user for chain and swap ETH to oUSDT."""

        chain = select("Swap ETH -> oUSDT:", choices=["base", "optimism"], style=q_style).ask()
        if chain is None:
            quit()

        return self._swap(chain=chain, to_eth=False)

    def swap_ousdt_to_eth(self):
        """Prompt user for chain and swap oUSDT to ETH."""

        chain = select("Swap oUSDT -> ETH:", choices=["base", "optimism"], style=q_style).ask()
        if chain is None:
            quit()

        return self._swap(chain=chain, to_eth=True)

    def prompt_and_bridge(self):
        """Prompt user for source and destination chains and bridge oUSDT."""
        source_chain = select("Select source chain:", choices=settings.AVAILABLE_CHAINS, style=q_style).ask()

        if source_chain is None:
            quit()

        dest_chain = select(
            "Select destination chain:",
            choices=[chain for chain in settings.AVAILABLE_CHAINS if chain != source_chain],
            style=q_style,
        ).ask()

        if dest_chain is None:
            quit()

        return self._bridge(source_chain, dest_name=dest_chain)

    def refuel(self, chain=None, dest_chain=None):
        """Perform a refuel from a source chain to a destination chain."""

        if not chain:
            chain = select("Source chain", choices=settings.AVAILABLE_CHAINS, style=q_style).ask()
            not chain and quit()

        if not dest_chain:
            dest = select("Destination chain", choices=settings.AVAILABLE_CHAINS, style=q_style).ask()
            not chain and quit()

        dapp = self._get_random_refuel(chain, dest_chain=dest)
        dapp.refuel()
