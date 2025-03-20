from pydantic import BaseModel, Field


class Data(BaseModel):
    from_: str = Field(..., alias="from")
    to: str
    data: str
    value: str
    chainId: int
    gas: str
    maxFeePerGas: str
    maxPriorityFeePerGas: str


class Check(BaseModel):
    endpoint: str
    method: str


class Item(BaseModel):
    status: str
    data: Data
    check: Check


class Step(BaseModel):
    id: str
    action: str
    description: str
    kind: str
    requestId: str
    depositAddress: str
    items: list[Item]


class Metadata(BaseModel):
    logoURI: str
    verified: bool
    isNative: bool


class Currency(BaseModel):
    chainId: int
    address: str
    symbol: str
    name: str
    decimals: int
    metadata: Metadata


class Gas(BaseModel):
    currency: Currency
    amount: str
    amountFormatted: str
    amountUsd: str
    minimumAmount: str


class Metadata1(BaseModel):
    logoURI: str
    verified: bool
    isNative: bool


class Currency1(BaseModel):
    chainId: int
    address: str
    symbol: str
    name: str
    decimals: int
    metadata: Metadata1


class Relayer(BaseModel):
    currency: Currency1
    amount: str
    amountFormatted: str
    amountUsd: str
    minimumAmount: str


class Metadata2(BaseModel):
    logoURI: str
    verified: bool
    isNative: bool


class Currency2(BaseModel):
    chainId: int
    address: str
    symbol: str
    name: str
    decimals: int
    metadata: Metadata2


class RelayerGas(BaseModel):
    currency: Currency2
    amount: str
    amountFormatted: str
    amountUsd: str
    minimumAmount: str


class Metadata3(BaseModel):
    logoURI: str
    verified: bool
    isNative: bool


class Currency3(BaseModel):
    chainId: int
    address: str
    symbol: str
    name: str
    decimals: int
    metadata: Metadata3


class RelayerService(BaseModel):
    currency: Currency3
    amount: str
    amountFormatted: str
    amountUsd: str
    minimumAmount: str


class Metadata4(BaseModel):
    logoURI: str
    verified: bool
    isNative: bool


class Currency4(BaseModel):
    chainId: int
    address: str
    symbol: str
    name: str
    decimals: int
    metadata: Metadata4


class App(BaseModel):
    currency: Currency4
    amount: str
    amountFormatted: str
    amountUsd: str
    minimumAmount: str


class Fees(BaseModel):
    gas: Gas
    relayer: Relayer
    relayerGas: RelayerGas
    relayerService: RelayerService
    app: App


class Metadata5(BaseModel):
    logoURI: str
    verified: bool
    isNative: bool


class Currency5(BaseModel):
    chainId: int
    address: str
    symbol: str
    name: str
    decimals: int
    metadata: Metadata5


class CurrencyIn(BaseModel):
    currency: Currency5
    amount: str
    amountFormatted: str
    amountUsd: str
    minimumAmount: str


class Metadata6(BaseModel):
    logoURI: str
    verified: bool
    isNative: bool


class Currency6(BaseModel):
    chainId: int
    address: str
    symbol: str
    name: str
    decimals: int
    metadata: Metadata6


class CurrencyOut(BaseModel):
    currency: Currency6
    amount: str
    amountFormatted: str
    amountUsd: str
    minimumAmount: str


class TotalImpact(BaseModel):
    usd: str
    percent: str


class SwapImpact(BaseModel):
    usd: str
    percent: str


class Origin(BaseModel):
    usd: str
    value: str
    percent: str


class Destination(BaseModel):
    usd: str
    value: str
    percent: str


class SlippageTolerance(BaseModel):
    origin: Origin
    destination: Destination


class Details(BaseModel):
    operation: str
    sender: str
    recipient: str
    currencyIn: CurrencyIn
    currencyOut: CurrencyOut
    totalImpact: TotalImpact
    swapImpact: SwapImpact
    rate: str
    slippageTolerance: SlippageTolerance
    timeEstimate: int
    userBalance: str


class Quote(BaseModel):
    steps: list[Step]
    fees: Fees
    details: Details
