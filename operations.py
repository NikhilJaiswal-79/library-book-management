"""
Library Operations Module.
Handles Books, Borrowers, and Circulation (Issue/Return) with strict validation.
"""

from datetime import datetime, timedelta, date
from database import Database, get_raw_connection
from config import DEFAULT_LOAN_DAYS


def add_book(isbn: str, title: str, author: str, category: str, copies_available: int = 1) -> tuple[bool, str]:
    """Adds a new book to the library catalogue."""
    try:
        isbn = isbn.strip()
        title = title.strip()
        author = author.strip()
        category = category.strip()

        if not isbn or not title or not author or not category:
            return False, "All book fields (ISBN, Title, Author, Category) are required."

        if int(copies_available) < 0:
            return False, "Available copies cannot be negative."

        query = """
        INSERT INTO books (isbn, title, author, category, copies_available)
        VALUES (%s, %s, %s, %s, %s)
        """
        Database.execute(query, (isbn, title, author, category, int(copies_available)))
        return True, f"Book '{title}' added successfully."
    except Exception as e:
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            return False, f"A book with ISBN '{isbn}' already exists."
        return False, f"Database error: {e}"


def get_all_books() -> list[tuple]:
    """Retrieves all books."""
    query = "SELECT book_id, isbn, title, author, category, copies_available FROM books ORDER BY book_id ASC"
    return Database.fetchall(query)


def get_book_by_id(book_id: int):
    """Retrieves a single book by ID."""
    query = "SELECT book_id, isbn, title, author, category, copies_available FROM books WHERE book_id = %s"
    return Database.fetchone(query, (book_id,))


def add_borrower(borrower_name: str, roll_no: str) -> tuple[bool, str]:
    """Registers a new borrower/student."""
    try:
        borrower_name = borrower_name.strip()
        roll_no = roll_no.strip()

        if not borrower_name or not roll_no:
            return False, "Borrower Name and Roll Number are required."

        query = "INSERT INTO borrowers (borrower_name, roll_no) VALUES (%s, %s)"
        Database.execute(query, (borrower_name, roll_no))
        return True, f"Borrower '{borrower_name}' ({roll_no}) registered successfully."
    except Exception as e:
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            return False, f"Borrower with Roll No '{roll_no}' already exists."
        return False, f"Database error: {e}"


def get_all_borrowers() -> list[tuple]:
    """Retrieves all registered borrowers."""
    query = "SELECT borrower_id, borrower_name, roll_no FROM borrowers ORDER BY borrower_id ASC"
    return Database.fetchall(query)


def get_borrower_by_id(borrower_id: int):
    """Retrieves a borrower by ID."""
    query = "SELECT borrower_id, borrower_name, roll_no FROM borrowers WHERE borrower_id = %s"
    return Database.fetchone(query, (borrower_id,))


def issue_book(book_id: int, borrower_id: int, issue_date_str: str = None, loan_days: int = None) -> tuple[bool, str]:
    """
    Issues a book copy to a borrower with validation:
    - Book exists and copies_available > 0
    - Borrower exists
    - Computes due_date based on configurable loan_days
    - Decrements available copies
    """
    # 1. Validate Book
    book = get_book_by_id(book_id)
    if not book:
        return False, f"Error: Book ID {book_id} does not exist."

    copies_available = book[5]
    if copies_available <= 0:
        return False, f"Error: Book '{book[2]}' has NO copies available for issue (Stock: 0)."

    # 2. Validate Borrower
    borrower = get_borrower_by_id(borrower_id)
    if not borrower:
        return False, f"Error: Borrower ID {borrower_id} does not exist."

    # 3. Parse Issue Date and Due Date
    try:
        if issue_date_str:
            issue_date = datetime.strptime(issue_date_str.strip(), "%Y-%m-%d").date()
        else:
            issue_date = date.today()
    except ValueError:
        return False, "Error: Invalid date format. Use YYYY-MM-DD."

    days = int(loan_days) if loan_days and int(loan_days) > 0 else DEFAULT_LOAN_DAYS
    due_date = issue_date + timedelta(days=days)

    issue_str = issue_date.strftime("%Y-%m-%d")
    due_str = due_date.strftime("%Y-%m-%d")

    # 4. Atomic Transaction: Insert loan and decrement copies
    conn = get_raw_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO loans (book_id, borrower_id, issue_date, due_date, return_date) VALUES (%s, %s, %s, %s, NULL)",
            (book_id, borrower_id, issue_str, due_str)
        )
        cursor.execute(
            "UPDATE books SET copies_available = copies_available - 1 WHERE book_id = %s AND copies_available > 0",
            (book_id,)
        )

        if cursor.rowcount == 0:
            conn.rollback()
            return False, "Failed to issue book: Copy count was insufficient during checkout."

        conn.commit()
        return True, f"Successfully issued '{book[2]}' to {borrower[1]} (Roll: {borrower[2]}). Due date: {due_str}"
    except Exception as e:
        conn.rollback()
        return False, f"Transaction error: {e}"
    finally:
        cursor.close()
        conn.close()


def return_book(loan_id: int, return_date_str: str = None) -> tuple[bool, str]:
    """
    Records the return of an issued book with strict validation:
    - Loan exists
    - Loan is not already returned
    - return_date >= issue_date (rejects invalid chronological sequences)
    - Increments available copies
    """
    # 1. Fetch loan details
    loan = Database.fetchone("SELECT loan_id, book_id, borrower_id, issue_date, due_date, return_date FROM loans WHERE loan_id = %s", (loan_id,))
    if not loan:
        return False, f"Error: Loan record #{loan_id} not found."

    book_id = loan[1]
    raw_issue = loan[3]
    existing_return = loan[5]

    # Validate not already returned
    if existing_return is not None:
        return False, f"Error: Loan #{loan_id} was already returned on {existing_return}."

    # Parse dates
    try:
        if isinstance(raw_issue, str):
            issue_date = datetime.strptime(raw_issue[:10], "%Y-%m-%d").date()
        elif isinstance(raw_issue, (datetime, date)):
            issue_date = raw_issue if isinstance(raw_issue, date) else raw_issue.date()
        else:
            issue_date = date.today()

        if return_date_str:
            return_date = datetime.strptime(return_date_str.strip(), "%Y-%m-%d").date()
        else:
            return_date = date.today()
    except ValueError:
        return False, "Error: Invalid date format. Please use YYYY-MM-DD."

    # Validate chronological sequence
    if return_date < issue_date:
        return False, f"Rejected: Return date ({return_date}) cannot be earlier than issue date ({issue_date})."

    ret_str = return_date.strftime("%Y-%m-%d")

    # 2. Atomic Transaction: Update return_date and increment copies_available
    conn = get_raw_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE loans SET return_date = %s WHERE loan_id = %s AND return_date IS NULL",
            (ret_str, loan_id)
        )
        cursor.execute(
            "UPDATE books SET copies_available = copies_available + 1 WHERE book_id = %s",
            (book_id,)
        )

        if cursor.rowcount == 0:
            conn.rollback()
            return False, "Failed to return book: Loan status may have been updated concurrently."

        conn.commit()

        # Check if overdue
        raw_due = loan[4]
        if isinstance(raw_due, str):
            due_date = datetime.strptime(raw_due[:10], "%Y-%m-%d").date()
        else:
            due_date = raw_due if isinstance(raw_due, date) else raw_due.date()

        overdue_note = ""
        if return_date > due_date:
            days_late = (return_date - due_date).days
            overdue_note = f" (NOTE: Returned {days_late} day(s) late!)"

        return True, f"Book successfully returned on {ret_str}. Inventory copy restored.{overdue_note}"
    except Exception as e:
        conn.rollback()
        return False, f"Transaction error: {e}"
    finally:
        cursor.close()
        conn.close()


def get_active_loans() -> list[dict]:
    """Retrieves all currently active (unreturned) loans with overdue calculation."""
    query = """
    SELECT 
        l.loan_id,
        b.title,
        br.borrower_name,
        br.roll_no,
        l.issue_date,
        l.due_date
    FROM loans l
    JOIN books b ON l.book_id = b.book_id
    JOIN borrowers br ON l.borrower_id = br.borrower_id
    WHERE l.return_date IS NULL
    ORDER BY l.due_date ASC
    """
    rows = Database.fetchall(query)
    today = date.today()
    results = []

    for r in rows:
        loan_id, title, borrower_name, roll_no, issue_d, due_d = r
        if isinstance(due_d, str):
            due_dt = datetime.strptime(due_d[:10], "%Y-%m-%d").date()
        else:
            due_dt = due_d if isinstance(due_d, date) else due_d.date()

        days_diff = (today - due_dt).days
        is_overdue = days_diff > 0

        results.append({
            "loan_id": loan_id,
            "title": title,
            "borrower_name": borrower_name,
            "roll_no": roll_no,
            "issue_date": str(issue_d)[:10],
            "due_date": str(due_d)[:10],
            "is_overdue": is_overdue,
            "days_overdue": days_diff if is_overdue else 0
        })

    return results
