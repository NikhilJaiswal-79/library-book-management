"""
Interactive Terminal Menu (CLI) for Library Book Usage Analysis System.
Author: Library Systems Engineering
"""

import sys
import os
from datetime import date
from database import initialize_database, get_raw_connection
from config import DEFAULT_LOAN_DAYS, CHARTS_DIR
import operations
import analytics
import seed_data


def print_header(title: str):
    """Prints a styled banner for menus and sections."""
    print("\n" + "=" * 65)
    print(f" {title.upper()}")
    print("=" * 65)


def print_table(headers: list[str], rows: list, col_widths: list[int] = None):
    """Prints a nicely formatted ASCII table."""
    if not rows:
        print("  (No records found)")
        return

    if not col_widths:
        col_widths = []
        for i in range(len(headers)):
            max_len = len(str(headers[i]))
            for row in rows:
                if i < len(row):
                    max_len = max(max_len, len(str(row[i])))
            col_widths.append(min(max_len + 2, 40))

    header_str = " | ".join(str(h).ljust(col_widths[i]) for i, h in enumerate(headers))
    separator = "-+-".join("-" * col_widths[i] for i in range(len(headers)))
    print(header_str)
    print(separator)

    for row in rows:
        row_str = " | ".join(str(row[i])[:col_widths[i]].ljust(col_widths[i]) if i < len(row) else "".ljust(col_widths[i]) for i in range(len(headers)))
        print(row_str)


# ==================== Book Menu Handlers ====================

def handle_view_books():
    """Displays all books in the library."""
    print_header("Library Book Catalogue")
    books = operations.get_all_books()
    headers = ["ID", "ISBN", "Title", "Author", "Category", "Copies Left"]
    rows = [[b[0], b[1], b[2], b[3], b[4], b[5]] for b in books]
    print_table(headers, rows, [4, 16, 28, 22, 16, 11])


def handle_add_book():
    """Interactively adds a new book."""
    print_header("Add New Book Record")
    isbn = input("Enter ISBN (e.g. 978-0132350884): ").strip()
    title = input("Enter Book Title: ").strip()
    author = input("Enter Author Name: ").strip()
    category = input("Enter Category (e.g. Computer Science, Fiction): ").strip()
    copies = input("Enter Available Copies (Default: 1): ").strip()

    copies = int(copies) if copies.isdigit() else 1
    success, msg = operations.add_book(isbn, title, author, category, copies)
    print(f"\n[{'SUCCESS' if success else 'ERROR'}] {msg}")


# ==================== Borrower Menu Handlers ====================

def handle_view_borrowers():
    """Displays registered borrowers."""
    print_header("Registered Borrowers")
    borrowers = operations.get_all_borrowers()
    headers = ["ID", "Borrower Name", "Roll / Registration No."]
    rows = [[b[0], b[1], b[2]] for b in borrowers]
    print_table(headers, rows, [6, 26, 22])


def handle_add_borrower():
    """Interactively adds a new borrower."""
    print_header("Register New Borrower")
    name = input("Enter Borrower Name: ").strip()
    roll_no = input("Enter Roll No / ID: ").strip()

    success, msg = operations.add_borrower(name, roll_no)
    print(f"\n[{'SUCCESS' if success else 'ERROR'}] {msg}")


# ==================== Circulation Handlers ====================

def handle_issue_book():
    """Issues a book to a borrower with validation."""
    print_header("Issue a Book")
    handle_view_books()
    print("\n")
    handle_view_borrowers()
    print("-" * 65)

    book_id_input = input("\nEnter Book ID to issue: ").strip()
    borrower_id_input = input("Enter Borrower ID: ").strip()

    if not book_id_input.isdigit() or not borrower_id_input.isdigit():
        print("[ERROR] Book ID and Borrower ID must be numbers.")
        return

    issue_date_input = input(f"Enter Issue Date (YYYY-MM-DD) [Default: Today ({date.today()})]: ").strip()
    due_days_input = input(f"Enter Loan Period in Days [Default: {DEFAULT_LOAN_DAYS}]: ").strip()

    issue_date = issue_date_input if issue_date_input else None
    due_days = int(due_days_input) if due_days_input.isdigit() else None

    success, msg = operations.issue_book(int(book_id_input), int(borrower_id_input), issue_date, due_days)
    print(f"\n[{'SUCCESS' if success else 'ERROR'}] {msg}")


def handle_return_book():
    """Records the return of an issued book."""
    print_header("Return an Issued Book")
    active_loans = operations.get_active_loans()
    if not active_loans:
        print("There are currently no active loans to return.")
        return

    print("Currently Active Loans:")
    headers = ["Loan ID", "Book Title", "Borrower", "Roll No", "Due Date", "Status"]
    rows = []
    for l in active_loans:
        status = f"OVERDUE ({l['days_overdue']}d)" if l["is_overdue"] else "Active"
        rows.append([l["loan_id"], l["title"], l["borrower_name"], l["roll_no"], l["due_date"], status])
    print_table(headers, rows, [8, 24, 16, 12, 12, 14])

    loan_id_input = input("\nEnter Loan ID to return: ").strip()
    if not loan_id_input.isdigit():
        print("[ERROR] Loan ID must be a number.")
        return

    return_date_input = input(f"Enter Return Date (YYYY-MM-DD) [Default: Today ({date.today()})]: ").strip()
    return_date = return_date_input if return_date_input else None

    success, msg = operations.return_book(int(loan_id_input), return_date)
    print(f"\n[{'SUCCESS' if success else 'ERROR'}] {msg}")


def handle_view_active_loans():
    """Displays all active loans and indicates overdue items."""
    print_header("Active Loans & Overdue Status")
    active_loans = operations.get_active_loans()
    if not active_loans:
        print("No active loans at this time.")
        return

    headers = ["Loan ID", "Book Title", "Borrower", "Roll No", "Issued On", "Due Date", "Status"]
    rows = []
    for l in active_loans:
        status = f"OVERDUE ({l['days_overdue']} days)" if l["is_overdue"] else "On Time"
        rows.append([l["loan_id"], l["title"], l["borrower_name"], l["roll_no"], l["issue_date"], l["due_date"], status])
    print_table(headers, rows, [8, 22, 14, 12, 12, 12, 18])


# ==================== Analytics & Reports ====================

def handle_most_borrowed_report():
    """Displays the most-borrowed books report."""
    print_header("Analytics: Most-Borrowed Books Report")
    df = analytics.get_most_borrowed_books_df(limit=10)
    if df.empty:
        print("No circulation data available yet.")
        return

    headers = ["Rank", "Title", "Category", "Author", "Times Borrowed", "Stock Left"]
    rows = []
    for rank, (_, row) in enumerate(df.iterrows(), start=1):
        rows.append([rank, row["title"], row["category"], row["author"], row["borrow_count"], row["copies_available"]])
    print_table(headers, rows, [5, 26, 16, 20, 14, 10])


def handle_overdue_report():
    """Displays overdue loans report."""
    print_header("Analytics: Overdue Loans Report")
    df = analytics.get_overdue_loans_df()
    if df.empty:
        print("Great news! There are currently no overdue loans.")
        return

    headers = ["Loan ID", "Book Title", "Borrower", "Roll No", "Due Date", "Days Overdue"]
    rows = []
    for _, row in df.iterrows():
        rows.append([row["loan_id"], row["book_title"], row["borrower_name"], row["roll_no"], str(row["due_date"])[:10], f"{row['days_overdue']} day(s)"])
    print_table(headers, rows, [8, 24, 15, 12, 12, 14])


def handle_category_summary():
    """Displays category-level summary using Pandas."""
    print_header("Analytics: Book Category Usage Summary (Pandas)")
    df = analytics.get_category_summary_df()
    if df.empty:
        print("No category data available.")
        return

    headers = ["Category", "Titles", "Available Copies", "Times Borrowed", "Circulation Share"]
    rows = []
    for _, row in df.iterrows():
        rows.append([row["Category"], row["Total Titles"], row["Available Copies"], row["Times Borrowed"], f"{row['Circulation Share (%)']}%"])
    print_table(headers, rows, [18, 8, 16, 16, 18])


def handle_monthly_trends_report():
    """Displays monthly borrowing trends using Pandas."""
    print_header("Analytics: Monthly Borrowing Trends (Pandas)")
    df = analytics.get_monthly_borrowing_trends_df()
    if df.empty:
        print("No monthly trend data available.")
        return

    headers = ["Year-Month", "Total Loans", "Returned", "Active / Pending", "Overdue"]
    rows = []
    for _, row in df.iterrows():
        rows.append([row["Year-Month"], row["Total Loans"], row["Returned"], row["Active / Pending"], row["Overdue"]])
    print_table(headers, rows, [14, 12, 10, 16, 10])


def handle_descriptive_stats():
    """Displays NumPy descriptive statistics for loan duration."""
    print_header("Analytics: Loan Duration Descriptive Statistics (NumPy)")
    stats = analytics.calculate_loan_statistics()
    kpis = analytics.get_library_kpis()

    if stats["completed_loans_count"] == 0:
        print("No completed (returned) loans available for duration statistics.")
        return

    print(f" Sample Size (Completed Loans) : {stats['completed_loans_count']}")
    print(f" Mean Loan Duration            : {stats['mean_days']:.2f} days")
    print(f" Median Loan Duration          : {stats['median_days']:.2f} days")
    print(f" Standard Deviation            : {stats['std_dev_days']:.2f} days")
    print(f" Minimum Days Kept             : {stats['min_days']} day(s)")
    print(f" Maximum Days Kept             : {stats['max_days']} day(s)")
    print(f" 25th Percentile (Q1)          : {stats['q25_days']:.2f} days")
    print(f" 75th Percentile (Q3)          : {stats['q75_days']:.2f} days")
    print("-" * 65)
    print(" Library Circulation KPIs:")
    print(f"   • Total Book Titles        : {kpis['total_titles']}")
    print(f"   • Available Copies in Stock: {kpis['available_copies']}")
    print(f"   • Total Loans Recorded     : {kpis['total_loans']}")
    print(f"   • Currently Active Loans   : {kpis['active_loans']}")
    print(f"   • Overdue Loans Count      : {kpis['overdue_loans']}")
    print(f"   • Overall Return Rate      : {kpis['return_rate']}%")


# ==================== Visualizations ====================

def handle_generate_charts():
    """Generates charts using Matplotlib and saves them to reports_and_charts/."""
    print_header("Generate Visualizations (Matplotlib)")
    print("Generating charts...")

    c1 = analytics.plot_popular_books()
    c2 = analytics.plot_monthly_trends()
    c3 = analytics.plot_category_distribution()

    print("\n[SUCCESS] Charts successfully generated and saved:")
    if c1:
        print(f"  1. Popular Books Chart      : {c1}")
    if c2:
        print(f"  2. Monthly Trends Line Chart: {c2}")
    if c3:
        print(f"  3. Category Donut Chart     : {c3}")
    print(f"\nAll chart images are stored in: {CHARTS_DIR}")


# ==================== Main Application Loop ====================

def run_automated_demo():
    """Runs a complete automated walkthrough of all system features."""
    print_header("Running Automated System Walkthrough")
    print("1. Initializing Database and Loading Sample Data...")
    seed_data.populate_sample_data(force_reset=True)

    print("\n2. Displaying Catalogue & Active Loans...")
    handle_view_books()
    handle_view_active_loans()

    print("\n3. Testing Loan Return with Acceptance Validation...")
    active = operations.get_active_loans()
    if active:
        first_loan_id = active[0]["loan_id"]
        print(f"Returning loan #{first_loan_id}...")
        success, msg = operations.return_book(first_loan_id)
        print(f"Result: {msg}")

        # Attempt to return the same book again to verify rejection
        print("\nAttempting invalid duplicate return sequence on same loan...")
        dup_success, dup_msg = operations.return_book(first_loan_id)
        print(f"Result: {dup_msg} (Expected rejection)")

    print("\n4. Displaying Reports & Statistics...")
    handle_most_borrowed_report()
    handle_overdue_report()
    handle_category_summary()
    handle_monthly_trends_report()
    handle_descriptive_stats()

    print("\n5. Generating Visualization Charts...")
    handle_generate_charts()
    print("\n[COMPLETE] Automated demo executed successfully!")


def main():
    """Main CLI Menu loop."""
    initialize_database()

    if len(sys.argv) > 1 and sys.argv[1] in ("--demo", "-d"):
        run_automated_demo()
        return

    while True:
        print_header("Library Book Usage Analysis System")
        print(" [1] View Book Catalogue")
        print(" [2] Add New Book")
        print(" [3] View Registered Borrowers")
        print(" [4] Register New Borrower")
        print(" [5] Issue a Book (Checkout)")
        print(" [6] Return an Issued Book (Checkin)")
        print(" [7] View Active Loans & Overdue Status")
        print(" [8] Report: Most-Borrowed Books")
        print(" [9] Report: Overdue Loans List")
        print(" [10] Report: Category Circulation Summary (Pandas)")
        print(" [11] Report: Monthly Borrowing Trends (Pandas)")
        print(" [12] Statistics: Loan Durations & Circulation KPIs (NumPy)")
        print(" [13] Visualizations: Generate & Save Charts (Matplotlib)")
        print(" [14] Reset / Populate Sample Data")
        print(" [0] Exit System")
        print("-" * 65)

        choice = input("Enter option [0-14]: ").strip()

        if choice == "1":
            handle_view_books()
        elif choice == "2":
            handle_add_book()
        elif choice == "3":
            handle_view_borrowers()
        elif choice == "4":
            handle_add_borrower()
        elif choice == "5":
            handle_issue_book()
        elif choice == "6":
            handle_return_book()
        elif choice == "7":
            handle_view_active_loans()
        elif choice == "8":
            handle_most_borrowed_report()
        elif choice == "9":
            handle_overdue_report()
        elif choice == "10":
            handle_category_summary()
        elif choice == "11":
            handle_monthly_trends_report()
        elif choice == "12":
            handle_descriptive_stats()
        elif choice == "13":
            handle_generate_charts()
        elif choice == "14":
            confirm = input("Are you sure you want to reset and reload sample data? (y/n): ").strip().lower()
            if confirm == "y":
                seed_data.populate_sample_data(force_reset=True)
        elif choice == "0":
            print("\nExiting Library Book Usage Analysis System. Goodbye!\n")
            break
        else:
            print("\n[ERROR] Invalid option. Please select a number between 0 and 14.")

        input("\nPress Enter to return to main menu...")


if __name__ == "__main__":
    main()
