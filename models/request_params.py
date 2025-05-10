from pydantic import BaseModel

# stream request model
class StreamControl(BaseModel):
    start: bool
    ip: str = None

class ConnectRequest(BaseModel):
    ip: str
    name: str

class Message(BaseModel):
    msg: str