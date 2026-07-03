from database import SessionLocal
import models
import datetime

# Open a connection to your local database
db = SessionLocal()

# Find the book you just borrowed
loan = db.query(models.Loan).filter(models.Loan.status == "Active").first()

if loan:
    print(f"Old Due Date: {loan.due_date}")
    
    loan.due_date = datetime.date(2026, 6, 1)
    db.commit()
    
    print("SUCCESS: Time travel complete. The book is now dangerously overdue!")
else:
    print("ERROR: Could not find any active borrowed books.")

db.close()