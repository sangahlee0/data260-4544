from pydantic import BaseModel, Field, EmailStr

class VulnerabilityCreate(BaseModel):
    package_name: str = Field(min_length=1)
    vulnerability_name: str = Field(min_length=1)

class VulnerabilityUpdate(BaseModel):
    package_name: str = Field(min_length=1)
    vulnerability_name: str = Field(min_length=1)

class VulnerabilityOut(BaseModel):
    id: int
    package_name: str
    vulnerability_name: str

    class Config:
        from_attributes = True

# Users
class UserCreate(BaseModel):
    name: str = Field(min_length=1)
    email: EmailStr

class UserUpdate(BaseModel):
    name: str = Field(min_length=1)
    email: EmailStr

class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr

    class Config:
        from_attributes = True