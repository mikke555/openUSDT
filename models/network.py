from pydantic import BaseModel


class Network(BaseModel):
    name: str
    rpc_url: str
    explorer: str
    eip_1559: bool
    native_token: str

    def __str__(self):
        return self.name
