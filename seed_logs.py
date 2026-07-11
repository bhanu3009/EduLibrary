from database import SessionLocal
import models
import datetime

db = SessionLocal()

print("Scanning for users to attach logs to...")
admin = db.query(models.User).filter(models.User.profession == "Admin").first()
admin_id = admin.id if admin else None

student = db.query(models.User).filter(models.User.profession != "Admin").first()
student_id = student.id if student else None

print("Injecting historical security data...")
logs_to_add = [
    {"user_id": None, "action": "Failed Login Attempt - Invalid Credentials", "ip": "45.22.19.102", "days": 4},
    {"user_id": admin_id, "action": "Successful Admin Login", "ip": "192.168.1.10", "days": 4},
    {"user_id": admin_id, "action": "Added New Book: 'The Web Application Hacker's Handbook'", "ip": "192.168.1.10", "days": 3},
    {"user_id": student_id, "action": "Registered Account", "ip": "10.0.0.45", "days": 2},
    {"user_id": None, "action": "Unauthorized Access Blocked (Attempted /admin)", "ip": "103.45.22.9", "days": 2},
    {"user_id": student_id, "action": "Joined Waitlist for 'Python Crash Course'", "ip": "10.0.0.45", "days": 1},
    {"user_id": admin_id, "action": "System: Triggered Cron Job (Calculate Active Fines)", "ip": "127.0.0.1", "days": 0},
    {"user_id": admin_id, "action": "Successful Admin Login", "ip": "192.168.1.10", "days": 0}
]

for log in logs_to_add:
    new_log = models.AuditLog(
        user_id=log["user_id"],
        action=log["action"],
        ip_address=log["ip"],
        # Subtracting days so it looks like it happened over the last week
        timestamp=datetime.datetime.utcnow() - datetime.timedelta(days=log["days"]) 
    )
    db.add(new_log)

db.commit()
print("Matrix populated! You can now delete this file and refresh your dashboard.")