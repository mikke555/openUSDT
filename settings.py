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

STARTING_CHAINS = ["base", "optimism"]  # optimism | base
AVAILABLE_CHAINS = ["optimism", "base", "lisk", "soneium", "unichain", "mode", "superseed"]

HOPS = [4, 5]  # 4-5 bridges

REFUEL_AMOUNT = [0.00025, 0.00045]
