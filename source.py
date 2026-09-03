import csv
import tkinter as tk
from tkinter import ttk
from rapidfuzz import fuzz


# Load CSV
def load_books():
    books = []
    with open(r"E:\동건\가천대\2025-2\알고리즘\Project\books.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            books.append(row)
    return books


books_data = load_books()


# Search + Filter + Priority Sort
def search_books():
    query = search_entry.get().lower().strip()
    selected_language = language_var.get()

    filters_enabled = {
        "nlp": nlp_filter_var.get(),
        "rating": rating_filter_var.get(),
        "pages": pages_filter_var.get(),
        "ratings_count": ratings_count_filter_var.get(),
        "reviews": reviews_filter_var.get(),
        "date": date_filter_var.get(),
        "language": lang_filter_var.get(),
    }

    # Get numeric and date range values
    rating_min, rating_max = float(rating_min_entry.get() or 0), float(rating_max_entry.get() or 5)
    pages_min, pages_max = int(pages_min_entry.get() or 0), int(pages_max_entry.get() or 10000)
    rc_min, rc_max = int(ratings_count_min_entry.get() or 0), int(ratings_count_max_entry.get() or 10000000)
    rv_min, rv_max = int(reviews_min_entry.get() or 0), int(reviews_max_entry.get() or 1000000)
    year_min, year_max = int(date_min_entry.get() or 0), int(date_max_entry.get() or 2100)

    results = []

    for row in books_data:

        # ---------- NLP SCORE ----------
        if query:
            title_score = fuzz.partial_ratio(query, row["title"].lower())
            author_score = fuzz.partial_ratio(query, row["authors"].lower())
            pub_score = fuzz.partial_ratio(query, row["publisher"].lower())
            nlp_score = max(title_score, author_score, pub_score)

            if nlp_score < 60:
                continue
        else:
            nlp_score = 100  # neutral

        # ---------- FILTERS ----------
        if filters_enabled["rating"] and not (rating_min <= float(row["average_rating"]) <= rating_max):
            continue
        if filters_enabled["pages"] and not (pages_min <= int(row["num_pages"]) <= pages_max):
            continue
        if filters_enabled["ratings_count"] and not (rc_min <= int(row["ratings_count"]) <= rc_max):
            continue
        if filters_enabled["reviews"] and not (rv_min <= int(row["text_reviews_count"]) <= rv_max):
            continue
        if filters_enabled["date"]:
            year = int(row["publication_date"].split("/")[-1])
            if not (year_min <= year <= year_max):
                continue

        # Language with prefix logic
        if filters_enabled["language"] and selected_language != "Any":
            lang = row["language_code"]

            if selected_language == "eng":       # English family prefix
                if not lang.startswith("en"):
                    continue
            elif selected_language == "zho":     # Chinese family prefix
                if not lang.startswith("zh"):
                    continue
            else:
                if lang != selected_language:
                    continue

        results.append((row, nlp_score))

    # -------------------------- SORTING PRIORITY --------------------------
    # STRICT ORDER:
    # NLP → Pages → Date → Language → Rating → Ratings Count → Reviews

    # 7) Reviews
    if filters_enabled["reviews"]:
        results.sort(key=lambda r: int(r[0]["text_reviews_count"]), reverse=(reviews_order.get() == "desc"))

    # 6) Ratings Count
    if filters_enabled["ratings_count"]:
        results.sort(key=lambda r: int(r[0]["ratings_count"]), reverse=(ratings_count_order.get() == "desc"))

    # 5) Rating
    if filters_enabled["rating"]:
        results.sort(key=lambda r: float(r[0]["average_rating"]), reverse=(rating_order.get() == "desc"))

    # 4) Language
    if filters_enabled["language"]:
        results.sort(key=lambda r: r[0]["language_code"], reverse=(lang_order.get() == "desc"))

    # 3) Date
    if filters_enabled["date"]:
        results.sort(key=lambda r: int(r[0]["publication_date"].split("/")[-1]),
                     reverse=(date_order.get() == "desc"))

    # 2) Pages
    if filters_enabled["pages"]:
        results.sort(key=lambda r: int(r[0]["num_pages"]), reverse=(pages_order.get() == "desc"))

    # 1) NLP FIRST if enabled
    if filters_enabled["nlp"]:
        results.sort(key=lambda r: r[1], reverse=(nlp_order.get() == "desc"))

    # If NO filter is used: sort by bookID
    if not any(filters_enabled.values()):
        results.sort(key=lambda r: int(r[0]["bookID"]))

    # Display results
    display_results(results)


# Display results in table
def display_results(data):
    tree.delete(*tree.get_children())

    for book, score in data:
        tree.insert("", tk.END, values=(
            book["bookID"], book["title"], book["authors"], book["average_rating"], book["isbn"],
            book["language_code"], book["num_pages"], book["ratings_count"], book["text_reviews_count"],
            book["publication_date"], book["publisher"], round(score, 2)
        ))


# ---------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------
window = tk.Tk()
window.title("Book Search Engine - v11")


# Sorting order variables
nlp_order = tk.StringVar(value="desc")
rating_order = tk.StringVar(value="desc")
pages_order = tk.StringVar(value="desc")
ratings_count_order = tk.StringVar(value="desc")
reviews_order = tk.StringVar(value="desc")
date_order = tk.StringVar(value="desc")
lang_order = tk.StringVar(value="asc")

# Search bar
tk.Label(window, text="Keyword Search:").grid(row=0, column=0, padx=5)
search_entry = tk.Entry(window, width=40)
search_entry.grid(row=0, column=1)
tk.Button(window, text="🔍 Search", command=search_books).grid(row=0, column=2, padx=5)


# Filter variables
nlp_filter_var = tk.BooleanVar()
rating_filter_var = tk.BooleanVar()
pages_filter_var = tk.BooleanVar()
ratings_count_filter_var = tk.BooleanVar()
reviews_filter_var = tk.BooleanVar()
date_filter_var = tk.BooleanVar()
lang_filter_var = tk.BooleanVar()


# NLP sorting filter
tk.Checkbutton(window, text="NLP Accuracy First", variable=nlp_filter_var).grid(row=1, column=0, sticky="w")
tk.Radiobutton(window, text="⬆", value="asc", variable=nlp_order).grid(row=1, column=1)
tk.Radiobutton(window, text="⬇", value="desc", variable=nlp_order).grid(row=1, column=2)


# Helper function for numeric filters
def make_filter(label, row, default_min, default_max, order_var):
    var = globals()[f"{label}_filter_var"]
    tk.Checkbutton(window, text=label.replace("_", " ").title(), variable=var).grid(row=row, column=0, sticky="w")

    entry_min = tk.Entry(window, width=6)
    entry_max = tk.Entry(window, width=6)
    entry_min.insert(0, default_min)
    entry_max.insert(0, default_max)

    entry_min.grid(row=row, column=1)
    entry_max.grid(row=row, column=2)

    tk.Radiobutton(window, text="⬆", value="asc", variable=order_var).grid(row=row, column=3)
    tk.Radiobutton(window, text="⬇", value="desc", variable=order_var).grid(row=row, column=4)

    return entry_min, entry_max


# Filters
rating_min_entry, rating_max_entry = make_filter("rating", 2, "0", "5", rating_order)
pages_min_entry, pages_max_entry = make_filter("pages", 3, "0", "2000", pages_order)
ratings_count_min_entry, ratings_count_max_entry = make_filter("ratings_count", 4, "0", "5000000", ratings_count_order)
reviews_min_entry, reviews_max_entry = make_filter("reviews", 5, "0", "100000", reviews_order)
date_min_entry, date_max_entry = make_filter("date", 6, "1900", "2100", date_order)


# Language filter
tk.Checkbutton(window, text="Language", variable=lang_filter_var).grid(row=7, column=0, sticky="w")
language_var = tk.StringVar(value="Any")
language_box = ttk.Combobox(
    window,
    textvariable=language_var,
    values=["Any", "eng", "spa", "fre", "ger", "zho"],
    width=10
)
language_box.grid(row=7, column=1)

tk.Radiobutton(window, text="⬆", value="asc", variable=lang_order).grid(row=7, column=3)
tk.Radiobutton(window, text="⬇", value="desc", variable=lang_order).grid(row=7, column=4)


# Results table
cols = (
    "ID", "Title", "Author", "Rating", "ISBN", "Lang", "Pages",
    "Ratings", "Reviews", "Year", "Publisher", "NLP Score"
)

tree = ttk.Treeview(window, columns=cols, show="headings", height=18)

column_widths = [50, 250, 150, 60, 100, 60, 60, 90, 90, 80, 180, 90]

for col, w in zip(cols, column_widths):
    tree.heading(col, text=col)
    tree.column(col, width=w)

tree.grid(row=8, column=0, columnspan=5, pady=10)


window.mainloop()
