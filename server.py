"""
FastAPI Web Server for Library Book Usage Analysis System.
Exposes REST APIs for Books, Borrowers, Circulation, Analytics, and Visualizations,
while serving the modern single-page web interface.
"""

import os
from datetime import date
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

import database
import operations
import analytics
import seed_data
from config import CHARTS_DIR, DEFAULT_LOAN_DAYS

# Initialize database tables on server startup
database.initialize_database()

app = FastAPI(
    title="Library Book Usage Analysis API",
    description="Circulation and Usage Analytics Web Platform",
    version="1.0.0"
)

# Static directory setup
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, "css"), exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, "js"), exist_ok=True)
os.makedirs(CHARTS_DIR, exist_ok=True)

# Mount static folder
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# ==================== Request Models ====================

class BookCreateRequest(BaseModel):
    isbn: str
    title: str
    author: str
    category: str
    copies_available: int = 1


class BorrowerCreateRequest(BaseModel):
    borrower_name: str
    roll_no: str


class IssueBookRequest(BaseModel):
    book_id: int
    borrower_id: int
    issue_date: Optional[str] = None
    loan_days: Optional[int] = DEFAULT_LOAN_DAYS


class ReturnBookRequest(BaseModel):
    loan_id: int
    return_date: Optional[str] = None


# ==================== Frontend Root ====================

@app.get("/")
def read_root():
    """Serves the main single-page web application."""
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return HTMLResponse("<h1>Library Book Analysis System</h1><p>Frontend static files loading...</p>")


# ==================== REST API Endpoints ====================

@app.get("/api/status")
def get_system_status():
    """Returns database backend and system health."""
    conn = database.get_raw_connection()
    conn.close()
    return {
        "status": "online",
        "database_backend": "MYSQL",
        "today": str(date.today()),
        "default_loan_days": DEFAULT_LOAN_DAYS
    }


@app.get("/api/kpis")
def get_kpis():
    """Returns high-level circulation and stock KPIs."""
    try:
        return analytics.get_library_kpis()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/books")
def list_books():
    """Retrieves all books."""
    raw = operations.get_all_books()
    books = []
    for r in raw:
        books.append({
            "book_id": r[0],
            "isbn": r[1],
            "title": r[2],
            "author": r[3],
            "category": r[4],
            "copies_available": r[5]
        })
    return books


@app.post("/api/books")
def create_book(req: BookCreateRequest):
    """Registers a new book in the catalogue."""
    success, message = operations.add_book(
        req.isbn, req.title, req.author, req.category, req.copies_available
    )
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"success": True, "message": message}


@app.get("/api/borrowers")
def list_borrowers():
    """Retrieves all registered borrowers."""
    raw = operations.get_all_borrowers()
    borrowers = []
    for r in raw:
        borrowers.append({
            "borrower_id": r[0],
            "borrower_name": r[1],
            "roll_no": r[2]
        })
    return borrowers


@app.post("/api/borrowers")
def create_borrower(req: BorrowerCreateRequest):
    """Registers a new borrower."""
    success, message = operations.add_borrower(req.borrower_name, req.roll_no)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"success": True, "message": message}


@app.get("/api/loans/active")
def list_active_loans():
    """Retrieves all active unreturned loans with overdue status."""
    return operations.get_active_loans()


@app.post("/api/loans/issue")
def issue_book_endpoint(req: IssueBookRequest):
    """Issues a book to a borrower with validation."""
    success, message = operations.issue_book(
        req.book_id, req.borrower_id, req.issue_date, req.loan_days
    )
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"success": True, "message": message}


@app.post("/api/loans/return")
def return_book_endpoint(req: ReturnBookRequest):
    """Records the return of an issued book."""
    success, message = operations.return_book(
        req.loan_id, req.return_date
    )
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"success": True, "message": message}


# ==================== Analytics Endpoints ====================

@app.get("/api/analytics/popular")
def get_popular_books(limit: int = 10):
    """Returns top borrowed books."""
    df = analytics.get_most_borrowed_books_df(limit=limit)
    return df.to_dict(orient="records")


@app.get("/api/analytics/overdue")
def get_overdue_loans():
    """Returns all overdue loans."""
    df = analytics.get_overdue_loans_df()
    return df.to_dict(orient="records")


@app.get("/api/analytics/categories")
def get_category_summary():
    """Returns category circulation summary."""
    df = analytics.get_category_summary_df()
    return df.to_dict(orient="records")


@app.get("/api/analytics/trends")
def get_monthly_trends():
    """Returns monthly borrowing trajectory."""
    df = analytics.get_monthly_borrowing_trends_df()
    return df.to_dict(orient="records")


@app.get("/api/analytics/statistics")
def get_loan_statistics():
    """Returns loan duration descriptive statistics (NumPy)."""
    return analytics.calculate_loan_statistics()


@app.get("/api/analytics/duration-distribution")
def get_duration_distribution():
    """Returns binned loan duration frequencies (NumPy)."""
    return analytics.get_loan_duration_distribution()


@app.get("/api/analytics/top-borrowers")
def get_top_borrowers(limit: int = 8):
    """Returns most active borrowers."""
    df = analytics.get_top_borrowers_df(limit=limit)
    return df.to_dict(orient="records")


@app.get("/api/analytics/inventory-health")
def get_inventory_health():
    """Returns stock vs checkout allocation."""
    return analytics.get_inventory_health()


@app.get("/api/analytics/punctuality")
def get_punctuality():
    """Returns return timeliness breakdown."""
    return analytics.get_return_punctuality()


@app.post("/api/seed")
def seed_database(reset: bool = True):
    """Populates or resets sample data."""
    try:
        seed_data.populate_sample_data(force_reset=reset)
        return {"success": True, "message": "Sample library data successfully populated."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/charts/generate")
def generate_all_charts():
    """Generates and updates Matplotlib charts."""
    try:
        p1 = analytics.plot_popular_books()
        p2 = analytics.plot_monthly_trends()
        p3 = analytics.plot_category_distribution()
        return {
            "success": True,
            "charts": {
                "popular_books": "/api/charts/popular_books_chart.png",
                "monthly_trends": "/api/charts/monthly_borrowing_trends.png",
                "category_distribution": "/api/charts/category_distribution_chart.png"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/charts/{chart_name}")
def get_chart_image(chart_name: str):
    """Serves the generated chart images."""
    file_path = os.path.join(CHARTS_DIR, chart_name)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="image/png")
    raise HTTPException(status_code=404, detail="Chart not found. Call /api/charts/generate first.")


if __name__ == "__main__":
    import uvicorn
    print("\nStarting Library Book Usage Analysis Web Server...")
    print("Web Interface URL: http://127.0.0.1:8000")
    print("API Documentation: http://127.0.0.1:8000/docs\n")
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
