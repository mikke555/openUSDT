########################################################################
#                           General Settings                           #
########################################################################

USE_PROXY = False
SHUFFLE_WALLETS = False

SLEEP_BETWEEN_WALLETS = [20, 40]
SLEEP_BETWEEN_ACTIONS = [20, 120]

########################################################################
#                           Action Settings                            #
########################################################################

SWAP_AMOUNT = [0.001, 0.002]
SWAP_BACK_PERCENTAGE = [1, 1]  # 1 = 100%

STARTING_CHAIN = ["base", "optimism"]  # optimism | base
AVAILABLE_CHAINS = ["optimism", "base", "lisk", "soneium", "unichain", "mode"]

MIN_GAS_BALANCE = 0.00016  # $.30
GASZIP_REFUEL_SOURCE = ["base", "optimism"]
GASZIP_REFUEL_AMOUNT = [0.00055, 0.00105]

HOPS = [5, 6]  # 4-5 bridges
