"""
Added Feature Update:
--------------------------------------------------
✔ Each filter now includes an ON/OFF (Radio Button).
✔ Only active filters are used for dataset filtering.
✔ Sorting priority still follows same logic when any filter is active.
"""


import pandas as pd
from rapidfuzz import fuzz
import tkinter as tk
from tkinter import ttk


# ================================
# Load dataset
# ================================
try:
	df = pd.read_csv(r"E:동건\가천대\2025-2\알고리즘\Project\books.csv")
except FileNotFoundError:
    raise SystemExit("ERROR: books.csv not found!")

numeric_fields = ["average_rating", "num_pages", "ratings_count", "text_reviews_count"]
for col in numeric_fields:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df["publication_year"] = pd.to_datetime(df["publication_date"], errors="coerce").dt.year



# ================================
# Sorting logic (Timsort)
# ================================
def sort_with_priority(data, filters_used):
    if not filters_used:
        return data.sort_values(by="bookID")

    priority = [
        "num_pages", "publication_year", "language_code",
        "average_rating", "ratings_count", "text_reviews_count"
    ]

    valid_keys = [p for p in priority if p in data.columns]
    return data.sort_values(by=valid_keys, ascending=False)



# ================================
# NLP Searching
# ================================
def fuzzy_search(query, data):
    if not query:
        return data

    text_fields = ["title", "authors", "publisher"]

    def score(row):
        return max(fuzz.token_set_ratio(query.lower(), str(row[c]).lower()) for c in text_fields)

    data["similarity"] = data.apply(score, axis=1)

    return data[data["similarity"] >= 60].sort_values(by="similarity", ascending=False)



# ================================
# Filter Logic
# ================================
def apply_filters(data, filters):
    filtered = data.copy()

    for col, filter_data in filters.items():
        enabled, low, high = filter_data
        if enabled:
            filtered = filtered[(filtered[col] >= low) & (filtered[col] <= high)]

    return filtered



# ================================
# GUI CLASS
# ================================
class BookApp:

    def __init__(self, root):
        self.root = root
        root.title("📚 Book Search System (With Filter Switches)")
        root.geometry("1100x700")

        tk.Label(root, text="Search Title / Author / Publisher:", font=("Arial", 11)).pack(pady=5)
        self.search_entry = tk.Entry(root, width=60)
        self.search_entry.pack()

        # === Filter Section ===
        filter_frame = tk.Frame(root)
        filter_frame.pack(pady=10)

        self.filter_settings = {}

        def create_filter_row(label, col_name, min_val, max_val):
            row = tk.Frame(filter_frame)
            row.pack(anchor="w", pady=3)

            tk.Label(row, text=f"{label}").pack(side="left")

            status_var = tk.IntVar(value=0)  # Default OFF (0 = disabled, 1 = enabled)
            tk.Radiobutton(row, text="Off", variable=status_var, value=0).pack(side="left")
            tk.Radiobutton(row, text="On", variable=status_var, value=1).pack(side="left")

            # Range sliders
            min_var = tk.DoubleVar(value=min_val)
            max_var = tk.DoubleVar(value=max_val)

            ttk.Scale(row, from_=min_val, to=max_val, variable=min_var).pack(side="left", padx=5)
            ttk.Scale(row, from_=min_val, to=max_val, variable=max_var).pack(side="left", padx=5)

            self.filter_settings[col_name] = (status_var, min_var, max_var)

        create_filter_row("Avg Rating", "average_rating", 0, 5)
        create_filter_row("Num Pages", "num_pages", 0, 2000)
        create_filter_row("Ratings Count", "ratings_count", 0, 1_000_000)
        create_filter_row("Text Review Count", "text_reviews_count", 0, 50_000)
        create_filter_row("Publication Year", "publication_year", 1900, 2025)

        # Language Filter
        tk.Label(root, text="Language:", font=("Arial", 10)).pack()
        self.language_var = tk.StringVar(value="(Any)")
        language_options = ["(Any)"] + sorted(df["language_code"].dropna().unique())
        ttk.Combobox(root, textvariable=self.language_var, values=language_options).pack()

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

        # NLP fuzzy matching
        results = fuzzy_search(query, results)

        filters_used = False
        compiled_filters = {}

        for col, filter_data in self.filter_settings.items():
            enabled = filter_data[0].get() == 1
            low = filter_data[1].get()
            high = filter_data[2].get()

            if enabled:
                compiled_filters[col] = (True, low, high)
                filters_used = True
            else:
                compiled_filters[col] = (False, low, high)

        # Apply filters
        results = apply_filters(results, compiled_filters)

        # Language filter
        if self.language_var.get() != "(Any)":
            results = results[results["language_code"] == self.language_var.get()]
            filters_used = True

        # Sorting rule
        results = sort_with_priority(results, filters_used)

        # Display
        self.tree.delete(*self.tree.get_children())
        for _, r in results.head(200).iterrows():
            self.tree.insert("", tk.END, values=(r["bookID"], r["title"], r["authors"], r["average_rating"]))



# ================================
# Run GUI
# ================================
root = tk.Tk()
app = BookApp(root)
root.mainloop()
