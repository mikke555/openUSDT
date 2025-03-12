import random
import time

from eth_account import Account
from eth_account.messages import encode_defunct
from web3 import HTTPProvider, Web3
from web3.contract import Contract
from web3.exceptions import Web3Exception, Web3RPCError
from web3.middleware import ExtraDataToPOAMiddleware

from models.network import Network
from modules.config import CHAIN_MAPPING, ERC20_ABI
from modules.logger import logger


def get_chain_by_name(name: str) -> Network:
    return CHAIN_MAPPING.get(name.lower())


class Wallet:
    def __init__(self, pk: str, _id: str = None, chain: str = "optimism"):
        self.account = Account.from_key(pk)
        self.address = self.account.address
        self.label = f"{_id} {self.address} | "

        self.chain: Network = get_chain_by_name(chain)
        self.w3 = self.get_web3(chain)

    def __str__(self) -> str:
        return f"Wallet(address={self.address})"

    @property
    def tx_count(self):
        return self.w3.eth.get_transaction_count(self.address)

    def get_web3(self, chain_name: str) -> Web3:
        chain: Network = get_chain_by_name(chain_name)
        web3 = Web3(HTTPProvider(chain.rpc_url))
        web3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

        return web3

    def get_contract(self, address: str, abi: dict = None, chain_name: str = None) -> Contract:
        w3: Web3 = self.get_web3(chain_name) if chain_name else self.w3

        address = w3.to_checksum_address(address)
        if not abi:
            abi = ERC20_ABI

        return w3.eth.contract(address=address, abi=abi)

    def get_token_info(self, token_address: str, chain: str = None, as_dict=False):
        token = self.get_contract(token_address, chain_name=chain)

        balance = token.functions.balanceOf(self.address).call()
        decimals = token.functions.decimals().call()
        symbol = token.functions.symbol().call()

        if as_dict:
            return {"balance": balance, "decimals": decimals, "symbol": symbol}

        return balance, decimals, symbol

    def get_balance(self, token_address: str = None, chain_name: str = None) -> int:
        w3: Web3 = self.get_web3(chain_name) if chain_name else self.w3

        if token_address == None:
            balance = w3.eth.get_balance(self.address)
        else:
            token = self.get_contract(token_address, chain_name=chain_name)
            balance = token.functions.balanceOf(self.address).call()

        return balance

    def await_token_balance(self, token_address: str, chain_name: str = None) -> bool:
        original_balance, decimals, symbol = self.get_token_info(token_address, chain_name)
        new_balance = self.get_balance(token_address, chain_name)
        logger.info(f"{self.label} Waiting for updated {symbol} balance on {chain_name.title()}")

        while new_balance <= original_balance:
            time.sleep(15)
            new_balance = self.get_balance(token_address, chain_name)

        logger.debug(
            f"{self.label} Got new balance of {new_balance / 10**decimals:.6f} {symbol} on {chain_name.title()}\n"
        )
        return True

    def get_gas(self, tx: dict) -> dict:
        gas_price_legacy = self.w3.eth.gas_price
        max_priority_fee = self.w3.eth.max_priority_fee
        latest_block = self.w3.eth.get_block("latest")
        base_fee = int(max(gas_price_legacy, latest_block["baseFeePerGas"]))

        max_fee_per_gas = max_priority_fee + base_fee

        if self.chain.eip_1559:
            tx["maxFeePerGas"] = max_fee_per_gas
            tx["maxPriorityFeePerGas"] = max_priority_fee

        else:
            tx["gasPrice"] = gas_price_legacy

        tx["gas"] = self.w3.eth.estimate_gas(tx)

        return tx

    def get_tx_data(self, value=0, get_gas=False, **kwargs):
        tx = {
            "chainId": self.w3.eth.chain_id,
            "from": self.address,
            "nonce": self.w3.eth.get_transaction_count(self.address),
            "value": value,
            **kwargs,
        }

        return self.get_gas(tx) if get_gas else tx

    def sign_message(self, message: str) -> str:
        message_encoded = encode_defunct(text=message)
        signed_message = self.account.sign_message(message_encoded)

        return "0x" + signed_message.signature.hex()

    def sign_tx(self, tx):
        return self.w3.eth.account.sign_transaction(tx, self.account.key)

    def send_tx(self, tx, tx_label="", gas_multiplier=1.0):
        try:
            tx["gas"] = int(tx["gas"] * gas_multiplier)

            signed_tx = self.sign_tx(tx)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            logger.info(f"{tx_label} [{self.tx_count}] | {self.chain.explorer}/tx/0x{tx_hash.hex()}")

            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=400)

            if tx_receipt.status:
                logger.success(f"{tx_label} [{self.tx_count}] | Tx confirmed \n")
                return tx_receipt.status
            else:
                raise Web3Exception(f"Tx Failed \n")

        except Web3RPCError as err:
            if "insufficient funds" in str(err):
                logger.error(f"{tx_label} | Insufficient funds \n")

            if "already known" in str(err):
                try:
                    tx_hash
                except:
                    tx_hash = ""
                logger.warning(f"{tx_label} | Couldn't get tx hash, assuming it's confirmed \n")
                return tx_hash or True

            else:
                logger.error(err)

        except Web3Exception as err:
            logger.error(f"{tx_label} | {err} \n")

    def check_allowance(self, token_address: str, spender: str) -> int:
        token = self.get_contract(token_address)

        return token.functions.allowance(self.address, spender).call()

    def approve(self, token_address, spender, amount, tx_label):
        token = self.get_contract(token_address)

        balance, decimals, symbol = self.get_token_info(token_address)
        allowance = self.check_allowance(token_address, spender)

        if balance == 0:
            logger.info(f"{tx_label} | Your {symbol} balance is 0")
            return

        if allowance >= balance:
            logger.warning(f"{tx_label} | {balance / 10 ** decimals:.6f} {symbol} Already approved")
            return

        tx_data = self.get_tx_data()
        tx = token.functions.approve(spender, amount).build_transaction(tx_data)

        status = self.send_tx(tx, tx_label)
        time.sleep(random.randint(5, 10))

        return status
