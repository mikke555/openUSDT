import random

import settings
from modules.utils import random_sleep

from .odos import Odos
from .velodrome import Velodrome
from .xerc20 import HypXERC20


def swap_and_bridge(account):
    hops = random.randint(*settings.HOPS)

    # Initial swap on optimism
    if not swap_to_ousdt(account):
        return False

    random_sleep(*settings.SLEEP_BETWEEN_ACTIONS)

    current_chain = "optimism"  # Start on optimism

    # Perform hops - 1 random transfers
    for _ in range(hops - 1):
        next_dest = transfer_remote(account, chain=current_chain)
        current_chain = next_dest
        random_sleep(*settings.SLEEP_BETWEEN_ACTIONS)

    # Final hop back to optimism if not already there
    if current_chain != "optimism":
        next_dest = transfer_remote(account, chain=current_chain, dest_name="optimism")
        if not next_dest:
            return False

    # Swap back to ETH on optimism
    if not swap_to_eth(account):
        return False

    return True


def transfer_remote(account, chain, dest_name=None):
    dapp = HypXERC20(**account, chain=chain)

    if dest_name:
        dest_id = dapp.get_dest_id_by_name(dest_name)
    else:
        dest_name, dest_id = dapp.get_random_dest()

    if not dapp.transfer_remote(dest_id):
        return False

    return dest_name


def swap_to_ousdt(account):
    dex = Velodrome(**account) if random.randint(0, 1) else Odos(**account)
    return dex.swap_eth()


def swap_to_eth(account):
    dex = Velodrome(**account) if random.randint(0, 1) else Odos(**account)
    return dex.swap_erc20()
