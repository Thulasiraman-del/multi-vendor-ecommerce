from pydantic import BaseModel, ConfigDict
class CategoryCreate(BaseModel):
    name:str
    description:str|None=None
class CategoryResponse(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id:int
    name:str
    description:str|None=None
    is_active:bool