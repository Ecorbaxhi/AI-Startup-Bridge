from pydantic import BaseModel, EmailStr

class Registration(BaseModel):
    email: EmailStr
    password: str
    role: str
