from pydantic import BaseModel


class ModuleInfo(BaseModel):
    id: str
    name: str
    group: str
    status: str
    description: str