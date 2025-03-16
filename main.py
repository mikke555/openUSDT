import random

import questionary
from questionary import Choice

import settings
from modules.actions import Action
from modules.config import q_style
from modules.logger import logger
from modules.utils import read_file, sleep


def get_action() -> Action:
    choices = [
        Choice("Swap and bridge oUSDT", Action("swap_and_bridge")),
        Choice("Swap ETH > oUSDT", Action("swap_eth_to_ousdt")),
        Choice("Swap oUSDT > ETH", Action("swap_ousdt_to_eth")),
        Choice("Quit", "quit"),
    ]
    action = questionary.select(
        "Action",
        choices=choices,
        style=q_style,
    ).ask()

    if action == "quit" or action is None:
        quit()

    return action


def get_accounts() -> list[dict]:
    keys = read_file("keys.txt")
    proxies = read_file("proxies.txt", prefix="http://")

    if not keys:
        logger.warning("keys.txt is empty") and quit()
    if not proxies and settings.USE_PROXY:
        logger.warning("proxies.txt is empty") and quit()

    accounts = [
        {"pk": key, "proxy": proxies[index % len(proxies)] if settings.USE_PROXY else None}
        for index, key in enumerate(keys)
    ]

    if settings.SHUFFLE_WALLETS:
        random.shuffle(accounts)

    for index, account in enumerate(accounts, start=1):
        account["_id"] = f"[{index}/{len(accounts)}]"

    return accounts


def main():
    action = get_action()
    accounts = get_accounts()

    for index, account in enumerate(accounts, start=1):
        tx_status = action(account)

        if tx_status and index < len(accounts):
            sleep(*settings.SLEEP_BETWEEN_WALLETS)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("Cancelled by user")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
