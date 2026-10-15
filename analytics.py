"""
Data Analysis and Visualization Module.
Uses Pandas for data grouping/summaries, NumPy for descriptive statistics,
and Matplotlib for charting borrowing trends and popular books.
"""

import os
from datetime import date, datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from database import Database
from config import CHARTS_DIR


def get_most_borrowed_books_df(limit: int = 10) -> pd.DataFrame:
    """
    Identifies the most-borrowed books ranked by loan frequency.
    """
    query = """
    SELECT 
        b.book_id,
        b.isbn,
        b.title,
        b.author,
        b.category,
        b.copies_available,
        COUNT(l.loan_id) AS borrow_count
    FROM books b
    LEFT JOIN loans l ON b.book_id = l.book_id
    GROUP BY b.book_id, b.isbn, b.title, b.author, b.category, b.copies_available
    ORDER BY borrow_count DESC, b.title ASC
    """
    df = Database.get_dataframe(query)
    if not df.empty:
        df["borrow_count"] = df["borrow_count"].astype(int)
        return df.head(limit)
    return df


def get_overdue_loans_df() -> pd.DataFrame:
    """
    Summarizes all currently overdue loans where return_date is NULL and due_date < today.
    """
    query = """
    SELECT 
        l.loan_id,
        b.title AS book_title,
        b.category,
        br.borrower_name,
        br.roll_no,
        l.issue_date,
        l.due_date
    FROM loans l
    JOIN books b ON l.book_id = b.book_id
    JOIN borrowers br ON l.borrower_id = br.borrower_id
    WHERE l.return_date IS NULL
    """
    df = Database.get_dataframe(query)
    if df.empty:
        return pd.DataFrame(columns=["loan_id", "book_title", "category", "borrower_name", "roll_no", "issue_date", "due_date", "days_overdue"])

    # Calculate days overdue using Pandas and current date
    today = pd.to_datetime(date.today())
    df["due_date_dt"] = pd.to_datetime(df["due_date"])
    df["days_overdue"] = (today - df["due_date_dt"]).dt.days

    # Filter only those that are overdue (days_overdue > 0)
    overdue_df = df[df["days_overdue"] > 0].copy()
    overdue_df.sort_values(by="days_overdue", ascending=False, inplace=True)
    overdue_df.drop(columns=["due_date_dt"], inplace=True)
    return overdue_df


def get_category_summary_df() -> pd.DataFrame:
    """
    Generates a category-wise summary using Pandas:
    - Number of distinct book titles
    - Total available inventory
    - Total borrowing circulation count
    - Popularity percentage
    """
    query = """
    SELECT 
        b.category,
        b.book_id,
        b.copies_available,
        l.loan_id
    FROM books b
    LEFT JOIN loans l ON b.book_id = l.book_id
    """
    raw_df = Database.get_dataframe(query)
    if raw_df.empty:
        return pd.DataFrame(columns=["Category", "Total Titles", "Available Copies", "Total Borrowed", "Circulation Share (%)"])

    summary = raw_df.groupby("category").agg(
        total_titles=("book_id", "nunique"),
        available_copies=("copies_available", "max"),  # per distinct book
        total_borrowed=("loan_id", "count")
    ).reset_index()

    # Re-calculate correct available copies by distinct books
    books_stock = Database.get_dataframe("SELECT category, copies_available FROM books")
    if not books_stock.empty:
        stock_sum = books_stock.groupby("category")["copies_available"].sum().reset_index()
        summary = summary.drop(columns=["available_copies"]).merge(stock_sum, on="category", how="left")

    total_loans = summary["total_borrowed"].sum()
    if total_loans > 0:
        summary["circulation_share"] = (summary["total_borrowed"] / total_loans * 100).round(1)
    else:
        summary["circulation_share"] = 0.0

    summary.rename(columns={
        "category": "Category",
        "total_titles": "Total Titles",
        "copies_available": "Available Copies",
        "total_borrowed": "Times Borrowed",
        "circulation_share": "Circulation Share (%)"
    }, inplace=True)

    return summary.sort_values(by="Times Borrowed", ascending=False)


def get_monthly_borrowing_trends_df() -> pd.DataFrame:
    """
    Summarizes monthly borrowing volume and completion status using Pandas.
    """
    query = "SELECT loan_id, issue_date, due_date, return_date FROM loans"
    df = Database.get_dataframe(query)
    if df.empty:
        return pd.DataFrame(columns=["Year-Month", "Total Loans", "Returned", "Active / Pending", "Overdue"])

    df["issue_dt"] = pd.to_datetime(df["issue_date"])
    df["due_dt"] = pd.to_datetime(df["due_date"])
    df["year_month"] = df["issue_dt"].dt.to_period("M").astype(str)

    today = pd.to_datetime(date.today())
    df["is_returned"] = df["return_date"].notnull()
    df["is_overdue"] = df["return_date"].isnull() & (df["due_dt"] < today)

    trends = df.groupby("year_month").agg(
        total_loans=("loan_id", "count"),
        returned=("is_returned", "sum"),
        overdue=("is_overdue", "sum")
    ).reset_index()

    trends["active_pending"] = trends["total_loans"] - trends["returned"]
    trends.rename(columns={"year_month": "Year-Month", "total_loans": "Total Loans", "returned": "Returned", "active_pending": "Active / Pending", "overdue": "Overdue"}, inplace=True)
    return trends.sort_values(by="Year-Month")


def calculate_loan_statistics() -> dict:
    """
    Calculates descriptive statistics using NumPy:
    - Duration of completed loans (days)
    - Mean, Median, Standard Deviation, Min, Max, and Percentiles
    """
    query = """
    SELECT issue_date, return_date 
    FROM loans 
    WHERE return_date IS NOT NULL
    """
    df = Database.get_dataframe(query)

    if df.empty:
        return {
            "completed_loans_count": 0,
            "mean_days": 0.0,
            "median_days": 0.0,
            "std_dev_days": 0.0,
            "min_days": 0,
            "max_days": 0,
            "q25_days": 0.0,
            "q75_days": 0.0
        }

    issue_dates = pd.to_datetime(df["issue_date"])
    return_dates = pd.to_datetime(df["return_date"])
    durations = (return_dates - issue_dates).dt.days.to_numpy()

    stats = {
        "completed_loans_count": int(len(durations)),
        "mean_days": float(np.mean(durations)),
        "median_days": float(np.median(durations)),
        "std_dev_days": float(np.std(durations)),
        "variance_days": float(np.var(durations)),
        "min_days": int(np.min(durations)),
        "max_days": int(np.max(durations)),
        "q25_days": float(np.percentile(durations, 25)),
        "q75_days": float(np.percentile(durations, 75)),
        "iqr_days": float(np.percentile(durations, 75) - np.percentile(durations, 25))
    }
    return stats


def get_loan_duration_distribution() -> dict:
    """
    Computes frequency distribution of completed loan durations using NumPy.
    Bins: 1-7 days, 8-14 days, 15-21 days, 22+ days.
    """
    query = "SELECT issue_date, return_date FROM loans WHERE return_date IS NOT NULL"
    df = Database.get_dataframe(query)
    labels = ["1-7 Days (Quick)", "8-14 Days (Standard)", "15-21 Days (Extended)", "22+ Days (Long)"]
    if df.empty:
        return {"labels": labels, "counts": [0, 0, 0, 0]}

    issue_dates = pd.to_datetime(df["issue_date"])
    return_dates = pd.to_datetime(df["return_date"])
    durations = (return_dates - issue_dates).dt.days.to_numpy()

    c1 = int(np.sum((durations >= 1) & (durations <= 7)))
    c2 = int(np.sum((durations >= 8) & (durations <= 14)))
    c3 = int(np.sum((durations >= 15) & (durations <= 21)))
    c4 = int(np.sum(durations >= 22))

    return {
        "labels": labels,
        "counts": [c1, c2, c3, c4]
    }


def get_top_borrowers_df(limit: int = 8) -> pd.DataFrame:
    """
    Identifies the most active borrowers/readers.
    """
    query = """
    SELECT 
        br.borrower_id,
        br.borrower_name,
        br.roll_no,
        COUNT(l.loan_id) AS total_borrows,
        SUM(CASE WHEN l.return_date IS NULL THEN 1 ELSE 0 END) AS active_loans
    FROM borrowers br
    LEFT JOIN loans l ON br.borrower_id = l.borrower_id
    GROUP BY br.borrower_id, br.borrower_name, br.roll_no
    ORDER BY total_borrows DESC, br.borrower_name ASC
    """
    df = Database.get_dataframe(query)
    if not df.empty:
        df["total_borrows"] = df["total_borrows"].fillna(0).astype(int)
        df["active_loans"] = df["active_loans"].fillna(0).astype(int)
        return df.head(limit)
    return df


def get_inventory_health() -> dict:
    """
    Returns total copies owned, copies available, copies on loan, and utilization rate.
    """
    books_df = Database.get_dataframe("SELECT copies_available FROM books")
    active_loans_count = Database.fetchone("SELECT COUNT(*) FROM loans WHERE return_date IS NULL")[0]

    available_copies = int(books_df["copies_available"].sum()) if not books_df.empty else 0
    total_copies = available_copies + active_loans_count
    utilization_rate = round((active_loans_count / total_copies * 100), 1) if total_copies > 0 else 0.0

    return {
        "total_copies": total_copies,
        "available_copies": available_copies,
        "on_loan_copies": active_loans_count,
        "utilization_rate": utilization_rate
    }


def get_return_punctuality() -> dict:
    """
    Breaks down return timeliness:
    - Returned On Time
    - Returned Late
    - Currently Active (On Time)
    - Currently Overdue
    """
    query = "SELECT loan_id, issue_date, due_date, return_date FROM loans"
    df = Database.get_dataframe(query)
    if df.empty:
        return {
            "returned_on_time": 0,
            "returned_late": 0,
            "active_on_time": 0,
            "active_overdue": 0
        }

    today = pd.to_datetime(date.today())
    df["due_dt"] = pd.to_datetime(df["due_date"])
    df["ret_dt"] = pd.to_datetime(df["return_date"])

    # Completed loans
    completed = df[df["return_date"].notnull()].copy()
    returned_on_time = int((completed["ret_dt"] <= completed["due_dt"]).sum())
    returned_late = int((completed["ret_dt"] > completed["due_dt"]).sum())

    # Active loans
    active = df[df["return_date"].isnull()].copy()
    active_overdue = int((active["due_dt"] < today).sum())
    active_on_time = int((active["due_dt"] >= today).sum())

    return {
        "returned_on_time": returned_on_time,
        "returned_late": returned_late,
        "active_on_time": active_on_time,
        "active_overdue": active_overdue
    }


def get_library_kpis() -> dict:
    """
    Returns general high-level circulation and stock KPIs.
    """
    books_df = Database.get_dataframe("SELECT copies_available FROM books")
    loans_df = Database.get_dataframe("SELECT loan_id, due_date, return_date FROM loans")
    borrowers_count = Database.fetchone("SELECT COUNT(*) FROM borrowers")[0]

    total_titles = len(books_df)
    available_copies = int(books_df["copies_available"].sum()) if not books_df.empty else 0

    total_loans = len(loans_df)
    if total_loans > 0:
        active_loans = int(loans_df["return_date"].isnull().sum())
        returned_loans = int(loans_df["return_date"].notnull().sum())

        today = pd.to_datetime(date.today())
        loans_df["due_dt"] = pd.to_datetime(loans_df["due_date"])
        overdue_count = int((loans_df["return_date"].isnull() & (loans_df["due_dt"] < today)).sum())
        return_rate = round((returned_loans / total_loans) * 100, 1)
    else:
        active_loans = 0
        returned_loans = 0
        overdue_count = 0
        return_rate = 0.0

    return {
        "total_titles": total_titles,
        "available_copies": available_copies,
        "registered_borrowers": borrowers_count,
        "total_loans": total_loans,
        "active_loans": active_loans,
        "returned_loans": returned_loans,
        "overdue_loans": overdue_count,
        "return_rate": return_rate
    }


# ==================== Matplotlib Visualization Functions ====================

def plot_popular_books(top_n: int = 5, show_plot: bool = False) -> str:
    """
    Creates and saves a bar chart of the most-borrowed books.
    Returns the file path of the saved PNG image.
    """
    df = get_most_borrowed_books_df(limit=top_n)
    if df.empty or df["borrow_count"].sum() == 0:
        return ""

    os.makedirs(CHARTS_DIR, exist_ok=True)
    file_path = os.path.join(CHARTS_DIR, "popular_books_chart.png")

    plt.figure(figsize=(9, 5))
    plt.style.use("ggplot" if "ggplot" in plt.style.available else "default")

    # Shorten titles if too long for clean display
    titles = [t[:25] + "..." if len(t) > 25 else t for t in df["title"]]
    counts = df["borrow_count"]

    bars = plt.barh(titles[::-1], counts[::-1], color="#3b82f6", edgecolor="#1d4ed8", alpha=0.85)
    plt.xlabel("Number of Times Borrowed", fontsize=11, fontweight="bold")
    plt.title(f"Top {len(df)} Most Borrowed Books", fontsize=13, fontweight="bold", pad=12)
    plt.grid(axis="x", linestyle="--", alpha=0.6)

    # Add count labels on the bars
    for bar in bars:
        width = bar.get_width()
        plt.text(width + 0.1, bar.get_y() + bar.get_height() / 2, f"{int(width)}",
                 va="center", ha="left", fontsize=10, fontweight="bold", color="#1e293b")

    plt.tight_layout()
    plt.savefig(file_path, dpi=200)
    if show_plot:
        plt.show()
    plt.close()
    return file_path


def plot_monthly_trends(show_plot: bool = False) -> str:
    """
    Creates and saves a line chart for monthly borrowing circulation trends.
    Returns the file path of the saved PNG image.
    """
    df = get_monthly_borrowing_trends_df()
    if df.empty:
        return ""

    os.makedirs(CHARTS_DIR, exist_ok=True)
    file_path = os.path.join(CHARTS_DIR, "monthly_borrowing_trends.png")

    plt.figure(figsize=(9, 5))
    plt.style.use("ggplot" if "ggplot" in plt.style.available else "default")

    months = df["Year-Month"]
    total = df["Total Loans"]
    returned = df["Returned"]

    plt.plot(months, total, marker="o", linewidth=2.5, color="#2563eb", label="Total Loans")
    plt.plot(months, returned, marker="s", linewidth=2, linestyle="--", color="#10b981", label="Returned Loans")

    plt.xlabel("Month (Year-Month)", fontsize=11, fontweight="bold")
    plt.ylabel("Number of Loans", fontsize=11, fontweight="bold")
    plt.title("Monthly Library Circulation Trends", fontsize=13, fontweight="bold", pad=12)
    plt.xticks(rotation=45)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend(frameon=True)

    # Add data point labels
    for i, txt in enumerate(total):
        plt.annotate(str(txt), (months.iloc[i], total.iloc[i] + 0.2), ha="center", fontsize=9, fontweight="bold")

    plt.tight_layout()
    plt.savefig(file_path, dpi=200)
    if show_plot:
        plt.show()
    plt.close()
    return file_path


def plot_category_distribution(show_plot: bool = False) -> str:
    """
    Creates and saves a donut chart of circulation distribution by book category.
    Returns the file path of the saved PNG image.
    """
    df = get_category_summary_df()
    if df.empty or df["Times Borrowed"].sum() == 0:
        return ""

    os.makedirs(CHARTS_DIR, exist_ok=True)
    file_path = os.path.join(CHARTS_DIR, "category_distribution_chart.png")

    plt.figure(figsize=(7, 7))
    categories = df["Category"]
    counts = df["Times Borrowed"]

    colors = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899", "#14b8a6"]
    plt.pie(
        counts,
        labels=categories,
        autopct="%1.1f%%",
        startangle=140,
        colors=colors[:len(categories)],
        wedgeprops=dict(width=0.45, edgecolor="white", linewidth=2),
        textprops=dict(fontsize=10, fontweight="bold")
    )
    plt.title("Borrowing Volume by Category", fontsize=13, fontweight="bold", pad=14)

    plt.tight_layout()
    plt.savefig(file_path, dpi=200)
    if show_plot:
        plt.show()
    plt.close()
    return file_path
