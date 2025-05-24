from pydantic import BaseModel, EmailStr, constr

class AuthSchema(BaseModel):
    email: EmailStr
    password: constr(min_length=8, max_length=64)
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "client@kredilakay.ht",
                "password": "Str0ngP@ss"
            }
        }
