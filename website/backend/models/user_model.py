from pydantic import BaseModel, Field

class User(BaseModel):
    name: str = Field(min_length=4)
    password: str = Field(min_length=8)
    email: str = Field(min_length=4)