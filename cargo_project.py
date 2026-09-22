import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import json
import os
import hashlib
import copy # For deep copying data states for undo/redo

# --- User Account Management ---
class UserAccountManager:
    def __init__(self, users_file="users.json"):
        self.users_file = users_file
        self.users = self._load_users()

    def _load_users(self):
        """Loads user data from the JSON file."""
        if os.path.exists(self.users_file):
            with open(self.users_file, 'r', encoding='utf-8') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    # If file is empty or corrupted JSON, start with an empty dictionary
                    return {}
        return {}

    def _save_users(self):
        """Saves current user data to the JSON file."""
        with open(self.users_file, 'w', encoding='utf-8') as f:
            json.dump(self.users, f, indent=4)

    def hash_password(self, password):
        """Hashes the password using SHA256. For production, use bcrypt or scrypt."""
        return hashlib.sha256(password.encode()).hexdigest()

    def register_user(self, login_id, password, registered_no, email, name, phone_no):
        """
        Registers a new user.
        Returns (True, message) on success, (False, error_message) on failure.
        """
        if login_id in self.users:
            return False, "Login ID already exists."

        # Basic validation for email and phone number format (can be enhanced)
        if "@" not in email or "." not in email:
            return False, "Invalid email format."
        if not phone_no.isdigit() or len(phone_no) < 7: # Simple digit check
            return False, "Invalid phone number format."

        hashed_password = self.hash_password(password)
        self.users[login_id] = {
            "password": hashed_password,
            "registered_no": registered_no,
            "email": email,
            "name": name,
            "phone_no": phone_no
        }
        self._save_users()
        return True, "Registration successful! You can now log in."

    def authenticate_user(self, login_id, password):
        """
        Authenticates a user.
        Returns (True, user_data) on success, (False, None) on failure.
        """
        user_data = self.users.get(login_id)
        if user_data and user_data["password"] == self.hash_password(password):
            return True, user_data
        return False, None

# --- Main Application Classes for GUI Pages ---

class LoginPage:
    def __init__(self, master, app_instance, user_manager):
        self.master = master
        self.app_instance = app_instance # Reference to the main application manager
        self.user_manager = user_manager

        self.login_frame = ttk.Frame(master, padding="30")
        self.login_frame.pack(expand=True, fill=tk.BOTH)

        self.login_id = tk.StringVar()
        self.password = tk.StringVar()

        self.setup_login_ui()

    def setup_login_ui(self):
        """Sets up the widgets for the login page."""
        # Clear existing widgets from the frame
        for widget in self.login_frame.winfo_children():
            widget.destroy()

        title_label = ttk.Label(self.login_frame, text="Login", font=('Inter', 18, 'bold'))
        title_label.pack(pady=20)

        form_frame = ttk.Frame(self.login_frame)
        form_frame.pack(pady=10)

        ttk.Label(form_frame, text="Login ID:").grid(row=0, column=0, pady=5, sticky="w")
        self.login_id_entry = ttk.Entry(form_frame, textvariable=self.login_id, width=30)
        self.login_id_entry.grid(row=0, column=1, pady=5, padx=5)
        self.login_id_entry.focus_set()

        ttk.Label(form_frame, text="Password:").grid(row=1, column=0, pady=5, sticky="w")
        self.password_entry = ttk.Entry(form_frame, textvariable=self.password, show="*")
        self.password_entry.grid(row=1, column=1, pady=5, padx=5)
        self.password_entry.bind("<Return>", lambda e: self.check_login()) # Bind Enter key to login

        login_button = ttk.Button(self.login_frame, text="Login", command=self.check_login, style='Blue.TButton')
        login_button.pack(pady=10)

        forgot_password_button = ttk.Button(self.login_frame, text="Forgot Password?", command=self.show_forgot_password, style='TButton')
        forgot_password_button.pack(pady=5)

        signup_button = ttk.Button(self.login_frame, text="Don't have an account? Sign Up", command=self.show_signup, style='TButton')
        signup_button.pack(pady=5)

    def check_login(self):
        """Authenticates the user based on provided credentials."""
        login_id = self.login_id.get().strip()
        password = self.password.get().strip()

        if not login_id or not password:
            messagebox.showwarning("Login Failed", "Please enter both Login ID and Password.")
            return

        success, user_data = self.user_manager.authenticate_user(login_id, password)
        if success:
            messagebox.showinfo("Login Success", f"Welcome, {user_data.get('name', login_id)}!")
            self.login_frame.pack_forget() # Hide login frame
            self.app_instance.show_dashboard(user_data) # Show dashboard with user data
        else:
            messagebox.showerror("Login Failed", "Invalid Login ID or Password.")
            self.password.set("") # Clear password field for security

    def show_forgot_password(self):
        """Displays a placeholder message for forgotten password."""
        messagebox.showinfo("Forgot Password", "Please contact support to reset your password.")

    def show_signup(self):
        """Switches the view to the sign-up page."""
        self.login_frame.pack_forget() # Hide login frame
        self.app_instance.show_signup_page()


class SignUpPage:
    def __init__(self, master, app_instance, user_manager):
        self.master = master
        self.app_instance = app_instance
        self.user_manager = user_manager

        self.signup_frame = ttk.Frame(master, padding="30")
        self.signup_frame.pack(expand=True, fill=tk.BOTH)

        self.login_id = tk.StringVar()
        self.registered_no = tk.StringVar()
        self.email = tk.StringVar()
        self.name = tk.StringVar()
        self.phone_no = tk.StringVar()
        self.create_password = tk.StringVar()
        self.confirm_password = tk.StringVar()
        self.show_password_var = tk.BooleanVar(value=False)

        self.setup_signup_ui()

    def setup_signup_ui(self):
        """Sets up the widgets for the sign-up page."""
        # Clear existing widgets from the frame
        for widget in self.signup_frame.winfo_children():
            widget.destroy()

        title_label = ttk.Label(self.signup_frame, text="Sign Up", font=('Inter', 18, 'bold'))
        title_label.pack(pady=10)

        form_frame = ttk.Frame(self.signup_frame)
        form_frame.pack(pady=10)

        # Labels and Entry fields for registration details
        labels_and_vars = {
            "Login ID:": self.login_id,
            "Registered No.:": self.registered_no,
            "Email:": self.email,
            "Name:": self.name,
            "Phone No.:": self.phone_no,
            "Create Password:": self.create_password,
            "Confirm Password:": self.confirm_password
        }
        
        self.entries = {} # Store references to entry widgets for password visibility toggle
        for i, (label_text, var) in enumerate(labels_and_vars.items()):
            ttk.Label(form_frame, text=label_text).grid(row=i, column=0, pady=5, sticky="w")
            entry = ttk.Entry(form_frame, textvariable=var, width=35)
            entry.grid(row=i, column=1, pady=5, padx=5)
            self.entries[label_text] = entry # Store reference

        # Configure password entries to hide characters initially
        self.entries["Create Password:"].config(show="*")
        self.entries["Confirm Password:"].config(show="*")

        # Checkbox to show/hide passwords
        show_password_checkbox = ttk.Checkbutton(
            form_frame, text="Show Password", variable=self.show_password_var,
            command=self.toggle_password_visibility
        )
        show_password_checkbox.grid(row=len(labels_and_vars), column=1, columnspan=1, sticky="w", pady=5)

        signup_button = ttk.Button(self.signup_frame, text="Sign Up", command=self.register_user, style='Blue.TButton')
        signup_button.pack(pady=15)

        back_to_login_button = ttk.Button(self.signup_frame, text="Back to Login", command=self.app_instance.show_login_page, style='TButton')
        back_to_login_button.pack(pady=5)

    def toggle_password_visibility(self):
        """Toggles the visibility of password characters."""
        if self.show_password_var.get():
            self.entries["Create Password:"].config(show="")
            self.entries["Confirm Password:"].config(show="")
        else:
            self.entries["Create Password:"].config(show="*")
            self.entries["Confirm Password:"].config(show="*")

    def register_user(self):
        """Handles user registration, validation, and saving data."""
        login_id = self.login_id.get().strip()
        registered_no = self.registered_no.get().strip()
        email = self.email.get().strip()
        name = self.name.get().strip()
        phone_no = self.phone_no.get().strip()
        create_password = self.create_password.get().strip()
        confirm_password = self.confirm_password.get().strip()

        # Basic validation
        if not all([login_id, registered_no, email, name, phone_no, create_password, confirm_password]):
            messagebox.showwarning("Registration Failed", "All fields are required.")
            return
        
        if create_password != confirm_password:
            messagebox.showwarning("Registration Failed", "Passwords do not match.")
            return

        if len(create_password) < 6:
            messagebox.showwarning("Registration Failed", "Password must be at least 6 characters long.")
            return

        # Attempt to register user via UserAccountManager
        success, message = self.user_manager.register_user(login_id, create_password, registered_no, email, name, phone_no)
        
        if success:
            messagebox.showinfo("Registration Success", message)
            self.signup_frame.pack_forget() # Hide signup frame
            self.app_instance.show_login_page() # Go back to login page
        else:
            messagebox.showerror("Registration Failed", message)


class DashboardPage:
    def __init__(self, master, app_instance, user_data):
        self.master = master
        self.app_instance = app_instance
        self.user_data = user_data # User data for the logged-in user

        self.dashboard_frame = ttk.Frame(master, padding="30")
        self.dashboard_frame.pack(expand=True, fill=tk.BOTH)

        self.setup_dashboard_ui()

    def setup_dashboard_ui(self):
        """Sets up the widgets for the dashboard page."""
        # Clear existing widgets from the frame
        for widget in self.dashboard_frame.winfo_children():
            widget.destroy()

        title_label = ttk.Label(self.dashboard_frame, text="Dashboard", font=('Inter', 20, 'bold'))
        title_label.pack(pady=20)

        details_frame = ttk.LabelFrame(self.dashboard_frame, text="Your Profile Details", padding="15")
        details_frame.pack(pady=20, padx=50, fill=tk.X, expand=True)

        # Display user details dynamically
        row_idx = 0
        for key, value in self.user_data.items():
            if key == "password": continue # Do not display hashed password
            
            display_key = key.replace("_", " ").title() # Format key for display
            ttk.Label(details_frame, text=f"{display_key}:", font=('Inter', 11, 'bold')).grid(row=row_idx, column=0, sticky="w", pady=2)
            ttk.Label(details_frame, text=value, font=('Inter', 11)).grid(row=row_idx, column=1, sticky="w", pady=2)
            row_idx += 1

        # Buttons at the bottom
        button_frame = ttk.Frame(self.dashboard_frame, padding="10")
        button_frame.pack(pady=20)

        # Using Unicode characters as icons for simplicity and self-containment
        excel_icon = "📊" # Spreadsheet icon
        report_icon = "📈" # Chart/report icon

        excel_button = ttk.Button(button_frame, text=f"{excel_icon} Excel Sheet", command=self.open_excel_sheet, style='Blue.TButton')
        excel_button.pack(side=tk.LEFT, padx=10)

        report_button = ttk.Button(button_frame, text=f"{report_icon} Report", command=self.generate_report, style='Blue.TButton')
        report_button.pack(side=tk.LEFT, padx=10)

        logout_button = ttk.Button(button_frame, text="Logout", command=self.app_instance.show_login_page, style='TButton')
        logout_button.pack(side=tk.RIGHT, padx=10)

    def open_excel_sheet(self):
        """Hides dashboard and launches the SheetEditorApp."""
        messagebox.showinfo("Excel Sheet", "Opening Excel Sheet Editor...")
        self.dashboard_frame.pack_forget() # Hide dashboard frame
        self.app_instance.show_sheet_editor()

    def generate_report(self):
        """Placeholder for report generation functionality."""
        messagebox.showinfo("Report", "Generating Report (Placeholder)...")
        # Add actual report generation logic here


class MainApplication:
    """
    Manages the overall application flow and switches between different GUI pages.
    """
    def __init__(self, root):
        self.root = root
        self.root.title("Application")
        self.root.geometry("1000x700") # Initial window size for main app
        self.root.minsize(800, 600)
        self.root.withdraw() # Hide main root window until login is successful

        self.user_manager = UserAccountManager()

        self.current_page_instance = None # To keep track of the active page object (LoginPage, SignUpPage, DashboardPage)

        # Initialize the login page as the starting point
        self.show_login_page()

    def show_login_page(self):
        """Displays the login page."""
        self._clear_current_page()
        self.root.deiconify() # Ensure root window is visible
        self.current_page_instance = LoginPage(self.root, self, self.user_manager)
        # LoginPage's constructor automatically packs its frame.
        self.root.title("Login")

    def show_signup_page(self):
        """Displays the sign-up page."""
        self._clear_current_page()
        self.root.deiconify() # Ensure root window is visible
        self.current_page_instance = SignUpPage(self.root, self, self.user_manager)
        # SignUpPage's constructor automatically packs its frame.
        self.root.title("Sign Up")

    def show_dashboard(self, user_data):
        """Displays the dashboard page after successful login."""
        self._clear_current_page()
        self.root.deiconify() # Ensure root window is visible
        self.current_page_instance = DashboardPage(self.root, self, user_data)
        # DashboardPage's constructor automatically packs its frame.
        self.root.title("Dashboard")

    def show_sheet_editor(self):
        """Launches the SheetEditorApp."""
        self._clear_current_page()
        self.root.title("Python Sheet Editor")
        # Instantiate SheetEditorApp directly using the main root window
        self.sheet_editor_instance = SheetEditorApp(self.root)
        self.root.deiconify() # Ensure main window is visible

    def _clear_current_page(self):
        """Destroys the widgets of the currently displayed page."""
        if self.current_page_instance and hasattr(self.current_page_instance, 'login_frame'):
            self.current_page_instance.login_frame.destroy()
        elif self.current_page_instance and hasattr(self.current_page_instance, 'signup_frame'):
            self.current_page_instance.signup_frame.destroy()
        elif self.current_page_instance and hasattr(self.current_page_instance, 'dashboard_frame'):
            self.current_page_instance.dashboard_frame.destroy()
        
        # If SheetEditorApp is active, its widgets are directly packed into root,
        # so we need to destroy all children of root.
        # This is handled by SheetEditorApp.setup_ui() itself when it's called.
        # So, no explicit destroy for SheetEditorApp here.
        # Setting current_page_instance to None helps in managing references.
        self.current_page_instance = None


# --- Your Existing SheetEditorApp Class (INTEGRATED AND SLIGHTLY ADAPTED) ---
class SheetEditorApp:
    def __init__(self, root):
        self.root = root
        # No need to set root title/geometry/minisize here, MainApplication handles it.
        # self.root.title("Python Sheet Editor")
        # self.root.geometry("1000x700")
        # self.root.minsize(800, 600)

        self.ROWS = 10
        self.COLS = 6
        self.current_sheet_name = "My New Sheet"
        self.data = [] # Stores current sheet data (including header)
        self.original_data = [] # Stores original data for filter reset (excluding header)
        self.saved_sheets_dir = "sheets" # Directory to store saved sheets

        # Undo/Redo history
        self.history = []
        self.history_index = -1
        self.max_history_states = 50 # Limit history states to prevent excessive memory usage

        # Filter dialog instance management
        self.filter_dialog_instance = None
        self._current_filter_col_index = -1 # To keep track of the column being filtered in the dialog

        # Ensure the sheets directory exists
        if not os.path.exists(self.saved_sheets_dir):
            os.makedirs(self.saved_sheets_dir)

        self.setup_ui()
        self.create_sheet()
        self.load_sheet_list()
        self._save_current_state() # Save initial state to history

    def setup_ui(self):
        """Sets up the Sheet Editor's main UI components."""
        # --- IMPORTANT: Clear all existing widgets from the root window ---
        # This ensures that when the SheetEditorApp is shown, it replaces
        # any widgets from previous pages (Login, Signup, Dashboard).
        for widget in self.root.winfo_children():
            widget.destroy()

        # Configure styles for a modern look
        style = ttk.Style()
        style.theme_use("clam") # 'clam', 'alt', 'default', 'classic'
        style.configure('TButton', font=('Inter', 10), padding=8, relief="raised",
                        background='#4CAF50', foreground='white')
        style.map('TButton', background=[('active', '#45a049')])

        style.configure('Blue.TButton', background='#007bff', foreground='white')
        style.map('Blue.TButton', background=[('active', '#0056b3')])

        style.configure('TEntry', font=('Inter', 11), padding=5)
        style.configure('TCombobox', font=('Inter', 11), padding=5)
        style.configure('TLabel', font=('Inter', 11))
        style.configure('Treeview.Heading', font=('Inter', 11, 'bold'), background='#f0f0f0', foreground='#555')
        style.configure('Treeview', font=('Inter', 10), rowheight=25, background='white', fieldbackground='white')
        style.map('Treeview', background=[('selected', '#a0c8f0')]) # Highlight selected row

        # --- STYLES FOR ALTERNATING ROWS ---
        style.configure("Treeview.Oddrow", background="#f8f8f8") # Light grey for odd rows
        style.configure("Treeview.Evenrow", background="#ffffff") # White for even rows
        # --- END ALTERNATING STYLES ---


        # --- Top Control Frame ---
        top_frame = ttk.Frame(self.root, padding="10")
        top_frame.pack(fill=tk.X)

        ttk.Label(top_frame, text="Sheet Name:").pack(side=tk.LEFT, padx=5)
        self.sheet_name_entry = ttk.Entry(top_frame, textvariable=tk.StringVar(value=self.current_sheet_name), width=30)
        self.sheet_name_entry.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        self.new_sheet_button = ttk.Button(top_frame, text="New Sheet", command=self.new_sheet)
        self.new_sheet_button.pack(side=tk.LEFT, padx=5)

        self.import_csv_button = ttk.Button(top_frame, text="Import CSV", command=self.import_sheet)
        self.import_csv_button.pack(side=tk.LEFT, padx=5)

        # --- Row/Column Controls Frame ---
        controls_frame = ttk.Frame(self.root, padding="10", relief="groove", borderwidth=2)
        controls_frame.pack(fill=tk.X, pady=10)

        # Row controls
        row_control_frame = ttk.Frame(controls_frame)
        row_control_frame.pack(side=tk.LEFT, padx=20)
        ttk.Button(row_control_frame, text="+", command=self.add_row, style='Blue.TButton', width=3).pack(side=tk.LEFT)
        ttk.Label(row_control_frame, text="Row").pack(side=tk.LEFT, padx=5)
        ttk.Button(row_control_frame, text="-", command=self.remove_row, style='Blue.TButton', width=3).pack(side=tk.LEFT)

        # Column controls
        col_control_frame = ttk.Frame(controls_frame)
        col_control_frame.pack(side=tk.LEFT, padx=20)
        ttk.Button(col_control_frame, text="+", command=self.add_column, style='Blue.TButton', width=3).pack(side=tk.LEFT)
        ttk.Label(col_control_frame, text="Column").pack(side=tk.LEFT, padx=5)
        ttk.Button(col_control_frame, text="-", command=self.remove_column, style='Blue.TButton', width=3).pack(side=tk.LEFT)

        # Undo/Redo buttons
        undo_redo_frame = ttk.Frame(controls_frame)
        undo_redo_frame.pack(side=tk.LEFT, padx=20)
        self.undo_button = ttk.Button(undo_redo_frame, text="Undo", command=self.undo, style='Blue.TButton')
        self.undo_button.pack(side=tk.LEFT, padx=5)
        self.redo_button = ttk.Button(undo_redo_frame, text="Redo", command=self.redo, style='Blue.TButton')
        self.redo_button.pack(side=tk.LEFT, padx=5)


        # --- Table Display Frame ---
        table_frame = ttk.Frame(self.root, padding="10")
        table_frame.pack(fill=tk.BOTH, expand=True)

        # Use "headings" only. "lines" is causing TclError in your environment.
        self.tree = ttk.Treeview(table_frame, show="headings")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbars for the table
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=vsb.set)

        hsb = ttk.Scrollbar(self.root, orient="horizontal", command=self.tree.xview)
        hsb.pack(fill=tk.X)
        self.tree.configure(xscrollcommand=hsb.set)

        # Bind events for cell editing and column sorting
        self.tree.bind("<Double-1>", self.on_cell_double_click)
        self.tree.bind("<ButtonRelease-1>", self.on_cell_select) # For selection after double-click
        self.tree.bind("<Return>", self.on_enter_pressed) # For finishing edit with Enter
        self.tree.bind("<Button-3>", self.on_heading_right_click) # Right-click for column actions (now opens filter dialog)

        # --- Bottom Control Frame ---
        bottom_frame = ttk.Frame(self.root, padding="10")
        bottom_frame.pack(fill=tk.X, pady=10)

        self.save_button = ttk.Button(bottom_frame, text="Save", command=self.save_sheet)
        self.save_button.pack(side=tk.LEFT, padx=5)

        self.export_csv_button = ttk.Button(bottom_frame, text="Export CSV", command=self.export_sheet)
        self.export_csv_button.pack(side=tk.LEFT, padx=5)

        self.print_button = ttk.Button(bottom_frame, text="Print", command=self.print_sheet)
        self.print_button.pack(side=tk.LEFT, padx=5)

        self.clear_filters_button = ttk.Button(bottom_frame, text="Clear All Filters", command=lambda: self.reset_filters_and_show_all(restore_order=True))
        self.clear_filters_button.pack(side=tk.LEFT, padx=5)

        # --- Sheet List and Load/Delete Frame ---
        sheet_manage_frame = ttk.Frame(self.root, padding="10")
        sheet_manage_frame.pack(fill=tk.X)

        ttk.Label(sheet_manage_frame, text="Saved Sheets:").pack(side=tk.LEFT, padx=5)
        self.sheet_list_combo = ttk.Combobox(sheet_manage_frame, state="readonly", width=25)
        self.sheet_list_combo.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        self.sheet_list_combo.bind("<<ComboboxSelected>>", self.on_sheet_selected)

        self.load_button = ttk.Button(sheet_manage_frame, text="Load", command=self.load_sheet)
        self.load_button.pack(side=tk.LEFT, padx=5)

        self.delete_button = ttk.Button(sheet_manage_frame, text="Delete", command=self.delete_sheet)
        self.delete_button.pack(side=tk.LEFT, padx=5)

        # Entry for cell editing
        self.edit_entry = ttk.Entry(self.root)
        self.edit_entry.bind("<FocusOut>", self.on_edit_focus_out)
        self.edit_entry.bind("<Return>", self.on_enter_pressed)
        self.edit_entry_active = False # Flag to track if edit_entry is active

        self._update_undo_redo_buttons() # Initial state of undo/redo buttons

    def create_sheet(self, initial_data=None, save_to_history=True):
        """
        Creates or recreates the sheet table with specified dimensions and data.
        If initial_data is None, an empty sheet with default dimensions is created.
        """
        # Clear existing data and remove any previous tags
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Determine dimensions from initial_data if provided
        if initial_data:
            # Ensure all rows have the same number of columns as the header for consistency
            max_cols = max(len(row) for row in initial_data) if initial_data else 0
            self.data = [row + [""] * (max_cols - len(row)) for row in initial_data]
            self.ROWS = len(self.data) - 1 # Number of data rows (excluding header)
            self.COLS = max_cols if max_cols > 0 else 1 # Ensure at least one column
        else:
            # Create default empty data with header
            self.data = []
            self.data.append([f"Attribute {j + 1}" for j in range(self.COLS)]) # Header row
            for i in range(self.ROWS):
                row_values = [""] * self.COLS
                self.data.append(row_values)

        # Configure Treeview columns based on new COLS
        self.tree["columns"] = [f"col{j}" for j in range(self.COLS)]
        
        # Set new column headings and properties
        for j in range(self.COLS):
            header_text = self.data[0][j] if j < len(self.data[0]) else f"Attribute {j + 1}"
            self.tree.heading(f"col{j}", text=header_text, anchor=tk.W,
                              command=lambda c=j: self.sort_column(c)) # Make headers clickable for sorting
            self.tree.column(f"col{j}", width=120, minwidth=80, stretch=False) # Default column width

        # Insert data rows (skip the first row which is the header)
        for i, row_data in enumerate(self.data[1:]):
            # Apply alternating row tags for visual separation
            tag = "Treeview.Evenrow" if (i % 2 == 0) else "Treeview.Oddrow"
            self.tree.insert("", "end", values=row_data, tags=(tag,))

        self.update_original_data() # Store initial/loaded state as original
        if save_to_history:
            self._save_current_state()

    def get_current_table_data(self):
        """Retrieves all data from the Treeview, including the header."""
        data = []
        # Get header data from Treeview headings
        header_data = [self.tree.heading(col_id, 'text') for col_id in self.tree["columns"]]
        data.append(header_data)

        # Get row data
        for iid in self.tree.get_children():
            data.append(list(self.tree.item(iid, 'values')))
        return data

    def update_original_data(self):
        """Updates the stored original data from the current sheet, excluding the header."""
        # This is used for filter reset to bring back the original data rows
        current_data = self.get_current_table_data()
        self.original_data = copy.deepcopy(current_data[1:]) if len(current_data) > 1 else []


    def _save_current_state(self):
        """Saves the current sheet state to the history stack."""
        current_state = copy.deepcopy(self.get_current_table_data())

        # If we're not at the end of history (i.e., we've undone some actions),
        # clear future history from the current point
        if self.history_index < len(self.history) - 1:
            self.history = self.history[:self.history_index + 1]

        self.history.append(current_state)
        self.history_index = len(self.history) - 1

        # Trim history if it exceeds max_history_states
        if len(self.history) > self.max_history_states:
            self.history.pop(0)
            self.history_index -= 1

        self._update_undo_redo_buttons()

    def _load_state(self, state_data):
        """Loads a given state from history into the sheet."""
        self.create_sheet(initial_data=state_data, save_to_history=False)
        self.update_original_data() # Update original_data as well

    def undo(self):
        """Undoes the last action by loading the previous state from history."""
        if self.history_index > 0:
            self.history_index -= 1
            self._load_state(self.history[self.history_index])
            self._update_undo_redo_buttons()
        else:
            messagebox.showinfo("Undo", "No more actions to undo.")

    def redo(self):
        """Redoes the last undone action by loading the next state from history."""
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self._load_state(self.history[self.history_index])
            self._update_undo_redo_buttons()
        else:
            messagebox.showinfo("Redo", "No more actions to redo.")

    def _update_undo_redo_buttons(self):
        """Updates the state of undo and redo buttons."""
        self.undo_button.config(state=tk.NORMAL if self.history_index > 0 else tk.DISABLED)
        self.redo_button.config(state=tk.NORMAL if self.history_index < len(self.history) - 1 else tk.DISABLED)

    def add_row(self):
        self.ROWS += 1
        new_row_values = [""] * self.COLS
        self.data.append(new_row_values)
        # Apply tag based on the new total number of data rows
        tag = "Treeview.Evenrow" if ((len(self.data) - 1) % 2 == 0) else "Treeview.Oddrow"
        self.tree.insert("", "end", values=new_row_values, tags=(tag,))
        self.update_original_data()
        self._save_current_state() # Save state after adding row

    def remove_row(self):
        # Allow removing the last data row but not the header
        if self.ROWS <= 0:
            messagebox.showinfo("Cannot Remove Row", "No data rows to remove.")
            return

        selected_item = self.tree.focus()
        if selected_item:
            # Get the actual index in the Treeview's display
            row_index_in_tree = self.tree.index(selected_item)
            self.tree.delete(selected_item)
            # Remove from self.data (account for header offset, so row_index_in_tree + 1)
            self.data.pop(row_index_in_tree + 1)
        else:
            # If no row is selected, remove the last data row
            last_item = self.tree.get_children()[-1] if self.tree.get_children() else None
            if last_item:
                self.tree.delete(last_item)
                self.data.pop(-1) # Remove last element from data
            else:
                messagebox.showinfo("Cannot Remove Row", "No rows available to remove.")
                return # Exit if nothing to remove

        self.ROWS = len(self.data) - 1 # Update ROWS count, excluding header
        
        # After removing a row, the row colors might need re-applying
        self._reapply_row_tags()

        self.update_original_data()
        self._save_current_state() # Save state after removing row

    def add_column(self):
        self.COLS += 1
        new_col_name = f"Attribute {self.COLS}"
        
        # Update Treeview columns
        current_columns = list(self.tree["columns"])
        current_columns.append(f"col{self.COLS-1}")
        self.tree["columns"] = current_columns
        
        self.tree.heading(f"col{self.COLS-1}", text=new_col_name, anchor=tk.W,
                          command=lambda c=self.COLS-1: self.sort_column(c))
        self.tree.column(f"col{self.COLS-1}", width=120, minwidth=80, stretch=False)

        # Update self.data: add new column to header and all data rows
        if self.data:
            self.data[0].append(new_col_name) # Add to header
            for i in range(1, len(self.data)):
                self.data[i].append("") # Add empty string to data rows

        # Update Treeview rows to reflect new column (re-insert all rows)
        self.refresh_treeview_from_data()

        self.update_original_data()
        self._save_current_state() # Save state after adding column

    def remove_column(self):
        if self.COLS <= 1:
            messagebox.showinfo("Cannot Remove Column", "Sheet must have at least one column.")
            return

        response = messagebox.askyesno("Remove Column",
                                       "Do you want to remove the last column? This action cannot be undone by redo button after save")
        if not response:
            return

        self.COLS -= 1
        
        # Remove from Treeview columns
        current_columns = list(self.tree["columns"])
        last_col_id = current_columns.pop()
        self.tree.forget(last_col_id) # Remove the column from Treeview display
        self.tree["columns"] = current_columns # Update treeview columns

        # Update self.data: remove last column from header and all data rows
        if self.data:
            for row in self.data:
                if row: # Ensure row is not empty
                    row.pop()

        # Update Treeview rows to reflect removed column (re-insert all rows)
        self.refresh_treeview_from_data()

        self.update_original_data()
        self._save_current_state() # Save state after removing column

    def _reapply_row_tags(self):
        """Reapplies alternating row tags after row additions/deletions."""
        for i, item_id in enumerate(self.tree.get_children()):
            tag = "Treeview.Evenrow" if (i % 2 == 0) else "Treeview.Oddrow"
            self.tree.item(item_id, tags=(tag,))

    def on_cell_double_click(self, event):
        """Activates an entry widget for cell editing on double-click."""
        if self.edit_entry_active: # If another entry is active, finalize it first
            self.on_edit_focus_out(None)

        item_id = self.tree.identify_row(event.y)
        column_id = self.tree.identify_column(event.x)

        if not item_id or not column_id:
            return

        # Get column index from Treeview's internal column ID
        col_index = int(column_id.replace('#', '')) - 1

        # Get current value
        current_value = self.tree.item(item_id, 'values')[col_index]

        # Get cell bounding box (x, y, width, height)
        x, y, width, height = self.tree.bbox(item_id, column_id)

        # Position and show the entry widget
        self.edit_entry.place(x=x, y=y, width=width, height=height)
        self.edit_entry.delete(0, tk.END)
        self.edit_entry.insert(0, current_value)
        self.edit_entry.focus_set()
        self.edit_entry.select_range(0, tk.END) # Select all text for easy replacement

        # Store context for saving changes
        self.edit_entry.item_id = item_id
        self.edit_entry.col_index = col_index
        self.edit_entry_active = True

    def on_edit_focus_out(self, event):
        """Saves changes from the edit entry when it loses focus."""
        if not self.edit_entry_active:
            return

        new_value = self.edit_entry.get()
        item_id = self.edit_entry.item_id
        col_index = self.edit_entry.col_index

        current_values = list(self.tree.item(item_id, 'values'))
        
        # Get the actual row index in the self.data list
        # This requires iterating through treeview children to find the position
        all_children = self.tree.get_children()
        row_index_in_tree = all_children.index(item_id)
        
        # Check if the value has actually changed before updating and saving state
        if current_values[col_index] != new_value:
            current_values[col_index] = new_value
            self.tree.item(item_id, values=current_values)
            
            # Update the self.data list (account for header offset)
            if 0 <= row_index_in_tree + 1 < len(self.data):
                if 0 <= col_index < len(self.data[row_index_in_tree + 1]):
                    self.data[row_index_in_tree + 1][col_index] = new_value
            
            self.update_original_data() # Update original data after edit
            self._save_current_state() # Save state after edit

        self.edit_entry.place_forget() # Hide the entry widget
        self.edit_entry_active = False

    def on_enter_pressed(self, event):
        """Finishes cell editing when Enter is pressed."""
        if self.edit_entry_active:
            self.edit_entry.focus_out() # Trigger focus_out to save changes

    def on_cell_select(self, event):
        """Allows selecting a cell after double-click without immediately losing focus."""
        # This ensures the focus remains on the treeview after editing if needed
        # It's primarily here to prevent immediate focus-out when clicking away from entry but still on treeview
        pass

    def new_sheet(self):
        """Creates a new empty sheet."""
        if messagebox.askyesno("New Sheet", "Are you sure you want to create a new sheet? Unsaved data will be lost."):
            self.current_sheet_name = "My New Sheet"
            self.sheet_name_entry.delete(0, tk.END)
            self.sheet_name_entry.insert(0, self.current_sheet_name)
            self.ROWS = 10 # Reset to default rows
            self.COLS = 6  # Reset to default columns
            self.create_sheet()
            self.reset_filters_and_show_all(restore_order=True) # Clear any active filters
            messagebox.showinfo("New Sheet", "New sheet created successfully.")
            self._save_current_state() # Save new sheet state

    def save_sheet(self):
        """Saves the current sheet data to a JSON file."""
        sheet_name = self.sheet_name_entry.get().strip()
        if not sheet_name:
            messagebox.showwarning("Save Sheet", "Please enter a sheet name.")
            return

        filename = os.path.join(self.saved_sheets_dir, f"{sheet_name}.json")
        try:
            current_data = self.get_current_table_data()
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(current_data, f, indent=4)
            messagebox.showinfo("Save Sheet", f"Sheet '{sheet_name}' saved successfully!")
            self.current_sheet_name = sheet_name
            self.load_sheet_list() # Refresh the sheet list
        except Exception as e:
            messagebox.showerror("Save Sheet Error", f"Failed to save sheet: {e}")

    def load_sheet_list(self):
        """Populates the combobox with available saved sheets."""
        sheets = []
        if os.path.exists(self.saved_sheets_dir):
            for filename in os.listdir(self.saved_sheets_dir):
                if filename.endswith(".json"):
                    sheets.append(os.path.splitext(filename)[0])
        self.sheet_list_combo['values'] = sorted(sheets)
        if self.current_sheet_name in sheets:
            self.sheet_list_combo.set(self.current_sheet_name)
        elif sheets:
            self.sheet_list_combo.set(sheets[0]) # Set to first sheet if available

    def on_sheet_selected(self, event):
        """Handles selection of a sheet from the combobox (prepares for loading)."""
        selected_sheet = self.sheet_list_combo.get()
        if selected_sheet:
            self.sheet_name_entry.delete(0, tk.END)
            self.sheet_name_entry.insert(0, selected_sheet)

    def load_sheet(self):
        """Loads the selected sheet from the JSON file."""
        sheet_name = self.sheet_list_combo.get().strip()
        if not sheet_name:
            messagebox.showwarning("Load Sheet", "Please select a sheet to load.")
            return

        if messagebox.askyesno("Load Sheet", "Are you sure you want to load this sheet? Unsaved data will be lost."):
            filename = os.path.join(self.saved_sheets_dir, f"{sheet_name}.json")
            if not os.path.exists(filename):
                messagebox.showerror("Load Sheet Error", f"Sheet file '{sheet_name}.json' not found.")
                return

            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                
                self.current_sheet_name = sheet_name
                self.sheet_name_entry.delete(0, tk.END)
                self.sheet_name_entry.insert(0, self.current_sheet_name)
                
                self.create_sheet(initial_data=loaded_data) # Recreate sheet with loaded data
                self.reset_filters_and_show_all(restore_order=True) # Clear any active filters
                messagebox.showinfo("Load Sheet", f"Sheet '{sheet_name}' loaded successfully!")
                self._save_current_state() # Save loaded state to history
            except Exception as e:
                messagebox.showerror("Load Sheet Error", f"Failed to load sheet: {e}")

    def delete_sheet(self):
        """Deletes the selected sheet file."""
        sheet_name = self.sheet_list_combo.get().strip()
        if not sheet_name:
            messagebox.showwarning("Delete Sheet", "Please select a sheet to delete.")
            return

        if messagebox.askyesno("Delete Sheet", f"Are you sure you want to delete sheet '{sheet_name}'? This cannot be undone."):
            filename = os.path.join(self.saved_sheets_dir, f"{sheet_name}.json")
            if not os.path.exists(filename):
                messagebox.showerror("Delete Sheet Error", f"Sheet file '{sheet_name}.json' not found.")
                return
            try:
                os.remove(filename)
                messagebox.showinfo("Delete Sheet", f"Sheet '{sheet_name}' deleted successfully.")
                self.load_sheet_list() # Refresh the list after deletion
                # Optionally, load a new blank sheet or the first available sheet
                self.new_sheet()
            except Exception as e:
                messagebox.showerror("Delete Sheet Error", f"Failed to delete sheet: {e}")

    def import_sheet(self):
        """Imports data from a CSV file into the sheet."""
        filepath = filedialog.askopenfilename(
            title="Import CSV File",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        if not filepath:
            return

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                imported_data = [line.strip().split(',') for line in lines]
            
            if not imported_data:
                messagebox.showwarning("Import CSV", "The selected CSV file is empty.")
                return

            # Ask user if they want to use first row as header
            use_header = messagebox.askyesno("Import CSV", "Use the first row as column headers?")
            
            if use_header:
                header = imported_data[0]
                data_rows = imported_data[1:]
            else:
                header = [f"Col {i+1}" for i in range(max(len(row) for row in imported_data))]
                data_rows = imported_data

            # Prepend header to data_rows to create the full data structure
            full_data = [header] + data_rows

            self.create_sheet(initial_data=full_data)
            self.reset_filters_and_show_all(restore_order=True) # Clear any active filters
            messagebox.showinfo("Import CSV", f"CSV file imported successfully. Sheet name updated to '{os.path.basename(filepath).replace('.csv', '')}'.")
            
            # Update sheet name entry to reflect imported file name
            new_sheet_name = os.path.basename(filepath).replace('.csv', '')
            self.sheet_name_entry.delete(0, tk.END)
            self.sheet_name_entry.insert(0, new_sheet_name)
            self.current_sheet_name = new_sheet_name
            self._save_current_state() # Save state after import

        except Exception as e:
            messagebox.showerror("Import CSV Error", f"Failed to import CSV: {e}")

    def export_sheet(self):
        """Exports the current sheet data to a CSV file."""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
            initialfile=f"{self.current_sheet_name}.csv"
        )
        if not filepath:
            return

        try:
            current_data = self.get_current_table_data()
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                for row in current_data:
                    f.write(','.join(map(str, row)) + '\n') # Ensure all elements are strings
            messagebox.showinfo("Export CSV", "Sheet exported to CSV successfully!")
        except Exception as e:
            messagebox.showerror("Export CSV Error", f"Failed to export CSV: {e}")

    def print_sheet(self):
        """Placeholder for printing functionality."""
        messagebox.showinfo("Print Sheet", "Printing functionality is not yet implemented.")

    def refresh_treeview_from_data(self, data_to_display=None):
        """
        Refreshes the Treeview widget with the current `self.data` or provided `data_to_display`.
        Preserves header names.
        """
        # Remove all existing rows
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Reconfigure columns if COLS changed (e.g., after add/remove column)
        if len(self.tree["columns"]) != self.COLS:
            self.tree["columns"] = [f"col{j}" for j in range(self.COLS)]
            for j in range(self.COLS):
                header_text = self.data[0][j] if j < len(self.data[0]) else f"Attribute {j + 1}"
                self.tree.heading(f"col{j}", text=header_text, anchor=tk.W,
                                  command=lambda c=j: self.sort_column(c))
                self.tree.column(f"col{j}", width=120, minwidth=80, stretch=False)
        else:
            # Update existing headers in case they were changed in data[0]
            for j in range(self.COLS):
                self.tree.heading(f"col{j}", text=self.data[0][j], anchor=tk.W)

        # Determine which data to display
        display_data = data_to_display if data_to_display is not None else self.data[1:]

        # Insert data rows (skip header)
        for i, row_values in enumerate(display_data):
            # Ensure row has correct number of columns
            padded_row = row_values + [""] * (self.COLS - len(row_values))
            tag = "Treeview.Evenrow" if (i % 2 == 0) else "Treeview.Oddrow"
            self.tree.insert("", "end", values=padded_row[:self.COLS], tags=(tag,))


    # --- New Sorting Features ---

    def sort_column(self, col_index, reverse=False, sort_type='alphanumeric'):
        """
        Sorts the Treeview data by the specified column index.
        The sorting order (ascending/descending) is toggled with each click.
        `sort_type` can be 'alphanumeric' (default), 'numeric', or 'custom' (for elements/values).
        """
        # Get all children (rows) from the Treeview
        data_rows_iids = self.tree.get_children('')
        
        # Extract the values from the specified column for sorting
        # We need to get the actual data from self.data, not just what's visible
        # to ensure correct sorting of all rows, even hidden ones.
        
        # Create a list of tuples: (value_in_column, original_row_index, item_id)
        # We use original_row_index to maintain stability for elements with same value
        # and item_id to re-insert correctly
        data_to_sort = []
        for i, item_id in enumerate(data_rows_iids):
            # Retrieve values from the Treeview item (which reflects the current display state)
            values = self.tree.item(item_id, 'values')
            if col_index < len(values):
                data_to_sort.append((values[col_index], i, item_id))
            else:
                data_to_sort.append(("", i, item_id)) # Handle cases where a row might have fewer values than columns

        if not data_to_sort:
            return

        # Determine the current sort order for this column
        # Store sort order in a dictionary associated with the column
        if not hasattr(self, '_sort_orders'):
            self._sort_orders = {}
        
        # Default to ascending for a new column, or toggle existing
        current_sort_direction = self._sort_orders.get(col_index, 'ascending')
        new_sort_direction = 'descending' if current_sort_direction == 'ascending' else 'ascending'
        self._sort_orders[col_index] = new_sort_direction
        
        actual_reverse = (new_sort_direction == 'descending')

        # Perform sorting based on sort_type
        if sort_type == 'alphanumeric':
            # Sort alphabetically (string comparison)
            data_to_sort.sort(key=lambda x: x[0], reverse=actual_reverse)
        elif sort_type == 'numeric':
            # Sort numerically, handling conversion errors
            def try_numeric_conversion(value):
                try:
                    return float(value)
                except ValueError:
                    return float('-inf') if actual_reverse else float('inf') # Put non-numeric at ends
            data_to_sort.sort(key=lambda x: try_numeric_conversion(x[0]), reverse=actual_reverse)
        elif sort_type == 'custom':
            # This would require a predefined custom order for elements/values.
            # For demonstration, let's treat it as alphanumeric for now unless a specific order is defined.
            # In a real app, you'd have a dialog to define the custom order.
            messagebox.showinfo("Custom Sort", "Custom sort by elements/values would require defining a specific order. Falling back to alphanumeric for now.")
            data_to_sort.sort(key=lambda x: x[0], reverse=actual_reverse)
        
        # Re-insert sorted data into Treeview
        for index, (value, original_index, item_id) in enumerate(data_to_sort):
            self.tree.detach(item_id) # Remove from current position without deleting
            self.tree.move(item_id, '', index) # Insert at new sorted position
            # Reapply row tags (colors) after moving
            tag = "Treeview.Evenrow" if (index % 2 == 0) else "Treeview.Oddrow"
            self.tree.item(item_id, tags=(tag,))

        # Update sort arrow in heading
        for j in range(self.COLS):
            header_text = self.data[0][j]
            arrow = ""
            if j == col_index:
                arrow = " ▲" if new_sort_direction == 'ascending' else " ▼"
            # Remove previous arrow and add new one
            clean_header_text = header_text.replace(" ▲", "").replace(" ▼", "")
            self.tree.heading(f"col{j}", text=clean_header_text + arrow)


    def on_heading_right_click(self, event):
        """Shows a context menu for column actions (sort and filter)."""
        region = self.tree.identify_region(event.x, event.y)
        if region == "heading":
            column_id = self.tree.identify_column(event.x)
            col_index = int(column_id.replace('#', '')) - 1 # Convert '#n' to 0-based index

            # Create a context menu
            menu = tk.Menu(self.root, tearoff=0)
            menu.add_command(label="Sort A to Z", command=lambda: self.sort_column(col_index, reverse=False, sort_type='alphanumeric'))
            menu.add_command(label="Sort Z to A", command=lambda: self.sort_column(col_index, reverse=True, sort_type='alphanumeric'))
            menu.add_command(label="Sort Numerically (Asc)", command=lambda: self.sort_column(col_index, reverse=False, sort_type='numeric'))
            menu.add_command(label="Sort Numerically (Desc)", command=lambda: self.sort_column(col_index, reverse=True, sort_type='numeric'))
            menu.add_separator()
            menu.add_command(label="Filter Column...", command=lambda: self.show_filter_dialog(col_index))
            
            # Display the menu at the cursor position
            menu.post(event.x_root, event.y_root)

    # --- New Filtering Features (Filter Dialog) ---
    def show_filter_dialog(self, col_index):
        """
        Displays a custom filter dialog for the specified column.
        """
        # If a dialog is already open, close it first
        if self.filter_dialog_instance and self.filter_dialog_instance.winfo_exists():
            self.filter_dialog_instance.destroy()

        self._current_filter_col_index = col_index
        header_text = self.tree.heading(f"col{col_index}", 'text').replace(" ▲", "").replace(" ▼", "")
        
        # Create a Toplevel window for the filter dialog
        filter_window = tk.Toplevel(self.root)
        filter_window.title(f"Filter: {header_text}")
        filter_window.transient(self.root) # Make it appear on top of the main window
        filter_window.grab_set() # Make it modal
        filter_window.resizable(False, False)

        self.filter_dialog_instance = filter_window # Store reference

        dialog_frame = ttk.Frame(filter_window, padding="10")
        dialog_frame.pack(expand=True, fill=tk.BOTH)

        # Search bar for column name (read-only in this context, as dialog is for a specific column)
        ttk.Label(dialog_frame, text="Column Name:").grid(row=0, column=0, sticky="w", pady=2)
        col_name_entry = ttk.Entry(dialog_frame, width=30)
        col_name_entry.insert(0, header_text)
        col_name_entry.config(state='readonly') # Make it read-only
        col_name_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=2)

        # Search bar for elements/values
        ttk.Label(dialog_frame, text="Search Value:").grid(row=1, column=0, sticky="w", pady=2)
        search_value_var = tk.StringVar()
        search_value_entry = ttk.Entry(dialog_frame, textvariable=search_value_var, width=30)
        search_value_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        search_value_entry.focus_set()

        # Listbox to display all unique elements/values for the column
        ttk.Label(dialog_frame, text="Available Values:").grid(row=2, column=0, columnspan=2, sticky="w", pady=5)
        
        listbox_frame = ttk.Frame(dialog_frame)
        listbox_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        
        self.filter_listbox = tk.Listbox(listbox_frame, selectmode=tk.MULTIPLE, height=10)
        self.filter_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        listbox_vsb = ttk.Scrollbar(listbox_frame, orient="vertical", command=self.filter_listbox.yview)
        listbox_vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.filter_listbox.config(yscrollcommand=listbox_vsb.set)

        # Populate the listbox
        unique_values = self._get_unique_column_values(col_index)
        for val in sorted(unique_values): # Sort values A-Z for listbox
            self.filter_listbox.insert(tk.END, val)
        
        # Pre-select currently filtered values if any
        self._preselect_filtered_values(col_index)

        # Bind search bar to update listbox
        search_value_var.trace_add("write", lambda name, index, mode: self._update_filter_listbox(col_index, search_value_var.get()))

        # Buttons for filter actions
        button_frame = ttk.Frame(dialog_frame, padding="5")
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)

        select_all_button = ttk.Button(button_frame, text="Select All", command=lambda: self._select_all_listbox_items())
        select_all_button.pack(side=tk.LEFT, padx=5)

        clear_selection_button = ttk.Button(button_frame, text="Clear Selection", command=lambda: self._clear_listbox_selection())
        clear_selection_button.pack(side=tk.LEFT, padx=5)

        apply_button = ttk.Button(button_frame, text="Apply Filter", command=self._apply_filter)
        apply_button.pack(side=tk.LEFT, padx=5, expand=True)

        clear_button = ttk.Button(button_frame, text="Clear Filter", command=self._clear_column_filter)
        clear_button.pack(side=tk.LEFT, padx=5, expand=True)
        
        cancel_button = ttk.Button(button_frame, text="Cancel", command=filter_window.destroy)
        cancel_button.pack(side=tk.LEFT, padx=5, expand=True)
        
        # Ensure the filter dialog is properly closed and grabs are released
        filter_window.protocol("WM_DELETE_WINDOW", lambda: self._on_filter_dialog_close(filter_window))

    def _get_unique_column_values(self, col_index):
        """Retrieves all unique values from a specific column in self.data."""
        unique_values = set()
        if col_index < 0 or col_index >= self.COLS:
            return unique_values

        for row_data in self.data[1:]: # Skip header
            if col_index < len(row_data):
                val = row_data[col_index]
                if val is not None and val != "":
                    unique_values.add(str(val)) # Ensure string for comparison
        return list(unique_values)

    def _update_filter_listbox(self, col_index, search_text):
        """Updates the listbox content based on search text."""
        self.filter_listbox.delete(0, tk.END)
        unique_values = self._get_unique_column_values(col_index)
        
        filtered_values = []
        for val in sorted(unique_values):
            if search_text.lower() in str(val).lower(): # Case-insensitive search
                filtered_values.append(val)
        
        for val in filtered_values:
            self.filter_listbox.insert(tk.END, val)
        
        self._preselect_filtered_values(col_index) # Re-select based on current filter

    def _preselect_filtered_values(self, col_index):
        """Pre-selects values in the filter listbox that are currently applied as a filter."""
        # Get currently displayed rows (these reflect the current filter state)
        displayed_data = []
        for item_id in self.tree.get_children():
            displayed_data.append(list(self.tree.item(item_id, 'values')))

        if not displayed_data:
            return

        # Get values in the current filter column that are present in the displayed data
        current_visible_values = set()
        for row in displayed_data:
            if col_index < len(row):
                current_visible_values.add(str(row[col_index]))

        # Select corresponding items in the listbox
        self.filter_listbox.selection_clear(0, tk.END) # Clear existing selection
        for i in range(self.filter_listbox.size()):
            item_value = self.filter_listbox.get(i)
            if item_value in current_visible_values:
                self.filter_listbox.selection_set(i)
    
    def _select_all_listbox_items(self):
        """Selects all items in the filter listbox."""
        self.filter_listbox.selection_set(0, tk.END)

    def _clear_listbox_selection(self):
        """Clears all selections in the filter listbox."""
        self.filter_listbox.selection_clear(0, tk.END)

    def _apply_filter(self):
        """Applies the selected filter criteria to the Treeview."""
        if self._current_filter_col_index == -1:
            messagebox.showwarning("Filter Error", "No column selected for filtering.")
            return

        selected_values = [self.filter_listbox.get(i) for i in self.filter_listbox.curselection()]
        
        if not selected_values:
            # If nothing selected, it means clear this specific column's filter
            self._clear_column_filter(apply_to_ui=False) # Don't destroy dialog yet
            self.filter_dialog_instance.destroy()
            return

        # Filter the original_data (excluding header) based on selected values
        # This approach ensures filters are cumulative if desired, or reset previous if not
        filtered_rows = []
        header = self.data[0] # Get current header

        # Get all rows that are currently *not* filtered out by other columns (if applicable)
        # For simplicity, we'll re-filter from original_data each time a filter is applied/changed.
        # This means previous filters are essentially overwritten unless you implement
        # a more complex filter chain.

        # To support cumulative filters:
        # You would need a self.active_filters dictionary like:
        # self.active_filters = {col_index: [list of allowed values]}
        # When a filter is applied, update self.active_filters[col_index] = selected_values
        # Then, iterate through self.original_data, and for each row, check if it satisfies ALL active filters.
        
        # For this implementation, we simplify: applying a filter to a column shows *only* rows matching that column's selected values.
        # To make it cumulative, you'd need more complex logic.
        
        # Let's start with a fresh filter from the original data (resets previous single-column filters)
        # If you want cumulative filtering across columns, you'd iterate through a self.filtered_data
        # that gets progressively refined by each filter.
        
        # For now, we clear all filters and apply the new one for the selected column.
        # To maintain previous filters on *other* columns, you'd need to retrieve the current visible rows
        # before applying the new filter, and then filter *those* rows.

        # To avoid complexity of managing multiple concurrent filters, let's assume
        # this filter dialog focuses on filtering *one specific column* at a time,
        # and subsequent filters on *other* columns would further refine the result.

        # Let's assume a global filter state, where each column can have an active filter.
        # We need a dictionary to store active filters for each column.
        if not hasattr(self, '_active_column_filters'):
            self._active_column_filters = {}
        
        self._active_column_filters[self._current_filter_col_index] = selected_values

        # Apply all active filters to the original data
        self._apply_all_active_filters()

        self.filter_dialog_instance.destroy() # Close the filter dialog

    def _apply_all_active_filters(self):
        """Applies all currently active column filters to the Treeview data."""
        filtered_rows = []
        for original_row_data in self.original_data: # Iterate over the full original data
            row_matches_all_filters = True
            for col_index, allowed_values in self._active_column_filters.items():
                if col_index < len(original_row_data):
                    value_in_row = str(original_row_data[col_index])
                    if value_in_row not in allowed_values:
                        row_matches_all_filters = False
                        break # This row doesn't match this filter, so it's out
                else:
                    # Handle cases where row is shorter than filter column, consider it not matching
                    row_matches_all_filters = False
                    break
            
            if row_matches_all_filters:
                filtered_rows.append(original_row_data)
        
        self.refresh_treeview_from_data(filtered_rows)

    def _clear_column_filter(self, apply_to_ui=True):
        """Clears the filter for the currently active column."""
        if self._current_filter_col_index != -1 and hasattr(self, '_active_column_filters'):
            if self._current_filter_col_index in self._active_column_filters:
                del self._active_column_filters[self._current_filter_col_index]
                if apply_to_ui:
                    self._apply_all_active_filters() # Re-apply other active filters
                    messagebox.showinfo("Filter Cleared", f"Filter on column '{self.data[0][self._current_filter_col_index]}' cleared.")
            else:
                if apply_to_ui:
                    messagebox.showinfo("No Filter", "No filter active on this column.")
        if self.filter_dialog_instance:
            self.filter_dialog_instance.destroy() # Close the dialog


    def reset_filters_and_show_all(self, restore_order=True):
        """Resets all active filters and displays all original data."""
        if hasattr(self, '_active_column_filters'):
            self._active_column_filters = {} # Clear all active filters

        self.refresh_treeview_from_data(self.original_data) # Show all original data
        messagebox.showinfo("Filters Cleared", "All filters have been cleared.")
        
        if restore_order:
            # Optionally restore original order after clearing filters
            # This requires sorting based on the original data's order (e.g., using a hidden index column)
            # For simplicity, we just clear filter indicators.
            # If you want true original order, you'd need to store the iid order before any sort/filter.
            self.sort_column(0, sort_type='alphanumeric') # Re-sort by first column (A-Z) to give a default order
            # Remove any sort arrows from headers
            for j in range(self.COLS):
                clean_header_text = self.tree.heading(f"col{j}", 'text').replace(" ▲", "").replace(" ▼", "")
                self.tree.heading(f"col{j}", text=clean_header_text)
            if hasattr(self, '_sort_orders'):
                self._sort_orders = {} # Reset sort indicators

        if self.filter_dialog_instance and self.filter_dialog_instance.winfo_exists():
            self.filter_dialog_instance.destroy()


    def _on_filter_dialog_close(self, dialog_window):
        """Handles cleanup when the filter dialog is closed."""
        dialog_window.grab_release()
        dialog_window.destroy()
        self.filter_dialog_instance = None # Clear reference
        self._current_filter_col_index = -1 # Reset column index


# --- Main Application Entry Point ---
if __name__ == "__main__":
    root = tk.Tk()
    app = MainApplication(root)
    root.mainloop()