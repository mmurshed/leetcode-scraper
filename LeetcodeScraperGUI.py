import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
from logging import Logger, Handler
import sys

from LeetcodeScraper import init
from utils.Util import Util
from utils.ConfigLoader import ConfigLoader


class TextHandler(Handler):
    """Custom logging handler that writes to a tkinter Text widget."""
    def __init__(self, text_widget):
        Handler.__init__(self)
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        def append():
            self.text_widget.configure(state='normal')
            self.text_widget.insert(tk.END, msg + '\n')
            self.text_widget.configure(state='disabled')
            self.text_widget.see(tk.END)
        # Thread-safe append
        self.text_widget.after(0, append)


class LeetcodeScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("LeetCode Scraper v3.0-beta")
        self.root.geometry("900x700")
        
        # Initialize logger
        self.logger = Util.get_logger()
        
        # Initialize components (will be loaded when needed)
        self.config = None
        self.cache = None
        self.cards = None
        self.company = None
        self.qued = None
        self.submission = None
        
        self.setup_ui()
        
    def setup_ui(self):
        # Create main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="LeetCode Scraper", font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, pady=10)
        
        # Create notebook (tabs)
        notebook = ttk.Notebook(main_frame)
        notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Tab 1: Questions
        questions_frame = ttk.Frame(notebook)
        notebook.add(questions_frame, text="Questions")
        self.setup_questions_tab(questions_frame)
        
        # Tab 2: Cards
        cards_frame = ttk.Frame(notebook)
        notebook.add(cards_frame, text="Cards")
        self.setup_cards_tab(cards_frame)
        
        # Tab 3: Companies
        companies_frame = ttk.Frame(notebook)
        notebook.add(companies_frame, text="Companies")
        self.setup_companies_tab(companies_frame)
        
        # Tab 4: Submissions
        submissions_frame = ttk.Frame(notebook)
        notebook.add(submissions_frame, text="Submissions")
        self.setup_submissions_tab(submissions_frame)
        
        # Tab 5: Utilities
        utilities_frame = ttk.Frame(notebook)
        notebook.add(utilities_frame, text="Utilities")
        self.setup_utilities_tab(utilities_frame)
        
        # Tab 6: Config (last tab)
        config_frame = ttk.Frame(notebook)
        config_scrollable = self.create_scrollable_frame(config_frame)
        notebook.add(config_frame, text="Config")
        self.setup_config_tab(config_scrollable)
        
        # Store notebook and config tab index for auto-loading
        self.notebook = notebook
        self.config_tab_index = 5  # Index of the Config tab (0-based)
        self.questions_tab_index = 0
        self.cards_tab_index = 1
        self.companies_tab_index = 2
        self.submissions_tab_index = 3
        
        # Track which lists have been loaded
        self.questions_loaded = False
        self.cards_loaded = False
        self.companies_loaded = False
        self.submissions_loaded = False
        
        # Bind tab change event to auto-load config and lists
        notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        
        # Log output area
        log_frame = ttk.LabelFrame(main_frame, text="Log Output", padding="5")
        log_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        main_frame.rowconfigure(2, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, state='disabled', wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Add text handler to logger
        text_handler = TextHandler(self.log_text)
        text_handler.setFormatter(self.logger.handlers[0].formatter if self.logger.handlers else None)
        self.logger.addHandler(text_handler)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=3, column=0, sticky=(tk.W, tk.E))
    
    def create_scrollable_frame(self, parent):
        """Create a scrollable frame for long content."""
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        return scrollable_frame
    
    def on_tab_changed(self, event):
        """Handle tab change event - auto-load config and lists when tabs are selected."""
        selected_tab = self.notebook.index(self.notebook.select())
        
        if selected_tab == self.config_tab_index:
            # Auto-load configuration when switching to Config tab
            self.load_config_to_form()
        elif selected_tab == self.questions_tab_index:
            # Auto-load questions list when switching to Questions tab
            if not self.questions_loaded:
                self.load_question_list(show_message=False)
        elif selected_tab == self.cards_tab_index:
            # Auto-load cards list when switching to Cards tab
            if not self.cards_loaded:
                self.load_card_list(show_message=False)
        elif selected_tab == self.companies_tab_index:
            # Auto-load companies list when switching to Companies tab
            if not self.companies_loaded:
                self.load_company_list(show_message=False)
        elif selected_tab == self.submissions_tab_index:
            # Auto-load questions list for submissions when switching to Submissions tab
            if not self.submissions_loaded:
                self.load_submission_question_list(show_message=False)
    
    def setup_config_tab(self, parent):
        """Setup configuration tab with all config fields."""
        parent.columnconfigure(0, weight=1)
        
        # Initialize config field variables
        self.config_vars = {}
        
        # Title
        ttk.Label(parent, text="LeetCode Scraper Configuration", font=('Arial', 12, 'bold')).pack(pady=10)
        ttk.Label(parent, text="Configuration is automatically loaded when you open this tab", 
                 font=('Arial', 9, 'italic'), foreground='gray').pack()
        
        # Save button at top
        button_frame = ttk.Frame(parent)
        button_frame.pack(pady=5)
        ttk.Button(button_frame, text="Save Config", command=self.save_config_from_form, width=20).pack(padx=5)
        
        ttk.Separator(parent, orient='horizontal').pack(fill='x', pady=10)
        
        # Basic Settings
        basic_frame = ttk.LabelFrame(parent, text="Basic Settings", padding="10")
        basic_frame.pack(fill='x', padx=10, pady=5)
        
        self.add_text_field(basic_frame, "leetcode_cookie", "LeetCode Cookie:", width=60)
        self.add_directory_field(basic_frame, "save_directory", "Save Directory:")
        
        ttk.Separator(parent, orient='horizontal').pack(fill='x', pady=10)
        
        # Cache Settings
        cache_frame = ttk.LabelFrame(parent, text="Cache Settings", padding="10")
        cache_frame.pack(fill='x', padx=10, pady=5)
        
        self.add_checkbox_field(cache_frame, "cache_api_calls", "Cache API Calls")
        self.add_number_field(cache_frame, "cache_expiration_days", "Cache Expiration (days):")
        
        ttk.Separator(parent, orient='horizontal').pack(fill='x', pady=10)
        
        # Download Settings
        download_frame = ttk.LabelFrame(parent, text="Download Settings", padding="10")
        download_frame.pack(fill='x', padx=10, pady=5)
        
        self.add_checkbox_field(download_frame, "overwrite", "Overwrite Existing Files")
        self.add_checkbox_field(download_frame, "download_images", "Download Images")
        self.add_checkbox_field(download_frame, "download_videos", "Download Videos")
        self.add_checkbox_field(download_frame, "include_default_code", "Include Default Code")
        
        ttk.Separator(parent, orient='horizontal').pack(fill='x', pady=10)
        
        # Content Settings
        content_frame = ttk.LabelFrame(parent, text="Content Settings", padding="10")
        content_frame.pack(fill='x', padx=10, pady=5)
        
        self.add_text_field(content_frame, "preferred_language_order", "Preferred Languages (comma-separated):")
        self.add_number_field(content_frame, "include_submissions_count", "Submissions to Include:")
        self.add_number_field(content_frame, "include_community_solution_count", "Community Solutions to Include:")
        
        ttk.Separator(parent, orient='horizontal').pack(fill='x', pady=10)
        
        # Image Processing
        image_frame = ttk.LabelFrame(parent, text="Image Processing", padding="10")
        image_frame.pack(fill='x', padx=10, pady=5)
        
        self.add_checkbox_field(image_frame, "extract_gif_frames", "Extract GIF Frames")
        self.add_checkbox_field(image_frame, "recompress_image", "Recompress Images")
        self.add_checkbox_field(image_frame, "base64_encode_image", "Base64 Encode Images")
        
        ttk.Separator(parent, orient='horizontal').pack(fill='x', pady=10)
        
        # Advanced Settings
        advanced_frame = ttk.LabelFrame(parent, text="Advanced Settings", padding="10")
        advanced_frame.pack(fill='x', padx=10, pady=5)
        
        self.add_number_field(advanced_frame, "threads_count_for_pdf_conversion", "PDF Conversion Threads:")
        self.add_number_field(advanced_frame, "api_max_failures", "API Max Failures:")
        self.add_dropdown_field(advanced_frame, "logging_level", "Logging Level:", 
                               ["debug", "info", "warning", "error"])
        
        ttk.Separator(parent, orient='horizontal').pack(fill='x', pady=10)
        
        # AI Solution Settings
        ai_frame = ttk.LabelFrame(parent, text="AI Solution Generator", padding="10")
        ai_frame.pack(fill='x', padx=10, pady=5)
        
        self.add_dropdown_field(ai_frame, "ai_solution_generator", "AI Generator:", 
                               ["None", "openai", "ollama"])
        
        # OpenAI Settings
        openai_subframe = ttk.LabelFrame(ai_frame, text="OpenAI Settings", padding="5")
        openai_subframe.pack(fill='x', pady=5)
        self.add_text_field(openai_subframe, "open_ai_api_key", "API Key:", width=50)
        self.add_text_field(openai_subframe, "open_ai_model", "Model:", width=30)
        
        # Ollama Settings
        ollama_subframe = ttk.LabelFrame(ai_frame, text="Ollama Settings", padding="5")
        ollama_subframe.pack(fill='x', pady=5)
        self.add_text_field(ollama_subframe, "ollama_url", "URL:")
        self.add_text_field(ollama_subframe, "ollama_model", "Model:")
        
        ttk.Separator(parent, orient='horizontal').pack(fill='x', pady=10)
        
        # Save button at bottom
        button_frame2 = ttk.Frame(parent)
        button_frame2.pack(pady=10)
        ttk.Button(button_frame2, text="Save Config", command=self.save_config_from_form, width=20).pack(padx=5)
    
    def add_text_field(self, parent, key, label, width=40):
        """Add a text field to the form."""
        frame = ttk.Frame(parent)
        frame.pack(fill='x', pady=2)
        ttk.Label(frame, text=label, width=30, anchor='w').pack(side='left', padx=5)
        var = tk.StringVar()
        entry = ttk.Entry(frame, textvariable=var, width=width)
        entry.pack(side='left', padx=5, fill='x', expand=True)
        self.config_vars[key] = var
        
    def add_directory_field(self, parent, key, label):
        """Add a directory field with browse button."""
        frame = ttk.Frame(parent)
        frame.pack(fill='x', pady=2)
        ttk.Label(frame, text=label, width=30, anchor='w').pack(side='left', padx=5)
        var = tk.StringVar()
        entry = ttk.Entry(frame, textvariable=var, width=40)
        entry.pack(side='left', padx=5, fill='x', expand=True)
        ttk.Button(frame, text="Browse", 
                  command=lambda: self.browse_directory(var)).pack(side='left', padx=5)
        self.config_vars[key] = var
        
    def add_checkbox_field(self, parent, key, label):
        """Add a checkbox field."""
        var = tk.BooleanVar()
        cb = ttk.Checkbutton(parent, text=label, variable=var)
        cb.pack(anchor='w', pady=2)
        self.config_vars[key] = var
        
    def add_number_field(self, parent, key, label):
        """Add a number input field."""
        frame = ttk.Frame(parent)
        frame.pack(fill='x', pady=2)
        ttk.Label(frame, text=label, width=30, anchor='w').pack(side='left', padx=5)
        var = tk.IntVar()
        spinbox = ttk.Spinbox(frame, from_=0, to=100, textvariable=var, width=10)
        spinbox.pack(side='left', padx=5)
        self.config_vars[key] = var
        
    def add_dropdown_field(self, parent, key, label, options):
        """Add a dropdown field."""
        frame = ttk.Frame(parent)
        frame.pack(fill='x', pady=2)
        ttk.Label(frame, text=label, width=30, anchor='w').pack(side='left', padx=5)
        var = tk.StringVar()
        combo = ttk.Combobox(frame, textvariable=var, values=options, width=20, state='readonly')
        combo.pack(side='left', padx=5)
        self.config_vars[key] = var
        
    def browse_directory(self, var):
        """Browse for a directory."""
        directory = filedialog.askdirectory(title="Select Directory")
        if directory:
            var.set(directory)
    
    def load_config_to_form(self, show_messages=False):
        """Load configuration from file and populate form fields.
        
        Args:
            show_messages: If True, show success/error messages. Default False for auto-load.
        """
        try:
            from utils.Config import Config
            import os
            
            config_path = os.path.join(os.path.expanduser("~"), ".leetcode-scraper", "config.json")
            if not os.path.exists(config_path):
                if show_messages:
                    messagebox.showwarning("Config Not Found", "No configuration file found. Please fill in the form and save.")
                else:
                    self.logger.info("No config file found. Please configure and save.")
                return
                
            config = Config.from_json_file(config_path)
            
            # Populate all fields
            for key, var in self.config_vars.items():
                value = getattr(config, key, None)
                if value is not None:
                    if isinstance(var, tk.BooleanVar):
                        var.set(bool(value))
                    elif isinstance(var, tk.IntVar):
                        var.set(int(value))
                    elif isinstance(var, tk.StringVar):
                        if isinstance(value, list):
                            var.set(', '.join(str(v) for v in value))
                        elif value is None or value == "None":
                            var.set("None")
                        else:
                            var.set(str(value))
            
            self.logger.info("Configuration loaded successfully")
            self.status_var.set("Config loaded")
            if show_messages:
                messagebox.showinfo("Success", "Configuration loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            if show_messages:
                messagebox.showerror("Error", f"Failed to load configuration: {e}")
    
    def save_config_from_form(self):
        """Save configuration from form fields to file."""
        try:
            from utils.Config import Config
            import os
            
            # Create config directory if it doesn't exist
            config_dir = os.path.join(os.path.expanduser("~"), ".leetcode-scraper")
            os.makedirs(config_dir, exist_ok=True)
            config_path = os.path.join(config_dir, "config.json")
            
            # Load existing config or create new one
            if os.path.exists(config_path):
                config = Config.from_json_file(config_path)
            else:
                config = Config()
            
            # Update config from form fields
            for key, var in self.config_vars.items():
                value = var.get()
                
                if isinstance(var, tk.BooleanVar):
                    setattr(config, key, bool(value))
                elif isinstance(var, tk.IntVar):
                    setattr(config, key, int(value))
                elif isinstance(var, tk.StringVar):
                    if key == "preferred_language_order":
                        # Convert comma-separated string to list
                        langs = [s.strip().lower() for s in value.split(',') if s.strip()]
                        setattr(config, key, langs if langs else ["all"])
                    elif key == "ai_solution_generator":
                        # Handle None vs string
                        setattr(config, key, None if value == "None" else value)
                    else:
                        setattr(config, key, value)
            
            # Set derivative values
            config.set_derivative_values()
            
            # Save to file
            config.to_json_file(config_path)
            
            self.logger.info(f"Configuration saved to {config_path}")
            self.status_var.set("Config saved")
            messagebox.showinfo("Success", f"Configuration saved to {config_path}")
        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")
            messagebox.showerror("Error", f"Failed to save configuration: {e}")
        
    def setup_questions_tab(self, parent):
        parent.columnconfigure(0, weight=1)
        
        # Questions section
        questions_frame = ttk.LabelFrame(parent, text="Questions", padding="10")
        questions_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Button(questions_frame, text="Download All Questions", command=self.download_all_questions, width=30).pack(pady=5)
        
        ttk.Separator(questions_frame, orient='horizontal').pack(fill='x', pady=10)
        
        # Single Question Download
        single_label = ttk.Label(questions_frame, text="Download Single Question", font=('Arial', 10, 'bold'))
        single_label.pack(pady=(5, 5))
        
        # Question ID input with dropdown
        question_input_frame = ttk.Frame(questions_frame)
        question_input_frame.pack(pady=5)
        ttk.Label(question_input_frame, text="Question ID:").pack(side='left', padx=5)
        
        # Use Combobox for both typing and dropdown
        self.question_id_var = tk.StringVar()
        self.question_id_combo = ttk.Combobox(question_input_frame, textvariable=self.question_id_var, width=30)
        self.question_id_combo.pack(side='left', padx=5)
        self.question_id_combo['values'] = ()  # Empty initially
        
        ttk.Button(question_input_frame, text="Download", command=self.download_question).pack(side='left')
        
        ttk.Separator(questions_frame, orient='horizontal').pack(fill='x', pady=10)
        
        # Range Download
        range_label = ttk.Label(questions_frame, text="Download Question Range", font=('Arial', 10, 'bold'))
        range_label.pack(pady=(5, 5))
        
        # Range input frame
        range_input_frame = ttk.Frame(questions_frame)
        range_input_frame.pack(pady=5)
        
        ttk.Label(range_input_frame, text="From ID:").pack(side='left', padx=5)
        self.question_from_id_var = tk.StringVar()
        self.question_from_id_combo = ttk.Combobox(range_input_frame, textvariable=self.question_from_id_var, width=15)
        self.question_from_id_combo.pack(side='left', padx=5)
        self.question_from_id_combo['values'] = ()  # Will be populated with question list
        
        ttk.Label(range_input_frame, text="To ID:").pack(side='left', padx=5)
        self.question_to_id_var = tk.StringVar()
        self.question_to_id_combo = ttk.Combobox(range_input_frame, textvariable=self.question_to_id_var, width=15)
        self.question_to_id_combo.pack(side='left', padx=5)
        self.question_to_id_combo['values'] = ()  # Will be populated with question list
        
        ttk.Button(range_input_frame, text="Download Range", command=self.download_question_range).pack(side='left', padx=5)
        
        # Info text
        info_frame = ttk.Frame(parent)
        info_frame.pack(fill='x', padx=10, pady=10)
        info_text = ttk.Label(info_frame, text="Download individual questions by ID, a range of questions, or all questions from LeetCode.\nQuestions are organized into folders by hundreds (0100, 0200, etc.).\n\nQuestion list loads automatically when you open this tab.",
                             wraplength=500, justify='left', foreground='gray', font=('Arial', 9, 'italic'))
        info_text.pack()
    
    def load_question_list(self, show_message=True):
        """Load all questions from LeetCode API and populate the dropdown.
        
        Args:
            show_message: If True, show success/error messages. Default True.
        """
        def task():
            try:
                self.status_var.set("Loading questions list...")
                self.logger.info("Loading questions list from LeetCode API...")
                
                # Import here to avoid circular dependencies
                from api.ApiManager import ApiManager
                from api.CachedRequest import CachedRequest
                from diskcache import Cache
                from utils.ConfigLoader import ConfigLoader
                import os
                
                # Load config to initialize API
                config_path = os.path.join(os.path.expanduser("~"), ".leetcode-scraper", "config.json")
                if not os.path.exists(config_path):
                    self.logger.error("No config found. Please configure first.")
                    if show_message:
                        messagebox.showerror("Error", "No configuration found. Please go to Config tab and save a configuration first.")
                    return
                
                # Initialize components if needed
                self.initialize_components()
                
                # Get all questions
                questions = self.qued.lc.get_all_questions()
                
                if questions:
                    # Format as "ID - Title" for display
                    question_list = [f"{q.id} - {q.title}" for q in sorted(questions, key=lambda x: int(x.id))]
                    
                    # Update all question comboboxes
                    self.question_id_combo['values'] = question_list
                    self.question_from_id_combo['values'] = question_list
                    self.question_to_id_combo['values'] = question_list
                    
                    self.questions_loaded = True
                    self.logger.info(f"Loaded {len(questions)} questions")
                    self.status_var.set(f"Loaded {len(questions)} questions")
                    if show_message:
                        messagebox.showinfo("Success", f"Loaded {len(questions)} questions into dropdown")
                else:
                    self.logger.error("No questions found")
                    if show_message:
                        messagebox.showwarning("Warning", "No questions found")
                    
            except Exception as e:
                self.logger.error(f"Failed to load questions: {e}")
                self.status_var.set("Failed to load questions")
                if show_message:
                    messagebox.showerror("Error", f"Failed to load questions: {e}")
        
        self.run_in_thread(task)
        
    def setup_cards_tab(self, parent):
        parent.columnconfigure(0, weight=1)
        
        # Cards section
        cards_frame = ttk.LabelFrame(parent, text="Cards", padding="10")
        cards_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Button(cards_frame, text="Download All Cards", command=self.download_all_cards, width=30).pack(pady=5)
        
        ttk.Separator(cards_frame, orient='horizontal').pack(fill='x', pady=10)
        
        # Card slug input with dropdown
        card_input_frame = ttk.Frame(cards_frame)
        card_input_frame.pack(pady=10)
        ttk.Label(card_input_frame, text="Card Name:").pack(side='left', padx=5)
        
        # Use Combobox for both typing and dropdown
        self.card_slug_var = tk.StringVar()
        self.card_slug_combo = ttk.Combobox(card_input_frame, textvariable=self.card_slug_var, width=30)
        self.card_slug_combo.pack(side='left', padx=5)
        self.card_slug_combo['values'] = ()  # Empty initially
        
        ttk.Button(card_input_frame, text="Download", command=self.download_card).pack(side='left')
        
        # Info text
        info_frame = ttk.Frame(parent)
        info_frame.pack(fill='x', padx=10, pady=10)
        info_text = ttk.Label(info_frame, text="Download LeetCode Explore Cards by slug name.\nCards contain curated problem sets and learning materials.\n\nCard list loads automatically when you open this tab.",
                             wraplength=500, justify='left', foreground='gray', font=('Arial', 9, 'italic'))
        info_text.pack()
    
    def load_card_list(self, show_message=True):
        """Load all cards from LeetCode API and populate the dropdown.
        
        Args:
            show_message: If True, show success/error messages. Default True.
        """
        def task():
            try:
                self.status_var.set("Loading cards list...")
                self.logger.info("Loading cards list from LeetCode API...")
                
                # Initialize components if needed
                self.initialize_components()
                
                # Get all cards
                categories = self.cards.lc.get_categories()
                
                if categories:
                    card_list = []
                    for category in categories:
                        if 'cards' in category:
                            for card in category['cards']:
                                if 'slug' in card:
                                    card_list.append(card['slug'])
                    
                    # Sort and remove duplicates
                    card_list = sorted(set(card_list))
                    
                    # Update combobox values
                    self.card_slug_combo['values'] = card_list
                    
                    self.cards_loaded = True
                    self.logger.info(f"Loaded {len(card_list)} cards")
                    self.status_var.set(f"Loaded {len(card_list)} cards")
                    if show_message:
                        messagebox.showinfo("Success", f"Loaded {len(card_list)} cards into dropdown")
                else:
                    self.logger.error("No cards found")
                    if show_message:
                        messagebox.showwarning("Warning", "No cards found")
                    
            except Exception as e:
                self.logger.error(f"Failed to load cards: {e}")
                self.status_var.set("Failed to load cards")
                if show_message:
                    messagebox.showerror("Error", f"Failed to load cards: {e}")
        
        self.run_in_thread(task)
        
    def setup_companies_tab(self, parent):
        parent.columnconfigure(0, weight=1)
        
        ttk.Button(parent, text="Download All Company Questions", command=self.download_all_companies, width=30).pack(pady=10)
        
        ttk.Separator(parent, orient='horizontal').pack(fill='x', pady=10)
        
        # Single company
        company_frame = ttk.LabelFrame(parent, text="Single Company", padding="10")
        company_frame.pack(fill='x', padx=10, pady=5)
        
        # Company slug input with dropdown
        company_input_frame = ttk.Frame(company_frame)
        company_input_frame.pack(pady=10)
        ttk.Label(company_input_frame, text="Company Name:").pack(side='left', padx=5)
        
        # Use Combobox for both typing and dropdown
        self.company_slug_var = tk.StringVar()
        self.company_slug_combo = ttk.Combobox(company_input_frame, textvariable=self.company_slug_var, width=30)
        self.company_slug_combo.pack(side='left', padx=5)
        self.company_slug_combo['values'] = ()  # Empty initially
        
        ttk.Button(company_input_frame, text="Download All Questions", command=self.download_company_questions).pack(side='left', padx=5)
        
        ttk.Separator(parent, orient='horizontal').pack(fill='x', pady=10)
        
        # Favorite company questions
        fav_frame = ttk.LabelFrame(parent, text="Favorite Company Questions", padding="10")
        fav_frame.pack(fill='x', padx=10, pady=5)
        
        fav_input_frame = ttk.Frame(fav_frame)
        fav_input_frame.pack(pady=5)
        ttk.Label(fav_input_frame, text="Company Name:").pack(side='left', padx=5)
        
        # Use Combobox for favorite company slug
        self.fav_company_slug_var = tk.StringVar()
        self.fav_company_slug_combo = ttk.Combobox(fav_input_frame, textvariable=self.fav_company_slug_var, width=20)
        self.fav_company_slug_combo.pack(side='left', padx=5)
        self.fav_company_slug_combo['values'] = ()  # Will be populated with company list
        
        ttk.Button(fav_input_frame, text="Load Favorites", command=self.load_company_favorites).pack(side='left')
        
        self.favorites_listbox = tk.Listbox(fav_frame, height=5)
        self.favorites_listbox.pack(fill='x', pady=5)
        
        ttk.Button(fav_frame, text="Download Selected Favorite", command=self.download_favorite_questions).pack(pady=5)
        
        # Info text
        info_frame = ttk.Frame(parent)
        info_frame.pack(fill='x', padx=10, pady=10)
        info_text = ttk.Label(info_frame, text="Company list loads automatically when you open this tab.",
                             wraplength=500, justify='left', foreground='gray', font=('Arial', 9, 'italic'))
        info_text.pack()
    
    def load_company_list(self, show_message=True):
        """Load all companies from LeetCode API and populate the dropdown.
        
        Args:
            show_message: If True, show success/error messages. Default True.
        """
        def task():
            try:
                self.status_var.set("Loading companies list...")
                self.logger.info("Loading companies list from LeetCode API...")
                
                # Initialize components if needed
                self.initialize_components()
                
                # Get all companies
                companies = self.company.get_company_slugs()
                
                if companies:
                    # Format as "name (slug)" for display
                    company_list = [f"{c.name} ({c.slug})" for c in sorted(companies, key=lambda x: x.name)]
                    company_slugs = [c.slug for c in sorted(companies, key=lambda x: x.name)]
                    
                    # Update both comboboxes
                    self.company_slug_combo['values'] = company_list
                    self.fav_company_slug_combo['values'] = company_list
                    
                    # Store slug mapping for easy lookup
                    self.company_slug_mapping = {f"{c.name} ({c.slug})": c.slug for c in companies}
                    
                    self.companies_loaded = True
                    self.logger.info(f"Loaded {len(companies)} companies")
                    self.status_var.set(f"Loaded {len(companies)} companies")
                    if show_message:
                        messagebox.showinfo("Success", f"Loaded {len(companies)} companies into dropdown")
                else:
                    self.logger.error("No companies found")
                    if show_message:
                        messagebox.showwarning("Warning", "No companies found")
                    
            except Exception as e:
                self.logger.error(f"Failed to load companies: {e}")
                self.status_var.set("Failed to load companies")
                if show_message:
                    messagebox.showerror("Error", f"Failed to load companies: {e}")
        
        self.run_in_thread(task)
        
    def setup_submissions_tab(self, parent):
        parent.columnconfigure(0, weight=1)
        
        ttk.Button(parent, text="Download All Your Submissions", command=self.download_all_submissions, width=30).pack(pady=10)
        
        ttk.Separator(parent, orient='horizontal').pack(fill='x', pady=10)
        
        # Single question submissions
        submission_frame = ttk.LabelFrame(parent, text="Download Submissions by Question ID", padding="10")
        submission_frame.pack(fill='x', padx=10, pady=5)
        
        # Question ID input with dropdown
        submission_input_frame = ttk.Frame(submission_frame)
        submission_input_frame.pack(pady=10)
        ttk.Label(submission_input_frame, text="Question ID:").pack(side='left', padx=5)
        
        # Use Combobox for both typing and dropdown
        self.submission_question_id_var = tk.StringVar()
        self.submission_question_id_combo = ttk.Combobox(submission_input_frame, textvariable=self.submission_question_id_var, width=30)
        self.submission_question_id_combo.pack(side='left', padx=5)
        self.submission_question_id_combo['values'] = ()  # Empty initially
        
        ttk.Button(submission_input_frame, text="Download", command=self.download_question_submissions).pack(side='left')
        
        # Info text
        info_frame = ttk.Frame(parent)
        info_frame.pack(fill='x', padx=10, pady=10)
        info_text = ttk.Label(info_frame, text="Download your submission history for specific questions or all questions.\nQuestion list loads automatically when you open this tab.",
                             wraplength=500, justify='left', foreground='gray', font=('Arial', 9, 'italic'))
        info_text.pack()
    
    def load_submission_question_list(self, show_message=True):
        """Load all questions from LeetCode API and populate the submissions dropdown.
        
        Args:
            show_message: If True, show success/error messages. Default True.
        """
        def task():
            try:
                self.status_var.set("Loading questions list...")
                self.logger.info("Loading questions list from LeetCode API...")
                
                # Initialize components if needed
                self.initialize_components()
                
                # Get all questions
                questions = self.qued.lc.get_all_questions()
                
                if questions:
                    # Format as "ID - Title" for display
                    question_list = [f"{q.id} - {q.title}" for q in sorted(questions, key=lambda x: int(x.id))]
                    
                    # Update combobox values
                    self.submission_question_id_combo['values'] = question_list
                    
                    self.submissions_loaded = True
                    self.logger.info(f"Loaded {len(questions)} questions")
                    self.status_var.set(f"Loaded {len(questions)} questions")
                    if show_message:
                        messagebox.showinfo("Success", f"Loaded {len(questions)} questions into dropdown")
                else:
                    self.logger.error("No questions found")
                    if show_message:
                        messagebox.showwarning("Warning", "No questions found")
                    
            except Exception as e:
                self.logger.error(f"Failed to load questions: {e}")
                self.status_var.set("Failed to load questions")
                if show_message:
                    messagebox.showerror("Error", f"Failed to load questions: {e}")
        
        self.run_in_thread(task)
        
    def setup_utilities_tab(self, parent):
        parent.columnconfigure(0, weight=1)
        
        # PDF Conversion
        pdf_frame = ttk.LabelFrame(parent, text="PDF Conversion", padding="10")
        pdf_frame.pack(fill='x', padx=10, pady=5)
        
        self.pdf_path_var = tk.StringVar()
        pdf_input_frame = ttk.Frame(pdf_frame)
        pdf_input_frame.pack(pady=5, fill='x')
        ttk.Label(pdf_input_frame, text="Path:").pack(side='left', padx=5)
        ttk.Entry(pdf_input_frame, textvariable=self.pdf_path_var, width=40).pack(side='left', padx=5, fill='x', expand=True)
        ttk.Button(pdf_input_frame, text="Browse", command=self.browse_pdf_path).pack(side='left', padx=5)
        ttk.Button(pdf_frame, text="Convert to PDF", command=self.convert_to_pdf).pack(pady=5)
        
        ttk.Separator(parent, orient='horizontal').pack(fill='x', pady=10)
        
        # Cache Management
        cache_frame = ttk.LabelFrame(parent, text="Cache Management", padding="10")
        cache_frame.pack(fill='x', padx=10, pady=5)
        
        cache_input_frame = ttk.Frame(cache_frame)
        cache_input_frame.pack(pady=5)
        ttk.Label(cache_input_frame, text="Cache Key:").pack(side='left', padx=5)
        self.cache_key_entry = ttk.Entry(cache_input_frame, width=30)
        self.cache_key_entry.pack(side='left', padx=5)
        ttk.Button(cache_input_frame, text="Get", command=self.get_cache).pack(side='left', padx=2)
        ttk.Button(cache_input_frame, text="Delete", command=self.delete_cache).pack(side='left', padx=2)
        
        ttk.Button(cache_frame, text="Clear All Cache", command=self.clear_cache).pack(pady=5)
        
    def run_in_thread(self, func):
        """Run a function in a separate thread to avoid blocking the GUI."""
        def wrapper():
            try:
                self.status_var.set("Running...")
                func()
                self.status_var.set("Completed successfully")
            except Exception as e:
                self.logger.error(f"Error: {e}")
                self.status_var.set(f"Error: {str(e)[:50]}")
                messagebox.showerror("Error", str(e))
        
        thread = threading.Thread(target=wrapper, daemon=True)
        thread.start()
        
    def initialize_components(self):
        """Initialize scraper components if not already initialized."""
        if self.config is None:
            try:
                self.config, self.cache, self.cards, self.company, self.qued, self.submission = init(self.logger)
            except Exception as e:
                raise Exception(f"Initialization error: {e}\n\nPlease setup config first (Option 1)")
    
    # Command methods
    def download_all_cards(self):
        def task():
            self.initialize_components()
            self.cards.download_all_cards()
        self.run_in_thread(task)
        
    def download_card(self):
        card_slug = self.card_slug_var.get().strip()
        if not card_slug:
            messagebox.showwarning("Input Required", "Please enter or select a card name")
            return
        def task():
            self.initialize_components()
            self.cards.download_selected_card(card_slug)
        self.run_in_thread(task)
        
    def download_all_questions(self):
        def task():
            self.initialize_components()
            self.qued.download_all_questions()
        self.run_in_thread(task)
        
    def download_question(self):
        question_input = self.question_id_var.get().strip()
        if not question_input:
            messagebox.showwarning("Input Required", "Please enter or select a question ID")
            return
        
        # Extract question ID from input
        # Input can be either "123" or "123 - Question Title"
        try:
            if ' - ' in question_input:
                # Extract ID from "ID - Title" format
                question_id = int(question_input.split(' - ')[0].strip())
            else:
                # Direct ID input
                question_id = int(question_input)
        except ValueError:
            messagebox.showerror("Invalid Input", "Question ID must be a number.\nFormat: 123 or select from dropdown")
            return
        
        # Validate it's a positive integer
        if question_id <= 0:
            messagebox.showerror("Invalid Input", "Question ID must be a positive number")
            return
            
        def task():
            self.initialize_components()
            self.qued.download_selected_question(question_id)
        self.run_in_thread(task)
    
    def download_question_range(self):
        """Download a range of questions from start ID to end ID."""
        from_input = self.question_from_id_var.get().strip()
        to_input = self.question_to_id_var.get().strip()
        
        if not from_input or not to_input:
            messagebox.showwarning("Input Required", "Please enter both From ID and To ID")
            return
        
        # Validate and parse IDs (handle both "123" and "123 - Title" formats)
        try:
            if ' - ' in from_input:
                from_id = int(from_input.split(' - ')[0].strip())
            else:
                from_id = int(from_input)
                
            if ' - ' in to_input:
                to_id = int(to_input.split(' - ')[0].strip())
            else:
                to_id = int(to_input)
        except ValueError:
            messagebox.showerror("Invalid Input", "Both From ID and To ID must be numbers.\nFormat: 123 or select from dropdown")
            return
        
        # Validate range
        if from_id <= 0 or to_id <= 0:
            messagebox.showerror("Invalid Input", "Question IDs must be positive numbers")
            return
        
        if from_id > to_id:
            messagebox.showerror("Invalid Range", "From ID must be less than or equal to To ID")
            return
        
        # Confirm large ranges
        range_size = to_id - from_id + 1
        if range_size > 100:
            if not messagebox.askyesno("Confirm Large Range", 
                                       f"You are about to download {range_size} questions.\nThis may take a long time. Continue?"):
                return
        
        def task():
            self.initialize_components()
            
            # Get all questions to validate IDs exist
            all_questions = self.qued.lc.get_all_questions()
            all_question_ids = {int(q.id) for q in all_questions}
            
            # Download questions in the range
            downloaded_count = 0
            skipped_count = 0
            
            for question_id in range(from_id, to_id + 1):
                if question_id not in all_question_ids:
                    self.logger.warning(f"Question ID {question_id} does not exist, skipping")
                    skipped_count += 1
                    continue
                
                try:
                    self.logger.info(f"Downloading question {question_id} ({downloaded_count + 1}/{range_size - skipped_count})")
                    self.qued.download_selected_question(question_id)
                    downloaded_count += 1
                except Exception as e:
                    self.logger.error(f"Failed to download question {question_id}: {e}")
            
            self.logger.info(f"Range download complete: {downloaded_count} downloaded, {skipped_count} skipped")
            
        self.run_in_thread(task)
        
    def download_all_companies(self):
        def task():
            self.initialize_components()
            self.company.download_all_company_questions()
        self.run_in_thread(task)
        
    def download_company_questions(self):
        company_input = self.company_slug_var.get().strip()
        if not company_input:
            messagebox.showwarning("Input Required", "Please enter or select a company slug")
            return
        
        # Extract company slug from input
        # Input can be either "slug" or "Company Name (slug)"
        if '(' in company_input and ')' in company_input:
            # Extract slug from "Company Name (slug)" format
            company_slug = company_input.split('(')[-1].split(')')[0].strip()
        else:
            # Direct slug input
            company_slug = company_input
            
        def task():
            self.initialize_components()
            self.company.download_selected_company_questions(company_slug)
        self.run_in_thread(task)
        
    def load_company_favorites(self):
        company_input = self.fav_company_slug_var.get().strip()
        if not company_input:
            messagebox.showwarning("Input Required", "Please enter or select a company slug")
            return
        
        # Extract company slug from input
        if '(' in company_input and ')' in company_input:
            company_slug = company_input.split('(')[-1].split(')')[0].strip()
        else:
            company_slug = company_input
            
        def task():
            self.initialize_components()
            favorite_details = self.company.get_company_favorite_slugs(company_slug)
            if favorite_details:
                self.favorites_listbox.delete(0, tk.END)
                self.favorite_data = favorite_details
                for idx, (slug, name) in enumerate(favorite_details, start=1):
                    self.favorites_listbox.insert(tk.END, f"{idx}. {name}")
        self.run_in_thread(task)
        
    def download_favorite_questions(self):
        selection = self.favorites_listbox.curselection()
        if not selection:
            messagebox.showwarning("Selection Required", "Please select a favorite from the list")
            return
        company_input = self.fav_company_slug_var.get().strip()
        if not company_input:
            messagebox.showwarning("Input Required", "Please enter or select a company slug")
            return
        
        # Extract company slug
        if '(' in company_input and ')' in company_input:
            company_slug = company_input.split('(')[-1].split(')')[0].strip()
        else:
            company_slug = company_input
        
        idx = selection[0]
        comp_fav_slug, name = self.favorite_data[idx]
        
        def task():
            self.initialize_components()
            self.company.download_favorite_company_questions(company_slug, comp_fav_slug)
        self.run_in_thread(task)
        
    def download_all_submissions(self):
        def task():
            self.initialize_components()
            self.submission.get_all_submissions()
        self.run_in_thread(task)
        
    def download_question_submissions(self):
        question_input = self.submission_question_id_var.get().strip()
        if not question_input:
            messagebox.showwarning("Input Required", "Please enter or select a question ID")
            return
        
        # Extract question ID from input
        # Input can be either "123" or "123 - Question Title"
        try:
            if ' - ' in question_input:
                # Extract ID from "ID - Title" format
                question_id = int(question_input.split(' - ')[0].strip())
            else:
                # Direct ID input
                question_id = int(question_input)
        except ValueError:
            messagebox.showerror("Invalid Input", "Question ID must be a number.\nFormat: 123 or select from dropdown")
            return
        
        # Validate it's a positive integer
        if question_id <= 0:
            messagebox.showerror("Invalid Input", "Question ID must be a positive number")
            return
            
        def task():
            self.initialize_components()
            self.submission.get_selected_submissions(question_id=question_id)
        self.run_in_thread(task)
        
    def browse_pdf_path(self):
        path = filedialog.askdirectory(title="Select Directory") or filedialog.askopenfilename(title="Select File")
        if path:
            self.pdf_path_var.set(path)
            
    def convert_to_pdf(self):
        from utils.Config import Config
        from utils.PdfConverter import PdfConverter
        import os
        
        path = self.pdf_path_var.get().strip()
        if not path:
            messagebox.showwarning("Input Required", "Please select a directory or file")
            return
        if not os.path.exists(path):
            messagebox.showerror("Error", "Directory or file doesn't exist")
            return
            
        def task():
            self.initialize_components()
            converter = PdfConverter(
                config=self.config,
                logger=self.logger,
                images_dir=Config.get_images_dir(path))
            if os.path.isdir(path):
                converter.convert_folder(path)
            else:
                converter.convert_single_file(path)
        self.run_in_thread(task)
        
    def get_cache(self):
        key = self.cache_key_entry.get().strip()
        if not key:
            messagebox.showwarning("Input Required", "Please enter a cache key")
            return
        def task():
            self.initialize_components()
            result = self.cache.get(key)
            self.logger.info(f"Cache value for key '{key}': {result}")
            messagebox.showinfo("Cache Value", str(result))
        self.run_in_thread(task)
        
    def delete_cache(self):
        key = self.cache_key_entry.get().strip()
        if not key:
            messagebox.showwarning("Input Required", "Please enter a cache key")
            return
        def task():
            self.initialize_components()
            self.cache.delete(key=key)
            self.logger.info(f"Deleted cache key: {key}")
        self.run_in_thread(task)
        
    def clear_cache(self):
        if messagebox.askyesno("Confirm", "Are you sure you want to clear all cache?"):
            def task():
                self.initialize_components()
                self.cache.clear()
                self.logger.info("Cache cleared")
            self.run_in_thread(task)


def main():
    root = tk.Tk()
    app = LeetcodeScraperGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()

