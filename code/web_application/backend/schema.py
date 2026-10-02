from pydantic import BaseModel, Field, EmailStr

class VulnerabilityCreate(BaseModel):
    package_id: int
    vulnerability_name: str = Field(min_length=1)
    vulnerability_code: str = Field(min_length=1)
    count: int = Field(default=0, ge=0)  # Ensure count is non-negative

class VulnerabilityUpdate(BaseModel):
    package_id: int
    vulnerability_name: str = Field(min_length=1)
    vulnerability_code: str = Field(min_length=1)
    count: int = Field(default=0, ge=0)  # Ensure count is non-negative

class VulnerabilityOut(BaseModel):
    id: int
    package_id: int
    vulnerability_name: str
    vulnerability_code: str
    count: int

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


####
# Update pydantic schemas for the second entity (Package)
class PackageCreate(BaseModel):
    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    package_code: str = Field(min_length=3, pattern=r"^[A-Za-z0-9-]+$")

class PackageUpdate(BaseModel):
    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    package_code: str = Field(min_length=3, pattern=r"^[A-Za-z0-9-]+$")

class PackageOut(BaseModel):
    id: int
    name: str
    version: str
    package_code: str

    class Config:
        from_attributes = True
