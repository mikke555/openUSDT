########################################################################
#                           General Settings                           #
########################################################################

USE_PROXY = False
SHUFFLE_WALLETS = False

SLEEP_BETWEEN_WALLETS = [10, 20]
SLEEP_BETWEEN_ACTIONS = [10, 20]

########################################################################
#                           Action Settings                            #
########################################################################

SWAP_AMOUNT = [0.00054, 0.0011]  # 1- 2$
SWAP_BACK_PERCENTAGE = [1, 1]  # 1 = 100%

STARTING_CHAIN = ["base", "optimism"]  # optimism | base
HOPS = [3, 5]  # 2-4 bridges
