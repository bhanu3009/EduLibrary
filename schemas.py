from pydantic import BaseModel, EmailStr
from datetime import date, datetime
from typing import List, Optional

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str
    dob: date
    grade_class: str
    roll_no: Optional[str] = None
    profession: str
    password: str

class UserResponse(BaseModel):
    id: int
    library_id: str
    name: str
    email: EmailStr
    phone: str
    grade_class: str
    profession: str
    
    class Config:
        from_attributes = True

class BookBase(BaseModel):
    title: str
    author: str
    category: str
    isbn: Optional[str] = None
    total_copies: int

class BookCreate(BookBase):
    pass

class BookResponse(BookBase):
    id: int
    available_copies: int
    
    class Config:
        from_attributes = True

class LoanResponse(BaseModel):
    id: int
    book_id: int
    issue_date: date
    due_date: date
    return_date: Optional[date] = None
    status: str
    book: BookResponse
    
    class Config:
        from_attributes = True

class FineResponse(BaseModel):
    id: int
    amount: int
    reason: str
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class ActivityLogResponse(BaseModel):
    id: int
    action: str
    timestamp: datetime
    
    class Config:
        from_attributes = True

class UserProfile(UserResponse):
    loans: List[LoanResponse] = []
    fines: List[FineResponse] = []
    activities: List[ActivityLogResponse] = []
