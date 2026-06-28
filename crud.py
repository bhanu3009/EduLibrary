from sqlalchemy.orm import Session
import models, schemas, auth
import datetime
import random

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_library_id(db: Session, library_id: str):
    return db.query(models.User).filter(models.User.library_id == library_id).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = auth.get_password_hash(user.password)
    year = datetime.datetime.now().year
    random_id = random.randint(1000, 9999)
    library_id = f"LIB-{year}-{random_id}"
    
    # Ensure uniqueness
    while get_user_by_library_id(db, library_id):
        random_id = random.randint(1000, 9999)
        library_id = f"LIB-{year}-{random_id}"

    db_user = models.User(
        library_id=library_id,
        name=user.name,
        email=user.email,
        phone=user.phone,
        dob=user.dob,
        grade_class=user.grade_class,
        roll_no=user.roll_no,
        profession=user.profession,
        password_hash=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    log_activity(db, db_user.id, "Registered Account")
    return db_user

def get_books(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Book).offset(skip).limit(limit).all()

def search_books(db: Session, query: str):
    return db.query(models.Book).filter(
        (models.Book.title.ilike(f"%{query}%")) | 
        (models.Book.author.ilike(f"%{query}%")) |
        (models.Book.category.ilike(f"%{query}%"))
    ).all()

def create_book(db: Session, book: schemas.BookCreate):
    db_book = models.Book(**book.model_dump(), available_copies=book.total_copies)
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book


def issue_book(db: Session, user_id: int, book_id: int):
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    
    # 1. Manual check for book availability
    if not book:
        return None
    if book.available_copies <= 0:
        return None
    
    # 2. Manual slot check (Maximum 5 books)
    user_loans = db.query(models.Loan).filter(models.Loan.user_id == user_id).all()
    active_count = 0
    for loan in user_loans:
        if loan.status != "Returned":
            active_count += 1
            
    if active_count >= 5:
        return None  # Reached the 5-book limit
    
    # 3. Process the issue
    book.available_copies -= 1
    due_date = datetime.date.today() + datetime.timedelta(days=14)
    
    loan = models.Loan(
        user_id=user_id,
        book_id=book_id,
        issue_date=datetime.date.today(),
        due_date=due_date,
        status="Active"
    )
    db.add(loan)
    db.commit()
    db.refresh(loan)
    
    log_activity(db, user_id, f"Issued Book: {book.title}")
    return loan

def return_book(db: Session, loan_id: int):
    loan = db.query(models.Loan).filter(models.Loan.id == loan_id).first()
    if not loan or loan.status == "Returned":
        return None
    
    loan.status = "Returned"
    loan.return_date = datetime.date.today()
    
    book = db.query(models.Book).filter(models.Book.id == loan.book_id).first()
    book.available_copies += 1
    
    # Check for fine
    if loan.return_date > loan.due_date:
        days_late = (loan.return_date - loan.due_date).days
        fine_amount = days_late * 5 # Rs 5 per day
        fine = models.Fine(
            user_id=loan.user_id,
            amount=fine_amount,
            reason=f"Overdue return of {book.title} ({days_late} days late)"
        )
        db.add(fine)
    
    db.commit()
    db.refresh(loan)
    
    log_activity(db, loan.user_id, f"Returned Book: {book.title}")
    return loan

def log_activity(db: Session, user_id: int, action: str):
    log = models.ActivityLog(user_id=user_id, action=action)
    db.add(log)
    db.commit()

def calculate_active_fines(db: Session):
    # This would typically be run by a daily cron job
    active_loans = db.query(models.Loan).filter(models.Loan.status == "Active").all()
    today = datetime.date.today()
    for loan in active_loans:
        if today > loan.due_date:
            loan.status = "Overdue"
    db.commit()

def get_user_fines(db: Session, user_id: int):
    return db.query(models.Fine).filter(models.Fine.user_id == user_id, models.Fine.status == "Unpaid").all()

def pay_fine(db: Session, fine_id: int):
    fine = db.query(models.Fine).filter(models.Fine.id == fine_id).first()
    if fine:
        fine.status = "Paid"
        log_activity(db, fine.user_id, f"Paid Fine: Rs {fine.amount}")
        db.commit()
        return True
    return False
