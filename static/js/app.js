/**
 * Library Book Usage Analysis System - Single Page Application Logic
 * Interactive Chart.js Vector Visualizations & Complete Circulation Management
 */

let allBooksCache = [];
let allBorrowersCache = [];
let allActiveLoansCache = [];
let currentActiveView = "dashboard";
const chartInstances = {};

const validViews = ["dashboard", "books", "addBook", "borrowers", "circulation", "analytics"];

const viewMetadata = {
  dashboard: {
    title: "Circulation Dashboard",
    sub: "Real-time library usage metrics and active loans"
  },
  books: {
    title: "Book Catalogue",
    sub: "Manage titles, categories, authors, and available inventory"
  },
  addBook: {
    title: "Register New Book",
    sub: "Add a new title, specify category, and allocate physical shelf copies"
  },
  borrowers: {
    title: "Borrowers Directory",
    sub: "Manage student and faculty borrower records"
  },
  circulation: {
    title: "Circulation Desk",
    sub: "Process checkouts, returns, and track overdue loan deadlines"
  },
  analytics: {
    title: "Interactive Analytics & Charts",
    sub: "Interactive Chart.js vector visualizations and Pandas summaries"
  }
};

// ==================== INITIALIZATION ====================

document.addEventListener("DOMContentLoaded", () => {
  // Set default dates
  const today = new Date().toISOString().split("T")[0];
  const issueDateEl = document.getElementById("issueDateInput");
  const returnDateEl = document.getElementById("returnDateInput");
  if (issueDateEl) issueDateEl.value = today;
  if (returnDateEl) returnDateEl.value = today;

  // Read URL Hash or default to dashboard
  const hash = window.location.hash.replace("#", "");
  const initialView = validViews.includes(hash) ? hash : "dashboard";

  loadSystemStatus();
  switchView(initialView);

  window.addEventListener("hashchange", () => {
    const newHash = window.location.hash.replace("#", "");
    if (newHash && validViews.includes(newHash) && newHash !== currentActiveView) {
      switchView(newHash);
    }
  });
});


// ==================== VIEW SWITCHING & NAVIGATION ====================

function switchView(viewName) {
  if (!validViews.includes(viewName)) viewName = "dashboard";
  currentActiveView = viewName;
  window.location.hash = viewName;

  // Update nav buttons
  document.querySelectorAll(".nav-menu button").forEach(btn => btn.classList.remove("active"));
  const activeNavBtn = document.getElementById(`nav${capitalize(viewName)}`);
  if (activeNavBtn) activeNavBtn.classList.add("active");

  // Update sections
  document.querySelectorAll(".view-section").forEach(sec => sec.classList.remove("active"));
  const targetSection = document.getElementById(`view${capitalize(viewName)}`);
  if (targetSection) targetSection.classList.add("active");

  // Update Header
  const meta = viewMetadata[viewName] || viewMetadata.dashboard;
  document.getElementById("viewHeading").textContent = meta.title;
  document.getElementById("viewSubheading").textContent = meta.sub;

  // Load specific view data
  if (viewName === "dashboard") loadDashboardData();
  else if (viewName === "books") loadBooks();
  else if (viewName === "addBook") updateLiveBookPreview();
  else if (viewName === "borrowers") loadBorrowers();
  else if (viewName === "circulation") loadCirculationData();
  else if (viewName === "analytics") loadAnalyticsData();
}

function refreshCurrentView() {
  showToast("Refreshing data...", "info");
  switchView(currentActiveView);
}

function capitalize(s) {
  return s.charAt(0).toUpperCase() + s.slice(1);
}


// ==================== API DATA LOADERS ====================

async function loadSystemStatus() {
  try {
    const res = await fetch("/api/status");
    if (!res.ok) throw new Error("Status API error");
    const data = await res.json();

    const sidebarBackend = document.getElementById("sidebarBackend");
    const settingsBackend = document.getElementById("settingsBackend");
    const settingsDueWindow = document.getElementById("settingsDueWindow");
    const settingsServerDate = document.getElementById("settingsServerDate");

    if (sidebarBackend) sidebarBackend.textContent = data.database_backend;
    if (settingsBackend) settingsBackend.textContent = data.database_backend;
    if (settingsDueWindow) settingsDueWindow.textContent = `${data.default_loan_days} Days`;
    if (settingsServerDate) settingsServerDate.textContent = data.today;
  } catch (err) {
    console.error("Failed to load status:", err);
  }
}

async function loadDashboardData() {
  try {
    // 1. Fetch KPIs
    const kpiRes = await fetch("/api/kpis");
    if (kpiRes.ok) {
      const kpis = await kpiRes.json();
      document.getElementById("kpiTotalTitles").textContent = kpis.total_titles;
      document.getElementById("kpiAvailableCopies").textContent = `${kpis.available_copies} copies in stock`;
      document.getElementById("kpiActiveLoans").textContent = kpis.active_loans;
      document.getElementById("kpiOverdueLoans").textContent = kpis.overdue_loans;
      document.getElementById("kpiBorrowers").textContent = kpis.registered_borrowers;
      document.getElementById("kpiReturnRate").textContent = `${kpis.return_rate}%`;
      document.getElementById("kpiTotalLoans").textContent = `${kpis.total_loans} total circulation events`;

      // Update sidebar badge
      const overdueBadge = document.getElementById("overdueBadge");
      if (kpis.overdue_loans > 0) {
        overdueBadge.textContent = `${kpis.overdue_loans} OVERDUE`;
        overdueBadge.style.display = "inline-block";
      } else {
        overdueBadge.style.display = "none";
      }
    }

    // 2. Fetch Active Loans for Dashboard Table
    const loansRes = await fetch("/api/loans/active");
    if (loansRes.ok) {
      const loans = await loansRes.json();
      renderDashboardActiveLoans(loans);
    }

    // 3. Render Dashboard Interactive Vector Charts (No Images!)
    const [popRes, trendsRes] = await Promise.all([
      fetch("/api/analytics/popular?limit=5"),
      fetch("/api/analytics/trends")
    ]);
    if (popRes.ok && trendsRes.ok) {
      const popularData = await popRes.json();
      const trendsData = await trendsRes.json();
      renderBarChart("dashPopularCanvas", popularData.map(b => b.title), popularData.map(b => b.borrow_count), "#3b82f6", "Times Borrowed", true);
      renderLineChart("dashTrendsCanvas", trendsData.map(t => t["Year-Month"]), [
        { label: "Total Loans", data: trendsData.map(t => t["Total Loans"]), color: "#38bdf8" },
        { label: "Returned", data: trendsData.map(t => t["Returned"]), color: "#34d399" }
      ]);
    }
  } catch (err) {
    console.error("Dashboard load error:", err);
    showToast("Error fetching dashboard statistics", "error");
  }
}

function renderDashboardActiveLoans(loans) {
  const tbody = document.getElementById("dashboardActiveLoansBody");
  if (!tbody) return;

  if (!loans || loans.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding: 24px; color: var(--text-dim);">No active loans right now. All copies returned!</td></tr>`;
    return;
  }

  tbody.innerHTML = loans.slice(0, 6).map(l => {
    const isOverdue = l.is_overdue;
    const statusBadge = isOverdue
      ? `<span class="badge badge-overdue">⚠️ ${l.days_overdue}d Overdue</span>`
      : `<span class="badge badge-active">Active</span>`;

    return `
      <tr>
        <td style="font-weight:700; color:var(--text-dim);">#${l.loan_id}</td>
        <td style="font-weight:600; color:var(--text-main);">${escapeHtml(l.title)}</td>
        <td>${escapeHtml(l.borrower_name)}</td>
        <td><code>${escapeHtml(l.roll_no)}</code></td>
        <td>${l.due_date}</td>
        <td>${statusBadge}</td>
        <td>
          <button class="btn btn-secondary btn-sm" onclick="openReturnModal(${l.loan_id}, '${escapeQuote(l.title)}', '${escapeQuote(l.borrower_name)}')">
            Return ↵
          </button>
        </td>
      </tr>
    `;
  }).join("");
}

// ==================== BOOKS MODULE ====================

async function loadBooks() {
  try {
    const res = await fetch("/api/books");
    if (!res.ok) throw new Error("Failed to load books");
    allBooksCache = await res.json();

    // Populate category filter
    const categories = Array.from(new Set(allBooksCache.map(b => b.category))).filter(Boolean).sort();
    const catSelect = document.getElementById("bookCategoryFilter");
    const curVal = catSelect.value;
    catSelect.innerHTML = '<option value="">All Categories</option>' + categories.map(c => `<option value="${c}">${c}</option>`).join("");
    catSelect.value = curVal;

    filterBooks();
  } catch (err) {
    showToast("Could not load book catalogue", "error");
  }
}

function filterBooks() {
  const search = document.getElementById("bookSearchInput").value.toLowerCase().trim();
  const category = document.getElementById("bookCategoryFilter").value;

  const filtered = allBooksCache.filter(b => {
    const matchSearch = !search ||
      b.title.toLowerCase().includes(search) ||
      b.author.toLowerCase().includes(search) ||
      b.isbn.toLowerCase().includes(search);
    const matchCat = !category || b.category === category;
    return matchSearch && matchCat;
  });

  const tbody = document.getElementById("booksTableBody");
  if (!tbody) return;

  if (filtered.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding: 24px; color: var(--text-dim);">No matching books found.</td></tr>`;
    return;
  }

  tbody.innerHTML = filtered.map(b => {
    const inStock = b.copies_available > 0;
    const stockBadge = inStock
      ? `<span class="badge badge-in-stock">● ${b.copies_available} Available</span>`
      : `<span class="badge badge-out-of-stock">● Out of Stock (0)</span>`;

    const actionBtn = inStock
      ? `<button class="btn btn-primary btn-sm" onclick="quickIssueBook(${b.book_id})">Issue →</button>`
      : `<button class="btn btn-secondary btn-sm" disabled style="opacity:0.5; cursor:not-allowed;">Unavailable</button>`;

    return `
      <tr>
        <td style="color:var(--text-dim); font-weight:700;">${b.book_id}</td>
        <td><code>${escapeHtml(b.isbn)}</code></td>
        <td style="font-weight:600; color:var(--text-main);">${escapeHtml(b.title)}</td>
        <td>${escapeHtml(b.author)}</td>
        <td><span class="badge badge-category">${escapeHtml(b.category)}</span></td>
        <td>${stockBadge}</td>
        <td>${actionBtn}</td>
      </tr>
    `;
  }).join("");
}

// ==================== DEDICATED ADD NEW BOOK VIEW ====================

function updateLiveBookPreview() {
  const title = document.getElementById("pageBookTitle")?.value.trim() || "Book Title Will Appear Here";
  const author = document.getElementById("pageBookAuthor")?.value.trim() || "Author Name";
  const category = document.getElementById("pageBookCategory")?.value.trim() || "CATEGORY";
  const isbn = document.getElementById("pageBookIsbn")?.value.trim() || "978-XXXXXXXXXX";
  const copies = parseInt(document.getElementById("pageBookCopies")?.value, 10) || 1;

  const prevTitle = document.getElementById("previewTitle");
  const prevAuthor = document.getElementById("previewAuthor");
  const prevCategory = document.getElementById("previewCategory");
  const prevIsbn = document.getElementById("previewIsbn");
  const prevStock = document.getElementById("previewStock");

  if (prevTitle) prevTitle.textContent = title;
  if (prevAuthor) prevAuthor.textContent = `By ${author}`;
  if (prevCategory) prevCategory.textContent = category.toUpperCase();
  if (prevIsbn) prevIsbn.textContent = `ISBN: ${isbn}`;
  if (prevStock) prevStock.textContent = `● ${copies} ${copies === 1 ? 'Copy' : 'Copies'} In Stock`;
}

function resetAddBookForm() {
  const form = document.getElementById("dedicatedAddBookForm");
  if (form) form.reset();
  const copies = document.getElementById("pageBookCopies");
  if (copies) copies.value = 3;
  updateLiveBookPreview();
}

async function handleDedicatedAddBookSubmit(e) {
  e.preventDefault();
  const isbn = document.getElementById("pageBookIsbn").value.trim();
  const title = document.getElementById("pageBookTitle").value.trim();
  const author = document.getElementById("pageBookAuthor").value.trim();
  const category = document.getElementById("pageBookCategory").value.trim();
  const copies = parseInt(document.getElementById("pageBookCopies").value, 10);

  if (!isbn || !title || !author || !category) {
    showToast("Please fill in all required book details.", "error");
    return;
  }

  const btn = document.getElementById("btnSubmitDedicatedAddBook");
  if (btn) {
    btn.disabled = true;
    btn.textContent = "Saving Book...";
  }

  try {
    const res = await fetch("/api/books", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ isbn, title, author, category, copies_available: copies })
    });
    const result = await res.json();
    if (!res.ok) throw new Error(result.detail || "Failed to add book");

    showToast(`Success: '${title}' has been added to the library catalogue!`, "success");
    resetAddBookForm();
    await loadBooks();
    // Switch to books view to see the new book in catalogue
    switchView("books");
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = "<span>💾</span> Add Book to Catalogue";
    }
  }
}

// ==================== BORROWERS MODULE ====================

async function loadBorrowers() {
  try {
    const res = await fetch("/api/borrowers");
    if (!res.ok) throw new Error("Failed to load borrowers");
    allBorrowersCache = await res.json();
    filterBorrowers();
  } catch (err) {
    showToast("Could not load borrowers", "error");
  }
}

function filterBorrowers() {
  const search = document.getElementById("borrowerSearchInput").value.toLowerCase().trim();
  const filtered = allBorrowersCache.filter(b => {
    return !search ||
      b.borrower_name.toLowerCase().includes(search) ||
      b.roll_no.toLowerCase().includes(search);
  });

  const tbody = document.getElementById("borrowersTableBody");
  if (!tbody) return;

  if (filtered.length === 0) {
    tbody.innerHTML = `<tr><td colspan="4" style="text-align:center; padding: 24px; color: var(--text-dim);">No borrowers registered yet.</td></tr>`;
    return;
  }

  tbody.innerHTML = filtered.map(b => `
    <tr>
      <td style="color:var(--text-dim); font-weight:700;">${b.borrower_id}</td>
      <td style="font-weight:600; color:var(--text-main);">${escapeHtml(b.borrower_name)}</td>
      <td><code>${escapeHtml(b.roll_no)}</code></td>
      <td>
        <button class="btn btn-secondary btn-sm" onclick="quickIssueToBorrower(${b.borrower_id})">
          Issue Book To Member →
        </button>
      </td>
    </tr>
  `).join("");
}

// ==================== CIRCULATION DESK MODULE ====================

async function loadCirculationData() {
  try {
    // 1. Load In-Stock Books for Checkout dropdown
    const booksRes = await fetch("/api/books");
    const books = await booksRes.json();
    allBooksCache = books;

    const bookSelect = document.getElementById("issueBookSelect");
    const availableBooks = books.filter(b => b.copies_available > 0);
    bookSelect.innerHTML = '<option value="">-- Choose Book in Stock --</option>' +
      availableBooks.map(b => `<option value="${b.book_id}">${b.title} (${b.category}) - ${b.copies_available} left</option>`).join("");

    // 2. Load Borrowers dropdown
    const borrowersRes = await fetch("/api/borrowers");
    const borrowers = await borrowersRes.json();
    allBorrowersCache = borrowers;

    const borrowerSelect = document.getElementById("issueBorrowerSelect");
    borrowerSelect.innerHTML = '<option value="">-- Choose Registered Borrower --</option>' +
      borrowers.map(b => `<option value="${b.borrower_id}">${b.borrower_name} (${b.roll_no})</option>`).join("");

    // 3. Load Active Loans Table
    const loansRes = await fetch("/api/loans/active");
    allActiveLoansCache = await loansRes.json();
    filterActiveLoans();
  } catch (err) {
    showToast("Failed to load circulation desk data", "error");
  }
}

function filterActiveLoans() {
  const search = document.getElementById("circulationSearchInput")?.value.toLowerCase().trim() || "";
  const filtered = allActiveLoansCache.filter(l => {
    return !search ||
      l.title.toLowerCase().includes(search) ||
      l.borrower_name.toLowerCase().includes(search) ||
      l.roll_no.toLowerCase().includes(search);
  });

  const tbody = document.getElementById("activeLoansTableBody");
  if (!tbody) return;

  if (filtered.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding: 24px; color: var(--text-dim);">No active unreturned loans.</td></tr>`;
    return;
  }

  tbody.innerHTML = filtered.map(l => {
    const statusBadge = l.is_overdue
      ? `<span class="badge badge-overdue">🔴 ${l.days_overdue} Day(s) Overdue</span>`
      : `<span class="badge badge-active">🟢 Active / On Time</span>`;

    return `
      <tr>
        <td style="font-weight:700; color:var(--text-dim);">#${l.loan_id}</td>
        <td style="font-weight:600; color:var(--text-main);">${escapeHtml(l.title)}</td>
        <td>${escapeHtml(l.borrower_name)}</td>
        <td><code>${escapeHtml(l.roll_no)}</code></td>
        <td>${l.issue_date}</td>
        <td>${l.due_date}</td>
        <td>${statusBadge}</td>
        <td>
          <button class="btn btn-success btn-sm" onclick="openReturnModal(${l.loan_id}, '${escapeQuote(l.title)}', '${escapeQuote(l.borrower_name)}')">
            Return Check-in ↵
          </button>
        </td>
      </tr>
    `;
  }).join("");
}

// Quick Issue Shortcuts
function quickIssueBook(bookId) {
  switchView("circulation");
  setTimeout(() => {
    const select = document.getElementById("issueBookSelect");
    if (select) select.value = bookId;
  }, 100);
}

function quickIssueToBorrower(borrowerId) {
  switchView("circulation");
  setTimeout(() => {
    const select = document.getElementById("issueBorrowerSelect");
    if (select) select.value = borrowerId;
  }, 100);
}

// ==================== ANALYTICS & INTERACTIVE CHART.JS MODULE ====================

async function loadAnalyticsData() {
  try {
    // Fetch Data for Interactive Vector Charts
    const [popRes, trendsRes, catRes, distRes, topBorrRes, healthDataRes, punctDataRes] = await Promise.all([
      fetch("/api/analytics/popular?limit=10"),
      fetch("/api/analytics/trends"),
      fetch("/api/analytics/categories"),
      fetch("/api/analytics/duration-distribution"),
      fetch("/api/analytics/top-borrowers?limit=8"),
      fetch("/api/analytics/inventory-health"),
      fetch("/api/analytics/punctuality")
    ]);

    // Chart 1: Popular Books (Horizontal Bar Chart)
    if (popRes.ok) {
      const books = await popRes.json();
      renderBarChart("chartPopularCanvas", books.map(b => b.title), books.map(b => b.borrow_count), "#3b82f6", "Times Borrowed", true);

      // Populate Table
      const tbody = document.getElementById("popularBooksReportBody");
      tbody.innerHTML = books.map((b, i) => `
        <tr>
          <td style="font-weight:700; color:var(--primary); font-size:15px;">#${i + 1}</td>
          <td style="font-weight:600; color:var(--text-main);">${escapeHtml(b.title)}</td>
          <td><span class="badge badge-category">${escapeHtml(b.category)}</span></td>
          <td>${escapeHtml(b.author)}</td>
          <td style="font-weight:700; color:var(--accent-cyan); font-size:14px;">${b.borrow_count} times</td>
          <td>${b.copies_available} in stock</td>
        </tr>
      `).join("");
    }

    // Chart 2: Monthly Trends (Multi-line Area Chart)
    if (trendsRes.ok) {
      const trends = await trendsRes.json();
      renderLineChart("chartTrendsCanvas", trends.map(t => t["Year-Month"]), [
        { label: "Total Checkouts", data: trends.map(t => t["Total Loans"]), color: "#38bdf8" },
        { label: "Returned Completed", data: trends.map(t => t["Returned"]), color: "#34d399" },
        { label: "Overdue Pending", data: trends.map(t => t["Overdue"]), color: "#f43f5e" }
      ]);

      // Populate Table
      const tbody = document.getElementById("monthlyTrendsBody");
      tbody.innerHTML = trends.map(t => `
        <tr>
          <td style="font-weight:600; color:var(--text-main);"><code>${t["Year-Month"]}</code></td>
          <td style="font-weight:700; color:var(--accent-cyan);">${t["Total Loans"]}</td>
          <td><span class="badge badge-in-stock">${t["Returned"]}</span></td>
          <td>${t["Active / Pending"]}</td>
          <td>${t["Overdue"] > 0 ? `<span class="badge badge-overdue">${t["Overdue"]}</span>` : "0"}</td>
        </tr>
      `).join("");
    }

    // Chart 3: Category Doughnut Chart
    if (catRes.ok) {
      const categories = await catRes.json();
      renderDoughnutChart("chartCategoryCanvas", categories.map(c => c.Category), categories.map(c => c["Times Borrowed"]), [
        "#3b82f6", "#10b981", "#f59e0b", "#ec4899", "#8b5cf6", "#06b6d4", "#64748b"
      ]);

      // Populate Table
      const tbody = document.getElementById("categorySummaryBody");
      tbody.innerHTML = categories.map(c => `
        <tr>
          <td style="font-weight:600; color:var(--text-main);">${escapeHtml(c.Category)}</td>
          <td>${c["Total Titles"]}</td>
          <td>${c["Available Copies"]}</td>
          <td style="font-weight:700; color:var(--accent-cyan);">${c["Times Borrowed"]}</td>
          <td>
            <div style="display:flex; align-items:center; gap:8px;">
              <div style="flex:1; background:rgba(255,255,255,0.06); height:6px; border-radius:3px; overflow:hidden;">
                <div style="width:${c["Circulation Share (%)"]}%; background:var(--primary); height:100%;"></div>
              </div>
              <span style="font-size:12px; font-weight:700; min-width:42px;">${c["Circulation Share (%)"]}%</span>
            </div>
          </td>
        </tr>
      `).join("");
    }

    // Chart 4: Duration Binned Distribution (Histogram)
    if (distRes.ok) {
      const dist = await distRes.json();
      renderBarChart("chartDurationCanvas", dist.labels, dist.counts, "#f59e0b", "Number of Loans", false);
    }

    // Chart 5: Top Borrowers Leaderboard
    if (topBorrRes.ok) {
      const topBorr = await topBorrRes.json();
      renderBarChart("chartBorrowersCanvas", topBorr.map(b => b.borrower_name), topBorr.map(b => b.total_borrows), "#10b981", "Books Borrowed", false);
    }

    // Chart 6: Inventory Allocation
    if (healthDataRes.ok) {
      const health = await healthDataRes.json();
      renderDoughnutChart("chartInventoryCanvas", ["Available On Shelf", "Currently Checked Out"], [health.available_copies, health.on_loan_copies], [
        "#10b981", "#3b82f6"
      ]);
    }

    // Chart 7: Return Punctuality
    if (punctDataRes.ok) {
      const punct = await punctDataRes.json();
      renderDoughnutChart("chartPunctualityCanvas", ["Returned On Time", "Returned Late", "Active (Due Soon)", "Active (Overdue)"], [
        punct.returned_on_time, punct.returned_late, punct.active_on_time, punct.active_overdue
      ], ["#10b981", "#f59e0b", "#3b82f6", "#f43f5e"]);
    }

  } catch (err) {
    console.error("Analytics load error:", err);
    showToast("Error loading analytics data", "error");
  }
}


// ==================== CHART.JS INTERACTIVE VECTOR HELPERS ====================

function destroyExistingChart(canvasId) {
  if (chartInstances[canvasId]) {
    chartInstances[canvasId].destroy();
    delete chartInstances[canvasId];
  }
}

function renderBarChart(canvasId, labels, data, color, datasetLabel = "Count", horizontal = false) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  destroyExistingChart(canvasId);

  // Shorten labels for clean display
  const cleanLabels = labels.map(l => l.length > 22 ? l.slice(0, 20) + "..." : l);

  chartInstances[canvasId] = new Chart(canvas, {
    type: "bar",
    data: {
      labels: cleanLabels,
      datasets: [{
        label: datasetLabel,
        data: data,
        backgroundColor: color + "cc",
        borderColor: color,
        borderWidth: 1.5,
        borderRadius: 6,
        hoverBackgroundColor: color
      }]
    },
    options: {
      indexAxis: horizontal ? "y" : "x",
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "#0f172a",
          titleColor: "#f8fafc",
          bodyColor: "#94a3b8",
          borderColor: "rgba(255,255,255,0.1)",
          borderWidth: 1,
          padding: 10,
          callbacks: {
            title: function(context) {
              return labels[context[0].dataIndex] || context[0].label;
            }
          }
        }
      },
      scales: {
        x: {
          grid: { color: "rgba(255, 255, 255, 0.05)" },
          ticks: { color: "#94a3b8", font: { family: "Plus Jakarta Sans", size: 11 } }
        },
        y: {
          grid: { color: "rgba(255, 255, 255, 0.05)" },
          ticks: { color: "#94a3b8", font: { family: "Plus Jakarta Sans", size: 11 }, precision: 0 }
        }
      }
    }
  });
}

function renderLineChart(canvasId, labels, datasets) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  destroyExistingChart(canvasId);

  chartInstances[canvasId] = new Chart(canvas, {
    type: "line",
    data: {
      labels: labels,
      datasets: datasets.map(ds => ({
        label: ds.label,
        data: ds.data,
        borderColor: ds.color,
        backgroundColor: ds.color + "1a",
        fill: true,
        tension: 0.35,
        borderWidth: 2.5,
        pointBackgroundColor: ds.color,
        pointRadius: 4,
        pointHoverRadius: 6
      }))
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: { color: "#cbd5e1", font: { family: "Plus Jakarta Sans", size: 12 } }
        },
        tooltip: {
          backgroundColor: "#0f172a",
          titleColor: "#f8fafc",
          borderColor: "rgba(255,255,255,0.1)",
          borderWidth: 1,
          padding: 10
        }
      },
      scales: {
        x: {
          grid: { color: "rgba(255, 255, 255, 0.05)" },
          ticks: { color: "#94a3b8", font: { family: "Plus Jakarta Sans" } }
        },
        y: {
          grid: { color: "rgba(255, 255, 255, 0.05)" },
          ticks: { color: "#94a3b8", font: { family: "Plus Jakarta Sans" }, precision: 0 }
        }
      }
    }
  });
}

function renderDoughnutChart(canvasId, labels, data, colors) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  destroyExistingChart(canvasId);

  chartInstances[canvasId] = new Chart(canvas, {
    type: "doughnut",
    data: {
      labels: labels,
      datasets: [{
        data: data,
        backgroundColor: colors.map(c => c + "dd"),
        borderColor: "#1e293b",
        borderWidth: 2,
        hoverOffset: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "68%",
      plugins: {
        legend: {
          position: "right",
          labels: { color: "#cbd5e1", font: { family: "Plus Jakarta Sans", size: 12 }, padding: 14 }
        },
        tooltip: {
          backgroundColor: "#0f172a",
          titleColor: "#f8fafc",
          bodyColor: "#94a3b8",
          borderColor: "rgba(255,255,255,0.1)",
          borderWidth: 1,
          padding: 10
        }
      }
    }
  });
}


// ==================== FORM ACTIONS & MUTATIONS ====================

async function handleAddBorrowerSubmit(e) {
  e.preventDefault();
  const name = document.getElementById("newBorrowerName").value.trim();
  const roll = document.getElementById("newBorrowerRoll").value.trim();

  try {
    const res = await fetch("/api/borrowers", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ borrower_name: name, roll_no: roll })
    });
    const result = await res.json();
    if (!res.ok) throw new Error(result.detail || "Failed to register borrower");

    showToast(`Borrower '${name}' registered successfully!`, "success");
    closeModal("addBorrowerModal");
    document.getElementById("addBorrowerForm").reset();
    loadBorrowers();
    loadDashboardData();
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function handleIssueSubmit(e) {
  e.preventDefault();
  const bookId = parseInt(document.getElementById("issueBookSelect").value, 10);
  const borrowerId = parseInt(document.getElementById("issueBorrowerSelect").value, 10);
  const issueDate = document.getElementById("issueDateInput").value;
  const loanDays = parseInt(document.getElementById("loanDaysInput").value, 10);

  if (!bookId || !borrowerId) {
    showToast("Please choose both a book and a borrower.", "error");
    return;
  }

  try {
    const res = await fetch("/api/loans/issue", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        book_id: bookId,
        borrower_id: borrowerId,
        issue_date: issueDate,
        loan_days: loanDays
      })
    });
    const result = await res.json();
    if (!res.ok) throw new Error(result.detail || "Failed to issue book");

    showToast(result.message, "success");
    loadCirculationData();
    loadDashboardData();
  } catch (err) {
    showToast(err.message, "error");
  }
}

function openReturnModal(loanId, bookTitle, borrowerName) {
  document.getElementById("returnLoanId").value = loanId;
  document.getElementById("returnModalBookTitle").textContent = `Book: ${bookTitle}`;
  document.getElementById("returnModalBorrowerInfo").textContent = `Issued to: ${borrowerName} (Loan #${loanId})`;
  document.getElementById("returnDateInput").value = new Date().toISOString().split("T")[0];
  openModal("returnBookModal");
}

async function handleReturnSubmit(e) {
  e.preventDefault();
  const loanId = parseInt(document.getElementById("returnLoanId").value, 10);
  const returnDate = document.getElementById("returnDateInput").value;

  try {
    const res = await fetch("/api/loans/return", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ loan_id: loanId, return_date: returnDate })
    });
    const result = await res.json();
    if (!res.ok) throw new Error(result.detail || "Failed to return book");

    showToast(result.message, "success");
    closeModal("returnBookModal");
    loadCirculationData();
    loadDashboardData();
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function handleResetSampleData() {
  if (!confirm("Are you sure you want to reset the database and reload 20 realistic sample books, borrowers, and loans?")) {
    return;
  }

  try {
    const res = await fetch("/api/seed", { method: "POST" });
    const result = await res.json();
    if (!res.ok) throw new Error(result.detail || "Failed to seed sample data");

    showToast("Sample data reloaded successfully!", "success");
    loadDashboardData();
  } catch (err) {
    showToast(err.message, "error");
  }
}


// ==================== MODAL HELPERS ====================

function openModal(id) {
  const modal = document.getElementById(id);
  if (modal) modal.classList.add("active");
}

function closeModal(id) {
  const modal = document.getElementById(id);
  if (modal) modal.classList.remove("active");
}

function openAddBorrowerModal() { openModal("addBorrowerModal"); }


// ==================== TOAST NOTIFICATIONS ====================

function showToast(message, type = "info") {
  const container = document.getElementById("toastContainer");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast ${type}`;

  const icon = type === "success" ? "✅" : (type === "error" ? "❌" : "ℹ️");
  toast.innerHTML = `<span>${icon}</span> <span>${escapeHtml(message)}</span>`;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(10px)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function escapeQuote(str) {
  if (!str) return "";
  return String(str).replace(/'/g, "\\'");
}
