import random

import settings
from modules.utils import random_sleep

from .odos import Odos
from .velodrome import Velodrome
from .xerc20 import HypXERC20


def swap_and_bridge(account):
    hops = random.randint(*settings.HOPS)
    current_chain = random.choice(settings.STARTING_CHAIN)

    # Perform initial swap on base or optimism
    if not swap_eth(account, chain=current_chain):
        return False
    random_sleep(*settings.SLEEP_BETWEEN_ACTIONS)

    # Perform hops - 1 random transfers
    for _ in range(hops - 1):
        next_dest = transfer_remote(account, chain=current_chain)
        if not next_dest:
            return False
        current_chain = next_dest
        random_sleep(*settings.SLEEP_BETWEEN_ACTIONS)

    # Perform the final transfer to base or optimism
    last_dest = random.choice(["base", "optimism"])
    next_dest = transfer_remote(account, chain=current_chain, dest_name=last_dest)
    if not next_dest:
        return False
    current_chain = next_dest  # Update to the final chain
    random_sleep(*settings.SLEEP_BETWEEN_ACTIONS)

    # Perform the final swap back to ETH on the current chain
    if not swap_erc20(account, chain=current_chain):
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


def swap_eth(account, chain="optimism"):
    dex = Velodrome(**account, chain=chain) if random.randint(0, 1) else Odos(**account, chain=chain)
    return dex.swap_eth()


def swap_erc20(account, chain="optimism"):
    dex = Velodrome(**account, chain=chain) if random.randint(0, 1) else Odos(**account, chain=chain)
    return dex.swap_erc20()
