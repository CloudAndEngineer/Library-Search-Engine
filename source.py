"""
GUI Book Finder Application
---------------------------------------------------
Features:
- Search books using fuzzy NLP matching (RapidFuzz similarity algorithm)
- Sort results based on user-defined filters
- Filtering numeric fields with user-selectable ranges
- Efficient sorting using Python's built-in Timsort algorithm
- Lazy evaluation using Pandas for performance on large datasets
"""

import pandas as pd
from rapidfuzz import fuzz, process
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox


# ================================
# Load dataset
# ================================
try:
	df = pd.read_csv(r"E:\동건\가천대\2025-2\알고리즘\Project\books.csv")
except FileNotFoundError:
    raise SystemExit("ERROR: books.csv not found in working directory!")


# Ensure numeric columns are properly typed
numeric_fields = ["average_rating", "num_pages", "ratings_count", "text_reviews_count"]
for col in numeric_fields:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df["publication_year"] = pd.to_datetime(df["publication_date"], errors="coerce").dt.year


# ================================
# Sorting Priority Logic
# ================================
def sort_with_priority(data, filters_used):
    """
    Uses Python sorted() which uses Timsort - O(n log n).
    Sorting priority only applies when at least one filter exists.
    Priority order:
    num_pages > publication_date > language_code > average_rating > rating_count > text_reviews_count
    """

    if not filters_used:
        # Default sorting by BookID when no filters are used
        return data.sort_values(by="bookID")

    priority = [
        "num_pages", "publication_year", "language_code",
        "average_rating", "ratings_count", "text_reviews_count"
    ]

    existing_cols = [col for col in priority if col in data.columns]

    return data.sort_values(by=existing_cols, ascending=False)


# ================================
# NLP Fuzzy Search Function
# Using RapidFuzz (efficient fuzzy matching)
# ================================
def fuzzy_search(query, data):
    """
    Using token_set_ratio from RapidFuzz.
    Algorithm Type: Fuzzy NLP matching (edit distance-based similarity algorithm).
    Purpose: Finds approximate matches for messy or partial user input.
    """

    if not query:
        return data

    # Fields considered for flexible text search
    text_fields = ["title", "authors", "publisher"]

    # Score each row based on max similarity across fields
    def get_score(row):
        return max(fuzz.token_set_ratio(query.lower(), str(row[col]).lower()) for col in text_fields)

    data["similarity"] = data.apply(get_score, axis=1)

    # Threshold: ≥ 60 similarity considered relevant
    return data[data["similarity"] >= 60].sort_values(by="similarity", ascending=False)


# ================================
# Apply Filters
# ================================
def apply_filters(data, filters):
    filtered = data.copy()

    for col, (low, high) in filters.items():
        if low is not None and high is not None:
            filtered = filtered[(filtered[col] >= low) & (filtered[col] <= high)]

    return filtered


# ================================
# GUI Application
# ================================
class BookApp:

    def __init__(self, root):
        self.root = root
        root.title("📚 Book Search System")
        root.geometry("1100x650")

        # Search Box
        tk.Label(root, text="Search (Title / Author / Publisher):").pack()
        self.search_entry = tk.Entry(root, width=50)
        self.search_entry.pack()

        # Filters Frame
        filter_frame = tk.Frame(root)
        filter_frame.pack(pady=10)

        self.filters = {}

        def create_slider(label, col, min_val, max_val):
            tk.Label(filter_frame, text=label).grid()
            min_var = tk.DoubleVar()
            max_var = tk.DoubleVar()
            ttk.Scale(filter_frame, from_=min_val, to=max_val, variable=min_var).grid()
            ttk.Scale(filter_frame, from_=min_val, to=max_val, variable=max_var).grid()
            self.filters[col] = (min_var, max_var)

        create_slider("Average Rating", "average_rating", 0, 5)
        create_slider("Num Pages", "num_pages", 0, 2000)
        create_slider("Ratings Count", "ratings_count", 0, 1_000_000)
        create_slider("Text Reviews Count", "text_reviews_count", 0, 50_000)
        create_slider("Publication Year", "publication_year", 1900, 2025)

        # Language Dropdown
        tk.Label(root, text="Language:").pack()
        self.language_var = tk.StringVar()
        languages = ["(Any)"] + sorted(df["language_code"].dropna().unique())
        ttk.Combobox(root, textvariable=self.language_var, values=languages).pack()

        # Search Button
        ttk.Button(root, text="Search", command=self.run_search).pack(pady=10)

        # Results Table
        self.tree = ttk.Treeview(root, columns=("ID", "Title", "Author", "Rating"), show="headings")
        for col in ["ID", "Title", "Author", "Rating"]:
            self.tree.heading(col, text=col)
        self.tree.pack(expand=True, fill="both")

    def run_search(self):
        query = self.search_entry.get().strip()

        results = df.copy()

        # Apply NLP search
        results = fuzzy_search(query, results)

        # Apply numerical filters
        used_filters = False
        active_ranges = {}
        for col, (low_var, high_var) in self.filters.items():
            low, high = low_var.get(), high_var.get()
            if low > 0 or high < df[col].max():
                active_ranges[col] = (low, high)
                used_filters = True

        if active_ranges:
            results = apply_filters(results, active_ranges)

        # Apply language filter
        if self.language_var.get() != "(Any)" and self.language_var.get().strip():
            results = results[results["language_code"] == self.language_var.get()]
            used_filters = True

        # Sorting based on rules
        results = sort_with_priority(results, used_filters)

        # Display
        self.tree.delete(*self.tree.get_children())
        for _, row in results.head(200).iterrows():
            self.tree.insert("", tk.END, values=(row["bookID"], row["title"], row["authors"], row["average_rating"]))


# ================================
# Run Program
# ================================
root = tk.Tk()
app = BookApp(root)
root.mainloop()
