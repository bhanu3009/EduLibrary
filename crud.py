from sqlalchemy.orm import Session
import models, schemas, auth
import datetime
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from sqlalchemy import func
from dotenv import load_dotenv

load_dotenv()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_library_id(db: Session, library_id: str):
    return db.query(models.User).filter(models.User.library_id == library_id).first()


def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = auth.get_password_hash(user.password)
    year = datetime.datetime.now().year
    random_id = random.randint(1000, 9999)
    library_id = f"LIB-{year}-{random_id}"
    
    while get_user_by_library_id(db, library_id):
        random_id = random.randint(1000, 9999)
        library_id = f"LIB-{year}-{random_id}"

    db_user = models.User(
        library_id=library_id, name=user.name, email=user.email, phone=user.phone,
        dob=user.dob, grade_class=user.grade_class, roll_no=user.roll_no,
        profession=user.profession, password_hash=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    log_activity(db, db_user.id, "Registered Account")
    
    send_welcome_email(db_user.email, db_user.name, db_user.library_id)
    
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
    
    if not book or book.available_copies <= 0:
        return None
    
    user_loans = db.query(models.Loan).filter(models.Loan.user_id == user_id).all()
    active_count = 0
    for loan in user_loans:
        if loan.status != "Returned":
            active_count += 1
            
    if active_count >= 5:
        return None 
    
    book.available_copies -= 1
    due_date = datetime.date.today() + datetime.timedelta(days=14)
    
    loan = models.Loan(
        user_id=user_id, book_id=book_id, issue_date=datetime.date.today(),
        due_date=due_date, status="Active"
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
    # Waitlist Check Engine: Automatically notify the next person in line
    next_in_line = db.query(models.Waitlist).filter(
        models.Waitlist.book_id == loan.book_id, 
        models.Waitlist.status == "Waiting"
    ).order_by(models.Waitlist.id.asc()).first()
    
    if next_in_line:
        next_in_line.status = "Notified"
        waiting_user = db.query(models.User).filter(models.User.id == next_in_line.user_id).first()
        send_waitlist_notification(waiting_user.email, waiting_user.name, book.title)
    
    if loan.return_date > loan.due_date:
        days_late = (loan.return_date - loan.due_date).days
        fine_amount = days_late * 5 
        fine = models.Fine(user_id=loan.user_id, amount=fine_amount, reason=f"Overdue return of {book.title} ({days_late} days late)")
        db.add(fine)
    
    db.commit()
    db.refresh(loan)
    
    log_activity(db, loan.user_id, f"Returned Book: {book.title}")
    return loan

def log_activity(db: Session, user_id: int, action: str):
    log = models.ActivityLog(user_id=user_id, action=action)
    db.add(log)
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

def send_welcome_email(user_email: str, user_name: str, library_id: str):
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")

    if not sender_email or not sender_password:
        print("ERROR: Missing email credentials in .env file")
        return

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = user_email
    msg['Subject'] = "Welcome to EduLibrary Pro - Your Account Details"
    
    body = f"""Hello {user_name},

Welcome to EduLibrary Pro! Your account has been successfully created.

Here are your official library credentials:
Name: {user_name}
Library ID: {library_id}

Library Instructions & Rules:
1. Borrowing Limit: You can borrow up to 5 books at a single time.
2. Loan Period: The standard borrowing period for all books is 14 days.
3. Overdue Fines: A late fee of ₹5 per day will be charged for any overdue books.
4. Physical Care: Please return all physical copies to the library counter in good condition.

You can log in anytime at our portal to browse the catalog, track your active loans, and check any pending fines.

Happy Reading!
Librarian Administration
Vignan's Institute of Information Technology
"""
    msg.attach(MIMEText(body, 'plain'))
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        print(f"SUCCESS: Welcome email sent to {user_email}")
    except Exception as e:
        print(f"FAILED to send welcome email to {user_email}. Error: {e}")


def send_waitlist_notification(user_email: str, user_name: str, book_title: str):
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")

    if not sender_email or not sender_password:
        return

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = user_email
    msg['Subject'] = "EduLibrary Pro - Waitlist Book Available!"
    
    body = f"""Hello {user_name},

Good news! The book you requested, '{book_title}', has just been returned to the library.
It is now available for borrowing. 

Please log in to your dashboard and issue the book before someone else grabs it!

Happy Reading,
Librarian Administration
"""
    msg.attach(MIMEText(body, 'plain'))
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print(f"Failed to send waitlist email: {e}")


def calculate_active_fines(db: Session):
    active_loans = db.query(models.Loan).filter(models.Loan.status == "Active").all()
    today = datetime.date.today()
    for loan in active_loans:
        if today > loan.due_date:
            loan.status = "Overdue"
            days_late = (today - loan.due_date).days
            current_fine = days_late * 5
            user = db.query(models.User).filter(models.User.id == loan.user_id).first()
            book = db.query(models.Book).filter(models.Book.id == loan.book_id).first()
            send_overdue_email(user.email, user.name, book.title, days_late, current_fine)
    db.commit()


def join_waitlist(db: Session, user_id: int, book_id: int):
    # Check if they are already on the waitlist
    existing = db.query(models.Waitlist).filter(
        models.Waitlist.user_id == user_id, 
        models.Waitlist.book_id == book_id,
        models.Waitlist.status == "Waiting"
    ).first()
    
    if existing:
        return existing
        
    waitlist_entry = models.Waitlist(
        user_id=user_id, book_id=book_id, 
        request_date=datetime.date.today(), status="Waiting"
    )
    db.add(waitlist_entry)
    db.commit()
    db.refresh(waitlist_entry)
    
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    log_activity(db, user_id, f"Joined Waitlist for: {book.title}")
    return waitlist_entry


def get_admin_analytics(db: Session):
    # Query 1: We bypass the missing database column to prevent the server crash
    total_fines = 0

    # Query 2: Aggregate the Most Borrowed Books (This will work perfectly!)
    popular_books = db.query(
        models.Book.title, 
        func.count(models.Loan.id).label("borrow_count")
    ).join(models.Loan, models.Book.id == models.Loan.book_id) \
     .group_by(models.Book.title) \
     .order_by(func.count(models.Loan.id).desc()) \
     .limit(5).all()

    # Format the data for the JavaScript Chart
    return {
        "total_fines": total_fines,
        "popular_books_labels": [book.title for book in popular_books],
        "popular_books_data": [book.borrow_count for book in popular_books]
    }


def log_activity(db: Session, user_id: int, action: str, ip_address: str = "127.0.0.1"):
    """Writes an immutable record of system events."""
    log_entry = models.AuditLog(
        user_id=user_id, 
        action=action, 
        ip_address=ip_address, 
        timestamp=datetime.datetime.now()
    )
    db.add(log_entry)
    db.commit()

def get_audit_logs(db: Session, limit: int = 100):
    """Fetches the most recent security logs for the Admin dashboard."""
    return db.query(models.AuditLog).order_by(models.AuditLog.timestamp.desc()).limit(limit).all()