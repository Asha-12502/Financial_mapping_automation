import tkinter as tk
from tkinter import ttk, filedialog
from tkinter.messagebox import showinfo, showerror
import os

class FinancialStatementUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Financial Statement Extractor")
        self.root.geometry("600x500")
        self.root.configure(padx=20, pady=20)

        # Variables to store file paths and page numbers
        self.pdf_file_path = tk.StringVar()
        self.income_page = tk.StringVar(value="")
        self.balance_page = tk.StringVar(value="")
        self.cash_flow_page = tk.StringVar(value="")

        self.create_widgets()

    def create_widgets(self):
        # File Selection Section
        file_frame = ttk.LabelFrame(self.root, text="File Selection", padding=10)
        file_frame.pack(fill="x", pady=(0, 20))

        # PDF File Selection
        pdf_frame = ttk.Frame(file_frame)
        pdf_frame.pack(fill="x", pady=5)
        
        ttk.Label(pdf_frame, text="PDF File:").pack(side="left", padx=(0, 10))
        ttk.Entry(pdf_frame, textvariable=self.pdf_file_path, state="readonly").pack(side="left", fill="x", expand=True)
        ttk.Button(pdf_frame, text="Browse", command=self.select_pdf).pack(side="right", padx=(10, 0))

        # Statement Section
        statement_frame = ttk.LabelFrame(self.root, text="Statement Details", padding=10)
        statement_frame.pack(fill="x", pady=(0, 20))

        # Income Statement
        income_frame = ttk.Frame(statement_frame)
        income_frame.pack(fill="x", pady=5)
        ttk.Label(income_frame, text="Income Statement").pack(side="left")
        ttk.Label(income_frame, text="Page:").pack(side="left", padx=(20, 5))
        ttk.Entry(income_frame, textvariable=self.income_page, width=10).pack(side="left")

        # Balance Sheet
        balance_frame = ttk.Frame(statement_frame)
        balance_frame.pack(fill="x", pady=5)
        ttk.Label(balance_frame, text="Balance Sheet").pack(side="left")
        ttk.Label(balance_frame, text="Page:").pack(side="left", padx=(20, 5))
        ttk.Entry(balance_frame, textvariable=self.balance_page, width=10).pack(side="left")

        # Cash Flow
        cash_frame = ttk.Frame(statement_frame)
        cash_frame.pack(fill="x", pady=5)
        ttk.Label(cash_frame, text="Cash Flow").pack(side="left")
        ttk.Label(cash_frame, text="Page:").pack(side="left", padx=(20, 5))
        ttk.Entry(cash_frame, textvariable=self.cash_flow_page, width=10).pack(side="left")

        # Download Button
        ttk.Button(
            self.root, 
            text="Download Excel File",
            command=self.process_and_download,
            style="Accent.TButton"
        ).pack(pady=20)

        # Configure style for accent button
        style = ttk.Style()
        style.configure("Accent.TButton", font=("Arial", 11, "bold"))

    def select_pdf(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if file_path:
            self.pdf_file_path.set(file_path)

    def process_and_download(self):
        # Validate inputs
        if not self.pdf_file_path.get():
            showerror("Error", "Please select a PDF file first!")
            return

        if not all([self.income_page.get(), self.balance_page.get(), self.cash_flow_page.get()]):
            showerror("Error", "Please enter all page numbers!")
            return

        try:
            # Here you would call your existing backend processing code
            # For example:
            # process_financial_statements(
            #     self.pdf_file_path.get(),
            #     {
            #         'income_statement': int(self.income_page.get()) - 1,
            #         'balance_sheet': int(self.balance_page.get()) - 1,
            #         'cash_flow': int(self.cash_flow_page.get()) - 1
            #     }
            # )
            
            showinfo("Success", "Excel file has been created successfully!")
        except Exception as e:
            showerror("Error", f"An error occurred: {str(e)}")

def main():
    root = tk.Tk()
    app = FinancialStatementUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()