# 📚 EduLibrary Pro

A secure, full-stack **Library Management System** built with FastAPI, featuring JWT-based authentication delivered via HttpOnly cookies, role-based access control, and strict request validation — built as a security-focused portfolio project.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.137-teal.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

---

## 🚀 Overview

EduLibrary Pro is a library management platform handling book cataloging, member management, and a borrow/return workflow — built with production-style security practices instead of typical tutorial-level auth.

**Live Demo:** [Add your deployment URL here, if deployed]

---

## ✨ Key Features

### Core Functionality
- 📖 Book catalog management (add, update, search)
- 👥 Member registration and profile management
- 🔄 Borrow / return workflow

### Security Architecture
- 🔐 **JWT Authentication** (PyJWT) delivered via HttpOnly cookies — mitigates XSS-based token theft
- 🧂 **Password hashing** with bcrypt via passlib (salted, adaptive cost)
- 🛡️ **Role-Based Access Control (RBAC)** — separate permission tiers enforced at the route level
- 🔑 **OAuth2 password flow** using FastAPI's built-in `OAuth2PasswordBearer` / `OAuth2PasswordRequestForm`
- ✅ **Pydantic validation** on all request/response schemas, including email validation
- 🔒 Secrets loaded via `python-dotenv` — never hardcoded, never committed

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend Framework | FastAPI |
| Templating | Jinja2 |
| ORM | SQLAlchemy |
| Database | SQLite |
| Auth | PyJWT (HttpOnly cookies) + FastAPI OAuth2 |
| Password Hashing | passlib (bcrypt) |
| Validation | Pydantic + email-validator |
| Server | Uvicorn |
| Env Management | python-dotenv |

> **Note:** SQLite is used for development. For production deployment, swapping in PostgreSQL/MySQL is a planned upgrade (see Roadmap).

---

## 📂 Project Structure

```
EduLibrary/
├── app/
│   ├── main.py              # FastAPI app entrypoint
│   ├── models/               # SQLAlchemy models
│   ├── schemas/               # Pydantic schemas
│   ├── routers/                # API route handlers
│   ├── auth/                    # JWT / OAuth2 / RBAC logic
│   ├── templates/                # Jinja2 templates
│   └── static/                    # CSS/JS assets
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```
> Adjust this tree to match your actual folder layout before pushing.

---

## ⚙️ Installation & Setup

### Prerequisites
- Python 3.11+
- pip

### 1. Clone the repository
```bash
git clone https://github.com/bhanu3009/EduLibrary.git
cd EduLibrary
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
Create a `.env` file in the root directory (use `.env.example` as a reference):
```
SECRET_KEY=your_jwt_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
DATABASE_URL=sqlite:///./edulibrary.db
```
> ⚠️ Never commit your real `.env` file. It's excluded via `.gitignore`.

### 5. Start the development server
```bash
uvicorn app.main:app --reload
```
The app will be available at `http://127.0.0.1:8000`

---

## 🔐 Security Design Notes

Built as a security-focused portfolio piece. Key decisions:

- **HttpOnly cookies over localStorage** for JWT storage, reducing exposure to XSS-based token theft
- **RBAC checks enforced at the route/dependency level**, not just hidden in the UI
- **Pydantic schemas** validate and sanitize all incoming data before it touches the database layer
- **bcrypt (via passlib)** with per-user salts for password storage — no plaintext or reversible encryption
- Secrets are loaded exclusively from environment variables via `python-dotenv`, never hardcoded

---

## 📸 Screenshots
> Add screenshots or a demo GIF here once available — this significantly improves recruiter/reviewer engagement.

---

## 🗺️ Roadmap
- [ ] Migrate from SQLite to PostgreSQL for production
- [ ] Add Alembic for schema migrations
- [ ] Rate limiting on auth endpoints (slowapi)
- [ ] Automated overdue-book notifications (APScheduler)
- [ ] Secure headers (CSP, X-Frame-Options)
- [ ] Static security scan with Bandit
- [ ] Automated test coverage (pytest)
- [ ] CI/CD pipeline via GitHub Actions

---

## 👤 Author

**Bhanu**
Final-year B.Tech CSE (Cyber Security), Vignan's Institute of Information Technology
[https://www.linkedin.com/in/bhanu-prakash-thamiri-967ba0278/]

---

## 📄 License
This project is licensed under the MIT License.
