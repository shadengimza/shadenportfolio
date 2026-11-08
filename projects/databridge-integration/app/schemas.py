from pydantic import BaseModel, ConfigDict, Field


class CustomerOut(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    customer_id: str = Field(min_length=1)
    first_name: str
    last_name: str
    email: str
    status: str
