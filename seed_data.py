"""
Sample Data Populator for Library Book Usage Analysis System.
Populates realistic books, borrowers, and past/active/overdue borrowing transactions.
"""

from datetime import date, timedelta
from database import Database, initialize_database, get_raw_connection


SAMPLE_BOOKS = [
    ("978-0131103627", "The C Programming Language", "Brian Kernighan & Dennis Ritchie", "Computer Science", 4),
    ("978-0262033848", "Introduction to Algorithms", "Thomas H. Cormen", "Computer Science", 3),
    ("978-0132350884", "Clean Code", "Robert C. Martin", "Computer Science", 3),
    ("978-0321751041", "The Art of Computer Programming", "Donald Knuth", "Computer Science", 2),
    ("978-0451524935", "1984", "George Orwell", "Fiction", 5),
    ("978-0141439518", "Pride and Prejudice", "Jane Austen", "Fiction", 4),
    ("978-0061120084", "To Kill a Mockingbird", "Harper Lee", "Fiction", 3),
    ("978-0393040029", "A Brief History of Time", "Stephen Hawking", "Science", 4),
    ("978-0385504201", "The Da Vinci Code", "Dan Brown", "Mystery", 3),
    ("978-0199535569", "The Republic", "Plato", "Philosophy", 2),
    ("978-0062316097", "Sapiens: A Brief History of Humankind", "Yuval Noah Harari", "History", 4),
    ("978-0471195863", "Calculus: Early Transcendentals", "Howard Anton", "Mathematics", 3),
]

SAMPLE_BORROWERS = [
    ("Alice Johnson", "CS-2024-001"),
    ("Bob Smith", "CS-2024-002"),
    ("Charlie Brown", "ME-2024-015"),
    ("Diana Prince", "EC-2024-032"),
    ("Ethan Hunt", "IT-2024-045"),
    ("Fiona Gallagher", "CV-2024-019"),
    ("George Clark", "EE-2024-011"),
]


def populate_sample_data(force_reset: bool = False):
    """
    Inserts sample catalogue, borrowers, and circulation records.
    If force_reset is True, clears existing records first.
    """
    initialize_database()
    conn = get_raw_connection()
    cursor = conn.cursor()

    if force_reset:
        cursor.execute("DELETE FROM loans;")
        cursor.execute("DELETE FROM books;")
        cursor.execute("DELETE FROM borrowers;")
        conn.commit()

    # Check if already populated
    cursor.execute("SELECT COUNT(*) FROM books")
    if cursor.fetchone()[0] > 0 and not force_reset:
        cursor.close()
        conn.close()
        print("[INFO] Database already contains records. Skipping sample population.")
        return

    print("[INFO] Populating sample data into MySQL database...")

    # 1. Insert Books
    book_id_map = {}
    for isbn, title, author, category, copies in SAMPLE_BOOKS:
        query = "INSERT INTO books (isbn, title, author, category, copies_available) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(query, (isbn, title, author, category, copies))
        book_id_map[title] = cursor.lastrowid

    # 2. Insert Borrowers
    borrower_id_map = {}
    for name, roll in SAMPLE_BORROWERS:
        query = "INSERT INTO borrowers (borrower_name, roll_no) VALUES (%s, %s)"
        cursor.execute(query, (name, roll))
        borrower_id_map[name] = cursor.lastrowid

    conn.commit()

    # 3. Insert Loans across multiple months (Historical, Active, and Overdue)
    today = date.today()

    # Loan scenarios:
    # (Book Title, Borrower Name, days_ago_issued, loan_duration_days, days_ago_returned_or_None)
    loan_scenarios = [
        # Returned on time (4 months ago)
        ("Introduction to Algorithms", "Alice Johnson", 120, 14, 108),
        ("Clean Code", "Bob Smith", 115, 14, 105),
        ("The C Programming Language", "Charlie Brown", 110, 14, 98),
        ("1984", "Diana Prince", 100, 14, 90),

        # Returned slightly late (3 months ago)
        ("Clean Code", "Ethan Hunt", 85, 14, 68),  # 3 days overdue when returned
        ("A Brief History of Time", "Fiona Gallagher", 80, 14, 70),
        ("The Da Vinci Code", "George Clark", 75, 14, 63),
        ("Introduction to Algorithms", "Bob Smith", 70, 14, 60),

        # Returned on time (2 months ago)
        ("Clean Code", "Alice Johnson", 55, 14, 45),
        ("The C Programming Language", "Diana Prince", 50, 14, 38),
        ("Calculus: Early Transcendentals", "Charlie Brown", 45, 14, 35),
        ("Sapiens: A Brief History of Humankind", "Ethan Hunt", 40, 14, 28),

        # Returned last month
        ("Introduction to Algorithms", "Diana Prince", 30, 14, 20),
        ("1984", "George Clark", 28, 14, 15),
        ("To Kill a Mockingbird", "Alice Johnson", 25, 14, 14),

        # ACTIVE LOAN: NOT Overdue (Issued 5 days ago, due in 9 days)
        ("The C Programming Language", "Alice Johnson", 5, 14, None),
        ("Clean Code", "Charlie Brown", 4, 14, None),
        ("Sapiens: A Brief History of Humankind", "George Clark", 3, 14, None),

        # ACTIVE LOAN: OVERDUE! (Issued 25 days ago, was due 11 days ago)
        ("Introduction to Algorithms", "Ethan Hunt", 25, 14, None),
        ("1984", "Bob Smith", 20, 14, None),
    ]

    for title, borrower_name, issue_offset, loan_duration, return_offset in loan_scenarios:
        b_id = book_id_map[title]
        br_id = borrower_id_map[borrower_name]

        issue_dt = today - timedelta(days=issue_offset)
        due_dt = issue_dt + timedelta(days=loan_duration)
        ret_dt = (today - timedelta(days=return_offset)) if return_offset is not None else None

        issue_str = issue_dt.strftime("%Y-%m-%d")
        due_str = due_dt.strftime("%Y-%m-%d")
        ret_str = ret_dt.strftime("%Y-%m-%d") if ret_dt else None

        loan_query = """
        INSERT INTO loans (book_id, borrower_id, issue_date, due_date, return_date)
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(loan_query, (b_id, br_id, issue_str, due_str, ret_str))

        # If currently active (ret_dt is None), decrement copies_available
        if ret_dt is None:
            update_query = "UPDATE books SET copies_available = copies_available - 1 WHERE book_id = %s"
            cursor.execute(update_query, (b_id,))

    conn.commit()
    cursor.close()
    conn.close()
    print("[SUCCESS] Sample database populated with 12 books, 7 borrowers, and 20 realistic circulation loans.")


if __name__ == "__main__":
    populate_sample_data(force_reset=True)
