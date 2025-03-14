import random

from eth_abi import encode
from eth_utils import to_bytes

import settings
from modules.config import OUSDT, QUOTER, QUOTER_ABI, ROUTER, ROUTER_ABI, WETH
from modules.logger import logger
from modules.utils import ether, wei
from modules.wallet import Wallet

commands = {"WRAP_SWAP": "0x0b00", "SWAP_UNWRAP": "0x000c"}
FEE_BIPS = 100  # 0.01% fee tier | bip = 1/10000


class Velodrome(Wallet):
    def __init__(self, pk, _id, proxy, chain):
        super().__init__(pk, _id, chain)

        self.label += "Aerodrome |" if self.chain.name == "base" else "Velodrome |"
        self.quoter = self.get_contract(QUOTER[self.chain.name], abi=QUOTER_ABI)
        self.router = self.get_contract(ROUTER[self.chain.name], abi=ROUTER_ABI)

    def _get_amount_out(self, path: bytes, amount_in: int, slippage: int = 1) -> int:
        """
        quoteExactInput returns []:
            amountOut
            The amount of the last token that would be received

            gasEstimate
            The estimate of the gas that the swap consumes

            initializedTicksCrossedList
            List of the initialized ticks that the swap crossed for each pool in the path

            sqrtPriceX96AfterList
            List of the sqrt price after the swap for each pool in the path

            Example output:
                [1512879, [1728150856839541183868667626044367], [1], 139086]
        """

        amount_out = self.quoter.functions.quoteExactInput(path, amount_in).call()[0]
        min_amount_out = int(amount_out * (1 - slippage / 100))

        if amount_out <= 0:
            raise ValueError("Invalid quoted amount")

        return min_amount_out

    def _build_swap_path(self, token_in: str, token_out: str) -> bytes:
        hexstr = (
            self.w3.to_checksum_address(token_in)[2:].lower()
            + f"{FEE_BIPS:06x}"
            + self.w3.to_checksum_address(token_out)[2:].lower()
        )
        return to_bytes(hexstr=hexstr)

    def _build_eth_swap(self, amount_in: int, token_in: str, token_out: str):
        """ETH → WETH → oUSDT swap construction"""
        # 1. Wrap ETH parameters
        wrap_params = encode(["address", "uint256"], [self.router.address, amount_in])

        # 2. Swap parameters
        path = self._build_swap_path(token_in, token_out)
        amount_out = self._get_amount_out(path, amount_in)

        swap_params = encode(
            ["address", "uint256", "uint256", "bytes", "bool"],
            [self.address, amount_in, amount_out, path, False],
        )

        return commands["WRAP_SWAP"], [wrap_params, swap_params], amount_in

    def _build_erc20_swap(self, amount_in: int, token_in: str, token_out: str):
        """oUSDT → WETH → ETH swap construction"""
        # 1. Swap parameters
        path = self._build_swap_path(token_in, token_out)
        amount_out = self._get_amount_out(path, amount_in)

        swap_params = encode(
            ["address", "uint256", "uint256", "bytes", "bool"],
            [self.router.address, amount_in, amount_out, path, True],
        )

        # # 2. Unwrap parameters
        unwrap_params = encode(["address", "uint256"], [self.address, amount_out])

        return commands["SWAP_UNWRAP"], [swap_params, unwrap_params], 0

    def swap_eth(self, token_in: str = WETH, token_out: str = OUSDT):
        amount_in = wei(random.uniform(*settings.SWAP_AMOUNT))
        token_out_symbol = self.get_token_info(token_out, as_dict=True)["symbol"]

        commands, inputs, value = self._build_eth_swap(amount_in, token_in, token_out)

        contract_tx = self.router.functions.execute(commands, inputs).build_transaction(self.get_tx_data(value=value))

        return self.send_tx(
            contract_tx,
            tx_label=f"{self.label} Swap {ether(amount_in):.6f} ETH -> {token_out_symbol}",
            gas_multiplier=1.1,
        )

    def swap_erc20(self, token_in: str = OUSDT, token_out: str = WETH):
        balance, decimals, symbol = self.get_token_info(token_in)
        amount_in = int(balance * random.uniform(*settings.SWAP_BACK_PERCENTAGE))

        if not balance:
            logger.warning(f"{self.label} No {symbol} tokens to swap \n")
            return

        commands, inputs, value = self._build_erc20_swap(amount_in, token_in, token_out)

        self.approve(token_in, self.router.address, amount_in)

        contract_tx = self.router.functions.execute(commands, inputs).build_transaction(self.get_tx_data(value=value))

        return self.send_tx(
            contract_tx,
            tx_label=f"{self.label} Swap {amount_in / 10**decimals:.8f} {symbol} -> ETH",
            gas_multiplier=1.2,
        )
