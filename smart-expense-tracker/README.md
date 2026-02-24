# 💸 ExpenseIQ — Smart Expense Tracker with Analytics

A **production-ready** full-stack web application for tracking personal expenses with interactive analytics.

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0-black?logo=flask)
![MySQL](https://img.shields.io/badge/MySQL-8.0+-orange?logo=mysql)
![Chart.js](https://img.shields.io/badge/Chart.js-4.4-ff6384?logo=chart.js)
![License](https://img.shields.io/badge/license-MIT-green)

---

## ✨ Features

| Feature | Detail |
|---|---|
| 🔐 **Secure Auth** | bcrypt password hashing, CSRF tokens, session management |
| 💰 **Expense CRUD** | Add, edit, delete — with date & category filters |
| 📊 **Analytics Dashboard** | Interactive Line + Doughnut charts (Chart.js) |
| 🗂️ **Normalised MySQL DB** | users → expenses → categories with FK constraints |
| 🛡️ **Security-first** | Parameterised queries, ownership checks, secure cookies |
| 📱 **Responsive UI** | Mobile sidebar, Google Fonts (Inter), premium design |

---

## 📁 Project Structure

```
smart-expense-tracker/
├── app.py                  # Application factory (create_app)
├── db.py                   # MySQL connection helper (mysql-connector-python)
├── extensions.py           # Bcrypt, LoginManager, CSRFProtect instances
├── schema.sql              # MySQL schema + seed data
├── requirements.txt
├── Procfile                # For Render / Heroku
├── .env.example            # Environment variable template
│
├── config/
│   └── settings.py         # Dev / Prod config classes
│
├── models/
│   ├── user.py             # User model (Flask-Login UserMixin)
│   └── expense.py          # Expense model + analytics queries
│
├── routes/
│   ├── auth.py             # POST /register  POST /login  GET /logout
│   ├── expenses.py         # CRUD + GET /api/analytics (JSON)
│   └── main.py             # GET /  GET /dashboard
│
├── templates/
│   ├── base.html           # Master layout (sidebar + topbar + modals)
│   ├── dashboard.html      # Analytics dashboard (Chart.js)
│   ├── auth/
│   │   ├── login.html      # Two-panel login page
│   │   └── register.html   # Two-panel registration page
│   ├── expenses/
│   │   ├── list.html       # Expense table with filter bar
│   │   └── form.html       # Add / Edit form
│   └── errors/
│       ├── 404.html
│       └── 500.html
│
└── static/
    ├── css/
    │   └── main.css        # Complete stylesheet (Inter, animations, responsive)
    └── js/
        ├── main.js         # Sidebar, password toggle, delete modal, alerts
        └── dashboard.js    # Chart.js charts + analytics (shimmer, count-up)
```

---

## 🚀 Local Setup (Step-by-Step)

### Prerequisites

| Tool | Version |
|---|---|
| Python | 3.11+ |
| MySQL | 8.0+ |
| pip | latest |

---

### Step 1 — Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/smart-expense-tracker.git
cd smart-expense-tracker
```

---

### Step 2 — Create & activate a virtual environment

**Windows (PowerShell)**
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

**macOS / Linux**
```bash
python3 -m venv venv
source venv/bin/activate
```

---

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

---

### Step 4 — Configure environment variables

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Edit `.env` and fill in your MySQL credentials:

```env
SECRET_KEY=your-random-secret-key-here
FLASK_ENV=development
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DB=smart_expense_tracker
```

> **Generate a secure SECRET_KEY:**
> ```bash
> python -c "import secrets; print(secrets.token_hex(32))"
> ```

---

### Step 5 — Create the MySQL database

Log in to MySQL and run the schema:

```bash
mysql -u root -p < schema.sql
```

Or paste `schema.sql` into **MySQL Workbench** / **phpMyAdmin**.

This creates:
- `smart_expense_tracker` database
- `users`, `categories`, `expenses` tables
- Seeds 6 default categories (Food, Travel, Shopping, Bills, Health, Others)

---

### Step 6 — Run the development server

```bash
flask run
```

Visit **http://localhost:5000** 🎉

---

## 🗄️ Database Schema

```sql
users       (id PK, username UNIQUE, email UNIQUE, password, created_at)
categories  (id PK, name UNIQUE)                     -- 6 defaults seeded
expenses    (id PK, user_id FK→users, category_id FK→categories,
             amount DECIMAL(10,2), description, date, created_at, updated_at)
```

**Relationships:**
- `expenses.user_id` → `users.id`  (CASCADE DELETE)
- `expenses.category_id` → `categories.id`  (RESTRICT DELETE)

---

## 📊 Analytics API

`GET /api/analytics` — authentication required. Returns JSON:

```json
{
  "monthly":      { "labels": ["2024-10", "2024-11"], "data": [1200.50, 980.00] },
  "category":     { "labels": ["Food", "Travel"],     "data": [450.00, 320.00] },
  "month_total":  1450.75,
  "top_category": { "name": "Food", "total": 450.00 },
  "recent": [
    { "id": 1, "amount": 120.00, "description": "Lunch", "date": "2024-11-01", "category": "Food" }
  ]
}
```

---

## 🔒 Security

| Threat | Mitigation |
|---|---|
| SQL Injection | Parameterised `%s` queries via mysql-connector |
| CSRF | Flask-WTF CSRF tokens on all forms + delete modal |
| XSS | Jinja2 auto-escaping + JS `escHtml()` in dashboard.js |
| Password Storage | bcrypt hashing (Flask-Bcrypt) |
| Session Hijacking | `SESSION_COOKIE_HTTPONLY`, `SameSite=Lax`, HTTPS in prod |
| Unauthorised Access | `@login_required` on all protected routes |
| Ownership Bypass | All queries filtered by `user_id` |

---

## ☁️ Deploy on Render (Recommended — Free Tier)

### 1. Push to GitHub

```bash
git add .
git commit -m "initial commit"
git push origin main
```

### 2. Create a free MySQL database

Use [Railway](https://railway.app) or [PlanetScale](https://planetscale.com):
- Create a MySQL database
- Import `schema.sql`
- Copy the connection credentials

### 3. Create a Web Service on Render

1. Go to [render.com](https://render.com) → **New Web Service**
2. Connect your GitHub repo
3. Set:
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`

### 4. Set Environment Variables in Render Dashboard

```
SECRET_KEY=<generate with secrets.token_hex(32)>
FLASK_ENV=production
MYSQL_HOST=<your-db-host>
MYSQL_PORT=3306
MYSQL_USER=<your-db-user>
MYSQL_PASSWORD=<your-db-password>
MYSQL_DB=smart_expense_tracker
```

### 5. Deploy

Render automatically builds and deploys on every push to `main`. ✅

---

## ☁️ Deploy on Heroku

```bash
heroku create your-app-name
heroku addons:create cleardb:ignite          # Free MySQL add-on

# Get DB URL and parse credentials
heroku config:get CLEARDB_DATABASE_URL

# Set all environment variables
heroku config:set \
  SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')" \
  FLASK_ENV=production \
  MYSQL_HOST="..." \
  MYSQL_USER="..." \
  MYSQL_PASSWORD="..." \
  MYSQL_DB="..."

# Import schema to ClearDB
mysql -u <user> -p<pass> -h <host> <db> < schema.sql

# Deploy
git push heroku main
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, Flask 3.0 |
| Database | MySQL 8.0 (InnoDB) |
| DB Driver | mysql-connector-python |
| Auth | Flask-Login, Flask-Bcrypt |
| Forms & CSRF | Flask-WTF, WTForms |
| Frontend | HTML5, CSS3 (Inter), Vanilla JS |
| Charts | Chart.js 4.4 |
| Deployment | Gunicorn, Render / Heroku |

---

## 📝 License

MIT — free for personal and commercial use.
