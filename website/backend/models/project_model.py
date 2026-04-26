from pydantic import BaseModel, Field

class Project(BaseModel):
    title: str = Field(min_length=3, max_length=70)
    description: str = Field(min_length=10, max_length=700)