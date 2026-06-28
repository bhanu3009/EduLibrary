from fastapi import FastAPI, Depends, HTTPException, Request, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import os

import models, schemas, crud, auth, database

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="EduLibrary Pro")

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, db: Session = Depends(get_db)):
    user = auth.get_current_user_from_cookie(request, db)
    if user:
        return RedirectResponse(url="/dashboard")
    return templates.TemplateResponse(request=request, name="login.html", context={"user": None})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse(request=request, name="register.html", context={"user": None})

@app.post("/register", response_class=HTMLResponse)
async def register(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    dob: str = Form(...),
    grade_class: str = Form(...),
    roll_no: str = Form(None),
    profession: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    # --- NEW CHECK: See if email already exists before trying to save ---
    existing_user = crud.get_user_by_email(db, email)
    if existing_user:
        return templates.TemplateResponse(
            request=request, 
            name="register.html", 
            context={"user": None, "error": "This email is already registered. Please login or use a different email."}
        )
    # --------------------------------------------------------------------
    try:
        user_create = schemas.UserCreate(
            name=name, email=email, phone=phone, dob=datetime.strptime(dob, "%Y-%m-%d").date(),
            grade_class=grade_class, roll_no=roll_no, profession=profession, password=password
        )
        user = crud.create_user(db, user_create)
        return templates.TemplateResponse(request=request, name="login.html", context={"user": None, "msg": f"Registered successfully! Your Library ID is {user.library_id}. Please log in."})
    except Exception as e:
        return templates.TemplateResponse(request=request, name="register.html", context={"user": None, "error": str(e)})


@app.post("/login")
async def login(
    response: Response, 
    request: Request, 
    login_identifier: str = Form(...), 
    password: str = Form(...), 
    db: Session = Depends(get_db)
):
    # Smart routing: check if user typed an email or an ID
    if "@" in login_identifier:
        user = crud.get_user_by_email(db, login_identifier)
    else:
        user = crud.get_user_by_library_id(db, login_identifier)
        
    if not user or not auth.verify_password(password, user.password_hash):
        return templates.TemplateResponse(request=request, name="login.html", context={"user": None, "error": "Invalid Email/Library ID or Password"})
    
    access_token = auth.create_access_token(data={"sub": user.library_id})
    res = RedirectResponse(url="/dashboard", status_code=302)
    res.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return res


@app.get("/logout")
async def logout(response: Response):
    res = RedirectResponse(url="/", status_code=302)
    res.delete_cookie("access_token")
    return res

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    user = auth.get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/")
    
    if user.profession == "Admin":
        return RedirectResponse(url="/admin")
        
    # Manual live fine calculation
    today = datetime.now().date()
    live_fine_total = 0
    
    # Add previously saved unpaid fines
    for fine in user.fines:
        if fine.status == "Unpaid":
            live_fine_total += fine.amount
            
    # Add active overdue fines dynamically (₹5 per day)
    for loan in user.loans:
        if loan.status != "Returned":
            if today > loan.due_date:
                days_late = 0
                # Manual date difference calculation
                current_date = loan.due_date
                while current_date < today:
                    days_late += 1
                    current_date += timedelta(days=1)
                
                live_fine_total += (days_late * 5)
        
    return templates.TemplateResponse(request=request, name="dashboard.html", context={"user": user, "live_fine_total": live_fine_total})

@app.get("/catalog", response_class=HTMLResponse)
async def catalog(request: Request, search: str = None, db: Session = Depends(get_db)):
    user = auth.get_current_user_from_cookie(request, db)
    if search:
        books = crud.search_books(db, search)
    else:
        books = crud.get_books(db)
    return templates.TemplateResponse(request=request, name="catalog.html", context={"user": user, "books": books, "search": search})

@app.post("/issue/{book_id}")
async def issue_book_endpoint(request: Request, book_id: int, db: Session = Depends(get_db)):
    user = auth.get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/")
    crud.issue_book(db, user.id, book_id)
    return RedirectResponse(url="/dashboard", status_code=302)

@app.post("/return/{loan_id}")
async def return_book_endpoint(request: Request, loan_id: int, db: Session = Depends(get_db)):
    user = auth.get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/")
    crud.return_book(db, loan_id)
    return RedirectResponse(url="/dashboard", status_code=302)

@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    user = auth.get_current_user_from_cookie(request, db)
    if not user or user.profession != "Admin":
        return RedirectResponse(url="/dashboard")
    
    users = db.query(models.User).all()
    books = db.query(models.Book).all()
    loans = db.query(models.Loan).order_by(models.Loan.issue_date.desc()).limit(10).all()
    fines = db.query(models.Fine).filter(models.Fine.status == "Unpaid").all()
    
    stats = {
        "total_members": len(users),
        "books_available": sum(b.available_copies for b in books),
        "fines_due": sum(f.amount for f in fines)
    }
    
    return templates.TemplateResponse(request=request, name="admin.html", context={
        "user": user, "stats": stats, "recent_loans": loans
    })

@app.post("/admin/add_book")
async def admin_add_book(
    request: Request,
    title: str = Form(...),
    author: str = Form(...),
    category: str = Form(...),
    total_copies: int = Form(...),
    db: Session = Depends(get_db)
):
    user = auth.get_current_user_from_cookie(request, db)
    if not user or user.profession != "Admin":
        return RedirectResponse(url="/dashboard")
        
    book_in = schemas.BookCreate(title=title, author=author, category=category, total_copies=total_copies)
    crud.create_book(db, book_in)
    return RedirectResponse(url="/admin", status_code=302)

@app.get("/trigger_cron")
async def trigger_cron(db: Session = Depends(get_db)):
    crud.calculate_active_fines(db)
    return {"status": "cron completed"}