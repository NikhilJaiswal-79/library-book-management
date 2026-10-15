# Library Book Usage Analysis & Circulation System

A modern library circulation management and usage analytics web platform built with **Python**, **FastAPI**, **Pandas**, **NumPy**, **Chart.js**, and a responsive Single-Page Application (SPA).

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Backend Framework** | **FastAPI & Uvicorn** | High-performance asynchronous REST API server |
| **Language** | **Python 3.10+ / 3.14** | Core backend logic and transactions |
| **Relational Database** | **MySQL Server 8.0+** | Sole database backend; the schema is created automatically on first run |
| **Database Driver** | **`mysql-connector-python`** | Connects Python to MySQL database |
| **Configuration** | **`python-dotenv`** | Credentials are loaded from a git-ignored `.env` file |
| **Data Analysis** | **`pandas`** | Category aggregations and monthly circulation groupings |
| **Statistical Analysis** | **`numpy`** | Descriptive statistics (mean, median, standard deviation, quartiles, IQR) |
| **Data Visualization** | **`Chart.js` (HTML5 Canvas)** | Dynamic, interactive vector charts with tooltips and animations (**no static images**) |
| **Web Frontend** | **HTML5, CSS3, JavaScript (SPA)** | Glassmorphism design system with real-time stats, search filters, and live book preview |

---

## 🌐 Web Interface Features & Navigation

The web platform is accessible at **`http://127.0.0.1:8000`** with intuitive sidebar navigation:

### 1. 📊 Dashboard (`#dashboard`)
* **Real-time KPI Tiles**: Tracks Total Titles, Copies In Stock, Active Loans, Overdue Loans, and Return Rate (%).
* **Interactive Preview Vector Charts**: Live Chart.js bar and line charts (no static images!).
* **Active Loans Priority Queue**: Real-time loan countdown and overdue badges (`🔴 11 Days Overdue` / `🟢 Active`).

### 2. 📖 Book Catalogue (`#books`)
* **Live Search**: Instant filtering by title, author, category, or ISBN.
* **Category Filter**: Filter books by genre (Computer Science, Fiction, Science, Mathematics, etc.).
* **Stock Indicators**: Shows real-time stock pills (`● In Stock` / `● Out of Stock`).
* **Quick Issue Shortcut**: Click **Issue →** on any available book to pre-select it in the checkout desk.

### 3. ➕ Add New Book (`#addBook`) — *New Dedicated View*
* **Direct Sidebar Access**: Dedicated navigation tab to quickly add books to the collection without opening modal popups.
* **Live Shelf Preview Card**: As you type the ISBN, Title, Author, Category, and Initial Copies, a live book card previews how the book will appear on the shelf.
* **Category Autocomplete**: Built-in datalist for common library categories.
* **Instant Catalogue Sync**: Automatically saves to the database and refreshes the catalogue.

### 4. 👥 Borrowers Directory (`#borrowers`)
* **Searchable Member Roster**: Search by student name or roll number.
* **Direct Checkout Link**: Issue books directly to a specific member with one click.
* **Register Borrower Modal**: Register new members with Name and Roll No.

### 5. 🔄 Circulation Desk (`#circulation`)
* **Issue Book Form**: Filtered dropdowns showing only books in stock, borrower picker, issue date selector, and configurable loan period.
* **Active Loans Table**: Real-time overdue alerts, search bar, and 1-click **Return Check-in** modal that instantly updates shelf stock.

### 6. 📈 Interactive Analytics & Charts (`#analytics`) — *Vector Charts & No Images*
* **7 Interactive Chart.js Vector Canvas Charts**:
  1. 🏆 **Top Most-Borrowed Books**: Horizontal bar chart with exact checkout frequencies and hover tooltips.
  2. 📅 **Monthly Circulation Trajectory**: Multi-line area chart tracking Total Checkouts, Returned Loans, and Overdue Loans.
  3. 🍩 **Circulation Share by Genre**: Interactive doughnut chart with percentage breakdown.
  4. ⏱️ **Loan Duration Frequency Distribution**: NumPy-binned histogram bar chart (1-7d, 8-14d, 15-21d, 22+d).
  5. 👥 **Most Active Borrowers Leaderboard**: Ranks readers with the highest borrow count.
  6. 📦 **Inventory Allocation & Stock Health**: Shelf available copies vs copies currently checked out.
  7. 🎯 **Return Punctuality Breakdown**: On-time returns vs late returns vs active loans.
* **Pandas Data Tables**: Top Borrowed Books leaderboard, Category circulation summary, and Monthly loan history.

---

## 📁 Project Directory Structure

```text
Library Book Management/
├── config.py                 # MySQL settings (read from .env) and loan duration rules
├── database.py               # MySQL connection handling and schema initialization
├── operations.py             # Book/borrower CRUD and transaction business rules
├── analytics.py              # Pandas grouping, NumPy statistics, and distributions
├── seed_data.py              # Realistic sample data generator (books, borrowers, loans)
├── server.py                 # FastAPI Web Server and REST API router
├── main.py                   # Optional Terminal CLI menu and automated test runner
├── requirements.txt          # Python dependencies
├── .env.example              # Template for the .env configuration file
├── .gitignore                # Excludes .env, __pycache__, and generated output
├── README.md                 # Project documentation
└── static/                   # Frontend assets
    ├── index.html            # Single Page Web Application markup with Chart.js
    ├── css/
    │   └── style.css         # Modern glassmorphism CSS design system & preview card styles
    └── js/
        └── app.js            # Chart.js vector rendering, routing, live preview & forms
```

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.10+**
- **MySQL Server 8.0+** running locally

### 1. Clone the Repository
```bash
git clone https://github.com/NikhilJaiswal-79/library-book-management.git
cd library-book-management
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure the Database
Copy the example environment file and fill in your MySQL credentials:
```bash
copy .env.example .env      # Windows
cp .env.example .env        # macOS / Linux
```
Then edit `.env`:
```ini
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=library_analysis_db
DEFAULT_LOAN_DAYS=14
```
> `.env` is git-ignored — your password is never committed to the repository.
> The `library_analysis_db` database and all three tables are created automatically on first run.

### 4. Load the Sample Data
```bash
python seed_data.py
```
This inserts 12 books, 7 borrowers, and 20 realistic circulation records so the dashboard and charts have something to display.

### 5. Start the Web Server
```powershell
python server.py
```
Open your browser and navigate to:
👉 **`http://127.0.0.1:8000`**

To explore and test the interactive API documentation:
👉 **`http://127.0.0.1:8000/docs`**

---

## 💻 Terminal CLI Mode

The same functionality is also available from an interactive terminal menu:

```bash
python main.py
```

---

## 🔌 REST API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/status` | Health check and active database backend |
| `GET` | `/api/books` | List all books |
| `POST` | `/api/books` | Add a new book to the catalogue |
| `GET` | `/api/borrowers` | List all borrowers |
| `POST` | `/api/borrowers` | Register a new borrower |
| `GET` | `/api/loans/active` | Active loans with overdue status |
| `POST` | `/api/loans/issue` | Issue a book to a borrower |
| `POST` | `/api/loans/return` | Record a book return |
| `GET` | `/api/kpis` | Headline circulation and stock KPIs |
| `GET` | `/api/analytics/popular` | Most-borrowed books leaderboard |
| `GET` | `/api/analytics/categories` | Category circulation summary |
| `GET` | `/api/analytics/trends` | Monthly borrowing trajectory |
| `GET` | `/api/analytics/statistics` | Loan duration statistics (NumPy) |
| `GET` | `/api/analytics/duration-distribution` | Binned loan duration frequencies |
| `GET` | `/api/analytics/top-borrowers` | Most active borrowers |
| `GET` | `/api/analytics/inventory-health` | Stock vs. checked-out allocation |
| `GET` | `/api/analytics/punctuality` | On-time vs. late return breakdown |
| `POST` | `/api/seed` | Reset and reload sample data |

---

## 🔐 Security Notes

- Never commit a real password. Credentials live in `.env`, which is excluded by `.gitignore`.
- `.env.example` is committed as a template and contains no secrets.
- In production, use a dedicated MySQL user with privileges scoped to this database rather than `root`.
