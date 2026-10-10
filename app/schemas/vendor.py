from pydantic import BaseModel, ConfigDict
class VendorCreate(BaseModel):
    business_name:str
    business_description:str|None=None
class VendorResponse(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id:int
    user_id:int
    business_name:str
    business_description:str|None=None
    is_active:bool