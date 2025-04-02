import json

import questionary

from models.network import Network

q_style = questionary.Style(
    [
        ("qmark", "fg:#47A6F9 bold"),
        ("pointer", "fg:#47A6F9 bold"),
        ("selected", "fg:#47A6F9"),
        ("highlighted", "fg:#808080"),
        ("answer", "fg:#808080"),
        ("instruction", "fg:#808080 italic"),
    ]
)

#######################################################################
#                             Network Config                          #
#######################################################################

ethereum = Network(
    name="ethereum",
    rpc_url="https://rpc.ankr.com/eth",
    explorer="https://etherscan.io",
    eip_1559=True,
    chain_id=1,
    native_token="ETH",
)

linea = Network(
    name="linea",
    rpc_url="https://rpc.linea.build",
    explorer="https://lineascan.build",
    eip_1559=True,
    chain_id=59144,
    native_token="ETH",
)

optimism = Network(
    name="optimism",
    rpc_url="https://mainnet.optimism.io",
    explorer="https://optimistic.etherscan.io",
    eip_1559=True,
    chain_id=10,
    native_token="ETH",
)

base = Network(
    name="base",
    rpc_url="https://mainnet.base.org",
    explorer="https://basescan.org",
    eip_1559=True,
    chain_id=8453,
    native_token="ETH",
)

soneium = Network(
    name="soneium",
    rpc_url="https://rpc.soneium.org",
    explorer="https://soneium.blockscout.com",
    eip_1559=True,
    chain_id=1868,
    native_token="ETH",
)

lisk = Network(
    name="lisk",
    rpc_url="https://rpc.api.lisk.com",
    explorer="https://blockscout.lisk.com",
    eip_1559=True,
    chain_id=1135,
    native_token="ETH",
)

unichain = Network(
    name="unichain",
    rpc_url="https://mainnet.unichain.org",
    explorer="https://uniscan.xyz",
    eip_1559=True,
    chain_id=130,
    native_token="ETH",
)

mode = Network(
    name="mode",
    rpc_url="https://mainnet.mode.network",
    explorer="https://explorer.mode.network",
    eip_1559=True,
    chain_id=34443,
    native_token="ETH",
)

superseed = Network(
    name="superseed",
    rpc_url="https://mainnet.superseed.xyz",
    explorer="https://explorer.superseed.xyz",
    eip_1559=True,
    chain_id=5330,
    native_token="ETH",
)

CHAIN_MAPPING = {
    "ethereum": ethereum,
    "linea": linea,
    "optimism": optimism,
    "base": base,
    "soneium": soneium,
    "lisk": lisk,
    "unichain": unichain,
    "mode": mode,
    "superseed": superseed,
}

#######################################################################
#                             Smart Contracts                         #
#######################################################################

GASZIP_DIRECT_DEPOSIT_ADDRESS = "0x391E7C679d29bD940d63be94AD22A25d25b5A604"

OUSDT = "0x1217BfE6c773EEC6cc4A38b5Dc45B92292B6E189"
WETH = "0x4200000000000000000000000000000000000006"

with open("abi/xERC20.json") as f:
    XERC20_ABI = json.load(f)

with open("abi/ERC20.json") as f:
    ERC20_ABI = json.load(f)


# ========================= Velodrome Finance ========================= #

QUOTER = {
    "optimism": "0x89D8218ed5fF1e46d8dcd33fb0bbeE3be1621466",
    "base": "0x0A5aA5D3a4d28014f967Bf0f29EAA3FF9807D5c6",
}

ROUTER = {
    "optimism": "0x4bF3E32de155359D1D75e8B474b66848221142fc",
    "base": "0x6Cb442acF35158D5eDa88fe602221b67B400Be3E",
}


with open("abi/velodrome/QuoterV2.json") as f:
    QUOTER_ABI = json.load(f)

with open("abi/velodrome/UniversalRouter.json") as f:
    ROUTER_ABI = json.load(f)


# ============================= Hyperlane ============================= #


HYPERLANE_ROUTER = {
    "optimism": "0x7bD2676c85cca9Fa2203ebA324fb8792fbd520b8",
    "base": "0x4F0654395d621De4d1101c0F98C1Dba73ca0a61f",
    "lisk": "0x910FF91a92c9141b8352Ad3e50cF13ef9F3169A1",
    "soneium": "0x2dC335bDF489f8e978477Ae53924324697e0f7BB",
    "unichain": "0x4A8149B1b9e0122941A69D01D23EaE6bD1441b4f",
    "mode": "0x324d0b921C03b1e42eeFD198086A64beC3d736c2",
    "superseed": "0x5beADE696E12aBE2839FEfB41c7EE6DA1f074C55",
}

HYPERLANE_DOMAINS = {
    "optimism": 10,
    "base": 8453,
    "lisk": 1135,
    "soneium": 1868,
    "unichain": 130,
    "mode": 34443,
    "superseed": 5330,
}
