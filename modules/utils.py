import csv
import os
import random
import time
from datetime import datetime
from decimal import Decimal

import requests
from tqdm import tqdm
from web3 import Web3

from modules.config import HYPERLANE_DOMAINS


def get_chain_by_id(_id: int) -> str:
    return [name for name, id in HYPERLANE_DOMAINS.items() if id == _id][0]


def get_random_token(tokens: list[str]) -> str:
    _, token_address = random.choice([(k, v) for k, v in tokens.items() if k != "WETH"])
    return token_address


def get_token_price(symbol: str = "ETH") -> float:
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}USDT"
    response = requests.get(url)
    data = response.json()

    return float(data["price"])


def wei(value: float) -> int:
    return Web3.to_wei(value, "ether")


def ether(value: int) -> Decimal:
    return Web3.from_wei(value, "ether")


def read_file(path: str, prefix: str = ""):
    with open(path) as file:
        rows = [f"{prefix}{row.strip()}" for row in file]
    return rows


def random_sleep(max_time, min_time=1):
    if min_time > max_time:
        min_time, max_time = max_time, min_time

    x = random.randint(min_time, max_time)
    time.sleep(x)


def sleep(sleep_time, to_sleep=None, label="Sleeping", new_line=True):
    if to_sleep is not None:
        x = random.randint(sleep_time, to_sleep)
    else:
        x = sleep_time

    desc = datetime.now().strftime("%H:%M:%S")

    for _ in tqdm(range(x), desc=desc, bar_format=f"{{desc}} | {label} {{n_fmt}}/{{total_fmt}}"):
        time.sleep(1)

    if new_line:
        print()  # new line break


def write_to_csv(path, headers, data):
    directory = os.path.dirname(path)

    if directory:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

    with open(path, mode="a", newline="") as file:
        writer = csv.writer(file)

        if file.tell() == 0:
            writer.writerow(headers)

        writer.writerow(data)
