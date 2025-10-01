# 🏋️ Gym Management Software

## 📄 Project Overview
**Gym Management Software** is a lightweight, desktop-based application built with **Python** and **Tkinter** for GUI. It automates gym operations for small to medium-sized gyms, including:

- Member registration & management
- Payments & subscription tracking
- Attendance tracking
- Reports & analytics
- WhatsApp notifications

Data is stored locally in **SQLite** (`gym.db`) for easy backup and portability.

**Key Goals:**
- Simplify daily tasks like adding members and marking attendance.
- Provide analytics and CSV exports for business insights.
- Integrate WhatsApp for automated welcome and renewal messages.
- Customizable via `.env` for multi-gym use (name, currency, theme).

**Current Date in App:** October 01, 2025 (hardcoded for testing; `datetime.now()` in production).

---

## ✨ Features

| Feature | Description | Icons |
|---------|------------|-------|
| 👥 Member Management | Add/update/delete members with unique phone validation. Auto-calculate expiry based on subscription plans. Country code support (+91 default). | 📱 Phone, 📅 Dates, 🆔 ID |
| 💰 Payment Management | Record payments linked to members. Supports manual/online methods. View history. | 💳 Method, 💵 Amount, 📊 Currency (₹ default) |
| 📅 Attendance Tracking | Mark Present/Absent with date. Prevents duplicates. Color-coded rows (Green: Present, Red: Absent). | ✅ Present, ❌ Absent, 📋 History |
| 📊 Reports & Analytics | View/export data to CSV. Charts: Monthly Revenue (Line), Active/Inactive Pie, Attendance Trend (Bar). | 📈 Charts, 📤 Export, 🔍 Filter |
| 📱 WhatsApp Integration | Auto-send welcome messages on registration and renewal reminders. Sent from gym phone. | 💬 Messages, 📲 +91 India Focus |
| ⚙️ Settings | Manage subscription plans, update gym info (name, address, currency, theme) via `.env`. | 🛠️ Customize, 💰 Plans |
| 💾 Backup & Auto-Maintenance | Manual/auto-backup DB. Auto-delete backups >7 days old on startup. | 🔄 Cleanup, 📁 .db Files |

---

## 🛠️ Tech Stack

- **Language:** Python 3.8+
- **GUI:** Tkinter
- **Database:** SQLite (`gym.db`)
- **Data Export/Charts:** Pandas, Matplotlib
- **Notifications:** PyWhatKit (WhatsApp via Chrome)
- **Env Management:** python-dotenv (`.env`)
- **Dependencies:** `pandas`, `matplotlib`, `pywhatkit`, `python-dotenv`

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8+ ([Download](https://www.python.org/downloads/))
- Chrome browser (for WhatsApp integration)

### Step-by-Step Setup
1. **Clone/Download Project**
```bash
git clone <repo-url>
cd gym-management-software

2. Create Virtual Environment
python -m venv gym_env
# Activate:
# Windows: gym_env\Scripts\activate
# macOS/Linux: source gym_env/bin/activate

3.Install Dependencies
pip install pandas matplotlib pywhatkit python-dotenv
pip freeze > requirements.txt

4.Configure .env File (Create in project root)
GYM_NAME=Vivek Fitness Center
GYM_ADDRESS=123 Gym Road, Mumbai, Maharashtra 400001
GYM_PHONE=916238100393  # digits only
CURRENCY_SYMBOL=₹
THEME_COLOR=#e8f4fd

5.Run the App
python gym_app.py

- Tabs: Members, Payments, Attendance, Reports, Settings

- First run auto-creates gym.db and default plans.




## 📖 Usage Guide

### 1. Adding a Member
- Enter Name, Country Code (+91), Phone (10 digits)
- Join Date auto-today, select Plan ID
- Click **Add Member** → WhatsApp welcome sent automatically

### 2. Recording Payments
- Enter Member ID, Amount, Method, Date
- Click **Add Payment** → updates list

### 3. Marking Attendance
- Enter Member ID, Status (Present/Absent), Date
- Click **Mark Attendance** → row color updates

### 4. Generating Reports
- View data in tabs
- Export CSV with timestamps
- Generate charts (requires data)

### 5. Settings
- Add/Delete Plans
- Update Gym Info and Phone (restart for theme updates)

### 6. Auto Features
- Renewal WhatsApp on startup
- Auto-backup + cleanup old DB files

---

## 🧪 Test Cases

| ID    | Feature           | Steps               | Expected                               |
|-------|-----------------|-------------------|----------------------------------------|
| TC-01 | Add Member        | Valid name & phone | Success popup, WhatsApp sent           |
| TC-02 | Invalid Phone     | 9 digits           | Error popup, not added                 |
| TC-03 | WhatsApp          | Valid member       | Welcome message sent                   |
| TC-04 | Attendance Color  | Mark Present/Absent| Green row / Red row                     |
| TC-05 | Renewal Auto      | Expiry today       | Popup: "Sent 1 renewal"               |
| TC-06 | Export            | Add data, export   | CSV with correct columns               |
| TC-07 | Backup            | Click Backup       | Timestamped .db, old deleted          |
| TC-08 | Settings          | Add plan           | Plan appears in list                   |
| TC-09 | Multi-Gym         | Change .env GYM_NAME | Header updates, messages include new name |

> Verify DB with SQLite CLI:  
> `sqlite3 gym.db` → `SELECT * FROM members;`

---

## 🤝 Contributing
1. Fork the repo  
2. Create a branch: `git checkout -b feature/add-sms`  
3. Commit: `git commit -m "Add Twilio SMS"`  
4. Push: `git push origin feature/add-sms`  
5. Open a Pull Request  

> Report issues with screenshots/error logs.

---

## 📄 Full Documentation

**Database Schema**
- `members`: id, name, phone, join_date, expiry_date  
- `payments`: id, member_id, payment_date, amount, method  
- `attendance`: id, member_id, att_date, status  
- `subscription_plans`: id, duration_months, price, description  

**Internal Methods**
- `add_member()`: Validates phone, sends WhatsApp  
- `refresh_members()`: Colors rows  
- `check_and_send_renewals()`: Sends expiry notifications  
- `auto_backup_and_cleanup()`: Backup & cleanup old DB  

**Customization**
- `.env` for gym info, theme, currency  
- Restart app after changes  
- Icons & emojis supported in tabs  

**Limitations**
- WhatsApp requires Chrome  
- Dates approximate months (30 days)  
- No online payments (future: Stripe/Twilio)  
- Local-only; no multi-user sync  

---

## 📋 License
**MIT License** – Free to use/modify. See LICENSE file.

Built with ❤️ by Grok (xAI). Questions? Check code or open an issue! 🚀
