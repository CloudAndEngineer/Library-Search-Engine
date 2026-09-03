"""
Final Updated Version
--------------------------------------------------
✔ Sorting now uses ONLY enabled filters in priority order
✔ No filter enabled → sort by bookID only
✔ Result table now includes more metadata fields
"""

import pandas as pd
from rapidfuzz import fuzz
import tkinter as tk
from tkinter import ttk


# ===========================================================
# Load Dataset
# ===========================================================
try:
	df = pd.read_csv(r"E:동건\가천대\2025-2\알고리즘\Project\books.csv", low_memory=False)
except FileNotFoundError:
    raise SystemExit("ERROR: books.csv not found in working directory!")

numeric_fields = ["average_rating", "num_pages", "ratings_count", "text_reviews_count"]
for col in numeric_fields:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df["publication_year"] = pd.to_datetime(df["publication_date"], errors="coerce").dt.year


# ===========================================================
# Sorting Logic (modified per new rules)
# ===========================================================
SORT_PRIORITY = [
    "num_pages",
    "publication_year",
    "language_code",
    "average_rating",
    "ratings_count",
    "text_reviews_count"
]

def dynamic_sort(data, enabled_filters, language_enabled):
    """
    - If no filters ON → sort by bookID only
    - If filters ON → sort using only enabled filter columns in priority order
    """
    if not enabled_filters and not language_enabled:
        return data.sort_values(by="bookID")

    sort_keys = [f for f in SORT_PRIORITY if f in enabled_filters]

    # If language filter is used, treat language_code as highest priority after pages
    if language_enabled and "language_code" not in sort_keys:
        sort_keys.insert(2, "language_code")

    return data.sort_values(by=sort_keys, ascending=False)



# ===========================================================
# NLP Search (RapidFuzz)
# ===========================================================
def fuzzy_search(query, data):
    if not query:
        return data

    text_fields = ["title", "authors", "publisher"]

    def score(row):
        return max(fuzz.token_set_ratio(query.lower(), str(row[c]).lower()) for c in text_fields)

    data["similarity"] = data.apply(score, axis=1)
    return data[data["similarity"] >= 60].sort_values(by="similarity", ascending=False)



# ===========================================================
# Apply Filters
# ===========================================================
def apply_filters(data, filter_state):
    filtered = data.copy()

    for col, (enabled, low, high) in filter_state.items():
        if enabled:
            filtered = filtered[(filtered[col] >= low) & (filtered[col] <= high)]

    return filtered



# ===========================================================
# GUI Class
# ===========================================================
class BookApp:

    def __init__(self, root):
        self.root = root
        root.title("📚 Book Search System (Final Version)")
        root.geometry("1400x800")

        tk.Label(root, text="Search Title / Author / Publisher:", font=("Arial", 12)).pack(pady=6)
        self.search_entry = tk.Entry(root, width=60)
        self.search_entry.pack()

        # ------------ FILTER UI ------------
        filter_frame = tk.Frame(root)
        filter_frame.pack(pady=10)
        self.filter_settings = {}

        def create_filter_row(label, col_name, min_val, max_val):
            row = tk.Frame(filter_frame)
            row.pack(anchor="w", pady=3)

            tk.Label(row, text=label).pack(side="left", padx=5)

            status_var = tk.IntVar(value=0)
            tk.Radiobutton(row, text="Off", variable=status_var, value=0).pack(side="left")
            tk.Radiobutton(row, text="On", variable=status_var, value=1).pack(side="left")

            min_var = tk.DoubleVar(value=min_val)
            max_var = tk.DoubleVar(value=max_val)

            s1 = ttk.Scale(row, from_=min_val, to=max_val, variable=min_var, orient=tk.HORIZONTAL, length=150)
            s2 = ttk.Scale(row, from_=min_val, to=max_val, variable=max_var, orient=tk.HORIZONTAL, length=150)
            s1.pack(side="left", padx=5)
            s2.pack(side="left", padx=5)

            lbl = tk.Label(filter_frame, text=f"Min: {min_val}  Max: {max_val}", fg="gray")
            lbl.pack(anchor="w", padx=25)

            def update(*_):
                lbl.config(text=f"Min: {min_var.get():.1f}   Max: {max_var.get():.1f}")

            min_var.trace_add("write", update)
            max_var.trace_add("write", update)

            self.filter_settings[col_name] = (status_var, min_var, max_var)

        # Filter sliders
        create_filter_row("Average Rating", "average_rating", 0, 5)
        create_filter_row("Num Pages", "num_pages", 0, 2000)
        create_filter_row("Ratings Count", "ratings_count", 0, 1_000_000)
        create_filter_row("Text Reviews Count", "text_reviews_count", 0, 50_000)
        create_filter_row("Published Year", "publication_year", 1900, 2025)

        # Language filter
        tk.Label(root, text="Language", font=("Arial", 11)).pack()
        self.language_var = tk.StringVar(value="(Any)")
        lang_options = ["(Any)"] + sorted(df["language_code"].dropna().unique())
        ttk.Combobox(root, textvariable=self.language_var, values=lang_options).pack(pady=5)

        # Search button
        ttk.Button(root, text="Search", command=self.run_search).pack(pady=10)

        # ------------ TABLE UI ------------
        columns = (
            "ID","Title","Author","Rating","ISBN","Lang",
            "Pages","Rating Count","Review Count","Published Date","Publisher"
        )

        self.tree = ttk.Treeview(root, columns=columns, show="headings")

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=140 if col == "Title" else 100)

        self.tree.pack(expand=True, fill="both")


    def run_search(self):
        query = self.search_entry.get().strip()
        results = df.copy()

        results = fuzzy_search(query, results)

        enabled_filter_keys = []
        compiled_filters = {}

        for col, (status, low, high) in self.filter_settings.items():
            enabled = status.get() == 1
            compiled_filters[col] = (enabled, low.get(), high.get())
            if enabled:
                enabled_filter_keys.append(col)

        results = apply_filters(results, compiled_filters)

        lang_filtered = False
        if self.language_var.get() != "(Any)":
            results = results[results["language_code"] == self.language_var.get()]
            lang_filtered = True

        results = dynamic_sort(results, enabled_filter_keys, lang_filtered)

        # show updated table
        self.tree.delete(*self.tree.get_children())

        for _, r in results.head(300).iterrows():
            self.tree.insert("", tk.END, values=(
                r["bookID"], r["title"], r["authors"], r["average_rating"],
                r["isbn"], r["language_code"],
                r["num_pages"], r["ratings_count"], r["text_reviews_count"],
                r["publication_date"], r["publisher"]
            ))


# ===========================================================
# RUN APP
# ===========================================================
root = tk.Tk()
app = BookApp(root)
root.mainloop()
