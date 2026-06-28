from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
import datetime
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    library_id = Column(String, unique=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    phone = Column(String)
    dob = Column(Date)
    grade_class = Column(String)
    roll_no = Column(String, nullable=True)
    profession = Column(String) # Student, Teacher, Admin
    password_hash = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    loans = relationship("Loan", back_populates="user")
    fines = relationship("Fine", back_populates="user")
    activities = relationship("ActivityLog", back_populates="user")

class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    author = Column(String, index=True)
    category = Column(String, index=True)
    isbn = Column(String, unique=True, index=True, nullable=True)
    total_copies = Column(Integer, default=1)
    available_copies = Column(Integer, default=1)

    loans = relationship("Loan", back_populates="book")

class Loan(Base):
    __tablename__ = "loans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    book_id = Column(Integer, ForeignKey("books.id"))
    issue_date = Column(Date, default=datetime.date.today)
    due_date = Column(Date)
    return_date = Column(Date, nullable=True)
    status = Column(String, default="Active") # Active, Returned, Overdue

    user = relationship("User", back_populates="loans")
    book = relationship("Book", back_populates="loans")

class Fine(Base):
    __tablename__ = "fines"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Integer, default=0)
    reason = Column(String)
    status = Column(String, default="Unpaid") # Unpaid, Paid
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="fines")

class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="activities")
