import csv
import tkinter as tk
from tkinter import ttk
from rapidfuzz import fuzz


# Load CSV Data
def load_books():
    books = []
    with open(r'E:\동건\가천대\2025-2\알고리즘\Project\books.csv', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            books.append(row)
    return books


books_data = load_books()


# Search + Filtering + Sorting
def search_books():
    query = search_entry.get().lower().strip()
    selected_language = language_var.get()

    # Filter enable states
    filters_enabled = {
        "nlp": nlp_filter_var.get(),
        "rating": rating_filter_var.get(),
        "pages": pages_filter_var.get(),
        "ratings_count": ratings_count_filter_var.get(),
        "reviews": reviews_filter_var.get(),
        "date": date_filter_var.get(),
        "language": lang_filter_var.get(),
    }

    # Range Inputs
    rating_min, rating_max = float(rating_min_entry.get() or 0), float(rating_max_entry.get() or 5)
    pages_min, pages_max = int(pages_min_entry.get() or 0), int(pages_max_entry.get() or 10000)
    ratings_count_min, ratings_count_max = int(ratings_count_min_entry.get() or 0), int(ratings_count_max_entry.get() or 10000000)
    reviews_min, reviews_max = int(reviews_min_entry.get() or 0), int(reviews_max_entry.get() or 1000000)
    date_min, date_max = int(date_min_entry.get() or 0), int(date_max_entry.get() or 2100)

    results = []

    # Process each row
    for row in books_data:

        # Fuzzy NLP Searching
        if query:
            score_title = fuzz.partial_ratio(query, row['title'].lower())
            score_author = fuzz.partial_ratio(query, row['authors'].lower())
            score_pub = fuzz.partial_ratio(query, row['publisher'].lower())
            nlp_score = max(score_title, score_author, score_pub)

            if nlp_score < 60:
                continue
        else:
            # No query: NLP = neutral
            nlp_score = 100

        # Apply Filters
        if filters_enabled["rating"] and not (rating_min <= float(row["average_rating"]) <= rating_max):
            continue
        if filters_enabled["pages"] and not (pages_min <= int(row["num_pages"]) <= pages_max):
            continue
        if filters_enabled["ratings_count"] and not (ratings_count_min <= int(row["ratings_count"]) <= ratings_count_max):
            continue
        if filters_enabled["reviews"] and not (reviews_min <= int(row["text_reviews_count"]) <= reviews_max):
            continue
        if filters_enabled["date"]:
            pub_year = int(row["publication_date"].split("/")[-1])
            if not (date_min <= pub_year <= date_max):
                continue

        # Language with prefix logic
        if filters_enabled["language"] and selected_language != "Any":
            lang = row["language_code"]

            # English family
            if selected_language == "eng":
                if not lang.startswith("en"):
                    continue

            # Chinese family
            elif selected_language == "zho":
                if not lang.startswith("zh"):
                    continue

            # Strict match for others
            else:
                if lang != selected_language:
                    continue

        results.append((row, nlp_score))

    # --------------------- SORTING LOGIC ---------------------

    # NLP FIRST when enabled
    if filters_enabled["nlp"]:
        results.sort(key=lambda r: r[1], reverse=(nlp_order.get() == "desc"))

    # If other filters are enabled, apply their sort priorities
    if any(filters_enabled.values()):
        sort_rules = [
            ("pages", lambda x: int(x["num_pages"]), pages_order.get()),
            ("date", lambda x: int(x["publication_date"].split("/")[-1]), date_order.get()),
            ("language", lambda x: x["language_code"], lang_order.get()),
            ("rating", lambda x: float(x["average_rating"]), rating_order.get()),
            ("ratings_count", lambda x: int(x["ratings_count"]), ratings_count_order.get()),
            ("reviews", lambda x: int(x["text_reviews_count"]), reviews_order.get())
        ]

        active_rules = [(func, direction)
                        for key, func, direction in sort_rules
                        if filters_enabled[key]]

        for func, direction in reversed(active_rules):
            results.sort(key=lambda r: func(r[0]), reverse=(direction == "desc"))

    else:
        # No sorting filters → default by bookID
        results.sort(key=lambda r: int(r[0]['bookID']))

    # Display results
    display_results(results)


# Display results
def display_results(data):
    for row in tree.get_children():
        tree.delete(row)

    for book, score in data:
        tree.insert("", tk.END, values=(
            book['bookID'], book['title'], book['authors'], book['average_rating'], book['isbn'],
            book['language_code'], book['num_pages'], book['ratings_count'], book['text_reviews_count'],
            book['publication_date'], book['publisher'], score
        ))


# -------------------- GUI --------------------
window = tk.Tk()
window.title("Book Search Engine | v10")


# Sort Order Variables
nlp_order = tk.StringVar(value="desc")
rating_order = tk.StringVar(value="desc")
pages_order = tk.StringVar(value="desc")
ratings_count_order = tk.StringVar(value="desc")
reviews_order = tk.StringVar(value="desc")
date_order = tk.StringVar(value="desc")
lang_order = tk.StringVar(value="asc")


# Search Row
tk.Label(window, text="Keyword Search:").grid(row=0, column=0, padx=5, pady=5)
search_entry = tk.Entry(window, width=40)
search_entry.grid(row=0, column=1, padx=5, pady=5)
tk.Button(window, text="🔍 Search", width=12, command=search_books).grid(row=0, column=2, padx=10)


# Filter Variables
nlp_filter_var = tk.BooleanVar()
rating_filter_var = tk.BooleanVar()
pages_filter_var = tk.BooleanVar()
ratings_count_filter_var = tk.BooleanVar()
reviews_filter_var = tk.BooleanVar()
date_filter_var = tk.BooleanVar()
lang_filter_var = tk.BooleanVar()


# NLP Sorting Filter
tk.Checkbutton(window, text="NLP Accuracy First", variable=nlp_filter_var).grid(row=1, column=0, sticky="w")
tk.Radiobutton(window, text="⬆", value="asc", variable=nlp_order).grid(row=1, column=1)
tk.Radiobutton(window, text="⬇", value="desc", variable=nlp_order).grid(row=1, column=2)


# Helper function
def make_filter(label, row, min_default, max_default, order_var):
    var = globals()[f"{label}_filter_var"]
    tk.Checkbutton(window, text=label.replace("_", " ").title(), variable=var).grid(row=row, column=0, sticky="w")

    entry_min = tk.Entry(window, width=6)
    entry_max = tk.Entry(window, width=6)
    entry_min.insert(0, min_default)
    entry_max.insert(0, max_default)

    entry_min.grid(row=row, column=1)
    entry_max.grid(row=row, column=2)

    tk.Radiobutton(window, text="⬆", value="asc", variable=order_var).grid(row=row, column=3)
    tk.Radiobutton(window, text="⬇", value="desc", variable=order_var).grid(row=row, column=4)

    return entry_min, entry_max


# Create Filters
rating_min_entry, rating_max_entry = make_filter("rating", 2, "0", "5", rating_order)
pages_min_entry, pages_max_entry = make_filter("pages", 3, "0", "2000", pages_order)
ratings_count_min_entry, ratings_count_max_entry = make_filter("ratings_count", 4, "0", "5000000", ratings_count_order)
reviews_min_entry, reviews_max_entry = make_filter("reviews", 5, "0", "100000", reviews_order)
date_min_entry, date_max_entry = make_filter("date", 6, "1900", "2100", date_order)


# Language Filter with prefix behavior
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


# Results Table
cols = ("ID", "Title", "Author", "Rating", "ISBN", "Lang", "Pages",
        "Ratings", "Reviews", "Year", "Publisher", "NLP Score")

tree = ttk.Treeview(window, columns=cols, show="headings", height=18)

column_widths = [50, 250, 150, 60, 90, 60, 60, 80, 80, 80, 180, 80]
for col, w in zip(cols, column_widths):
    tree.heading(col, text=col)
    tree.column(col, width=w)

tree.grid(row=8, column=0, columnspan=5, padx=5, pady=10)


window.mainloop()