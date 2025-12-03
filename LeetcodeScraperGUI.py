import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
from logging import Logger, Handler
import sys
import os

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
        self.utilities_tab_index = 4
        
        # Track which lists have been loaded
        self.questions_loaded = False
        self.cards_loaded = False
        self.companies_loaded = False
        self.submissions_loaded = False
        self.cache_keys_loaded = False
        
        # Store all cache keys for filtering
        self.all_cache_keys = []
        
        # Store full lists for filtering comboboxes
        self.all_questions = []
        self.all_cards = []
        self.all_companies = []
        self.all_submission_questions = []
        
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
        elif selected_tab == self.utilities_tab_index:
            # Auto-load cache keys when switching to Utilities tab
            if not self.cache_keys_loaded:
                self.load_cache_keys(show_message=False)
    
    def setup_config_tab(self, parent):
        """Setup configuration tab with all config fields."""
        parent.columnconfigure(0, weight=1)
        
        # Initialize config field variables
        self.config_vars = {}
        self.config_widgets = {}  # Store widget references for dynamic updates
        
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
        
        self.add_checkbox_field(download_frame, "overwrite", "Download again even if the file exists")
        self.add_checkbox_field(download_frame, "download_images", "Download Images")
        self.add_checkbox_field(download_frame, "download_videos", "Download Videos")
        self.add_checkbox_field(download_frame, "include_default_code", "Include Default Code")
        
        ttk.Separator(parent, orient='horizontal').pack(fill='x', pady=10)
        
        # Content Settings
        content_frame = ttk.LabelFrame(parent, text="Content Settings", padding="10")
        content_frame.pack(fill='x', padx=10, pady=5)
        
        # Import language list from Constants
        from utils.Constants import Constants
        available_languages = ["all"] + sorted([lang for lang in Constants.LANG_NAMES.keys() if lang != "all"])
        self.add_multiselect_field(content_frame, "preferred_language_order", 
                                   "Preferred Languages:", available_languages)
        
        self.add_number_field(content_frame, "include_submissions_count", "Number of your code submissions to include:")
        self.add_number_field(content_frame, "include_community_solution_count", "Number of community solutions to include:")
        
        ttk.Separator(parent, orient='horizontal').pack(fill='x', pady=10)
        
        # Image Processing
        image_frame = ttk.LabelFrame(parent, text="Image Processing", padding="10")
        image_frame.pack(fill='x', padx=10, pady=5)
        
        self.add_checkbox_field(image_frame, "extract_gif_frames", "Extract GIF Frames as separate images")
        self.add_checkbox_field(image_frame, "recompress_image", "Recompress images to improve compatibility")
        self.add_checkbox_field(image_frame, "base64_encode_image", "Embed images in HTML insted of linking from the images directory")
        
        ttk.Separator(parent, orient='horizontal').pack(fill='x', pady=10)
        
        # Advanced Settings
        advanced_frame = ttk.LabelFrame(parent, text="Advanced Settings", padding="10")
        advanced_frame.pack(fill='x', padx=10, pady=5)
        
        self.add_number_field(advanced_frame, "threads_count_for_pdf_conversion", "Number of threads to use for PDF conversion:")
        self.add_number_field(advanced_frame, "api_max_failures", "Maximum number of retries for API call failures:")
        self.add_dropdown_field(advanced_frame, "logging_level", "Logging level:", 
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
        self.add_editable_dropdown_field(openai_subframe, "open_ai_model", "Model:", width=30)
        
        # Add callback to fetch models when API key is entered
        api_key_var = self.config_vars.get("open_ai_api_key")
        if api_key_var:
            # Bind to key release event to detect when user finishes typing
            # We need to get the entry widget, not just the variable
            api_key_var.trace_add("write", lambda *args: self.on_openai_key_changed())
        
        # Ollama Settings
        ollama_subframe = ttk.LabelFrame(ai_frame, text="Ollama Settings", padding="5")
        ollama_subframe.pack(fill='x', pady=5)
        self.add_text_field(ollama_subframe, "ollama_url", "URL:")
        self.add_editable_dropdown_field(ollama_subframe, "ollama_model", "Model:", width=30)
        
        # Add callback to fetch models when Ollama URL is entered
        ollama_url_var = self.config_vars.get("ollama_url")
        if ollama_url_var:
            ollama_url_var.trace_add("write", lambda *args: self.on_ollama_url_changed())
        
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
    
    def add_editable_dropdown_field(self, parent, key, label, width=30):
        """Add an editable dropdown field (combobox that allows typing)."""
        frame = ttk.Frame(parent)
        frame.pack(fill='x', pady=2)
        ttk.Label(frame, text=label, width=30, anchor='w').pack(side='left', padx=5)
        var = tk.StringVar()
        combo = ttk.Combobox(frame, textvariable=var, values=[], width=width, state='normal')
        combo.pack(side='left', padx=5)
        self.config_vars[key] = var
        # Store reference to the combobox widget for updating values later
        self.config_widgets[key] = combo
        return combo
    
    def add_multiselect_field(self, parent, key, label, options):
        """Add a multi-select listbox field."""
        frame = ttk.Frame(parent)
        frame.pack(fill='x', pady=2)
        
        # Label and info frame
        label_frame = ttk.Frame(frame)
        label_frame.pack(fill='x')
        ttk.Label(label_frame, text=label, width=30, anchor='w').pack(side='left', padx=5)
        ttk.Label(label_frame, text="(Hold Ctrl/Cmd to select multiple)", 
                 font=('Arial', 8), foreground='gray').pack(side='left', padx=5)
        
        # Listbox with scrollbar
        list_frame = ttk.Frame(frame)
        list_frame.pack(fill='x', padx=35, pady=2)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')
        
        listbox = tk.Listbox(list_frame, selectmode='multiple', height=6, 
                            yscrollcommand=scrollbar.set, exportselection=False)
        listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=listbox.yview)
        
        # Populate listbox
        for option in options:
            listbox.insert(tk.END, option)
        
        # Store reference to listbox (not a var)
        self.config_vars[key] = listbox
        
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
                    elif isinstance(var, tk.Listbox):
                        # Handle multi-select listbox (for preferred_language_order)
                        var.selection_clear(0, tk.END)
                        if isinstance(value, list):
                            for i in range(var.size()):
                                item = var.get(i)
                                if item in value:
                                    var.selection_set(i)
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
                if isinstance(var, tk.BooleanVar):
                    setattr(config, key, bool(var.get()))
                elif isinstance(var, tk.IntVar):
                    setattr(config, key, int(var.get()))
                elif isinstance(var, tk.Listbox):
                    # Handle multi-select listbox (for preferred_language_order)
                    selected_indices = var.curselection()
                    selected_items = [var.get(i) for i in selected_indices]
                    setattr(config, key, selected_items if selected_items else ["all"])
                elif isinstance(var, tk.StringVar):
                    value = var.get()
                    if key == "preferred_language_order":
                        # This shouldn't happen anymore (using listbox), but keep as fallback
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
    
    def on_openai_key_changed(self):
        """Callback when OpenAI API key is changed - fetch available models."""
        api_key = self.config_vars.get("open_ai_api_key")
        if not api_key:
            return
        
        key_value = api_key.get().strip()
        
        # Only fetch if key looks valid (starts with "sk-" and has reasonable length)
        if key_value and key_value.startswith("sk-") and len(key_value) > 20:
            # Debounce - only fetch after user stops typing for 1 second
            if hasattr(self, '_openai_fetch_timer'):
                self.root.after_cancel(self._openai_fetch_timer)
            self._openai_fetch_timer = self.root.after(1000, lambda: self.fetch_openai_models(key_value))
    
    def fetch_openai_models(self, api_key):
        """Fetch available OpenAI models from the API."""
        def task():
            try:
                import requests
                
                self.logger.info("Fetching OpenAI models...")
                
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                
                response = requests.get("https://api.openai.com/v1/models", headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    models = data.get("data", [])
                    
                    # Filter for GPT models and sort them
                    gpt_models = sorted([
                        m["id"] for m in models 
                        if m["id"].startswith(("gpt-", "o1-", "chatgpt-"))
                    ], reverse=True)
                    
                    if gpt_models:
                        # Update the combobox with available models
                        model_combo = self.config_widgets.get("open_ai_model")
                        if model_combo:
                            model_combo['values'] = gpt_models
                            self.logger.info(f"Loaded {len(gpt_models)} OpenAI models")
                            self.status_var.set(f"Loaded {len(gpt_models)} OpenAI models")
                    else:
                        self.logger.warning("No GPT models found in API response")
                elif response.status_code == 401:
                    self.logger.warning("Invalid OpenAI API key")
                else:
                    self.logger.warning(f"Failed to fetch OpenAI models: HTTP {response.status_code}")
                    
            except requests.RequestException as e:
                self.logger.error(f"Error fetching OpenAI models: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error fetching OpenAI models: {e}")
        
        # Run in background thread
        thread = threading.Thread(target=task, daemon=True)
        thread.start()
    
    def on_ollama_url_changed(self):
        """Callback when Ollama URL is changed - fetch available models."""
        url_var = self.config_vars.get("ollama_url")
        if not url_var:
            return
        
        url_value = url_var.get().strip()
        
        # Only fetch if URL looks valid (contains http and localhost or valid domain)
        if url_value and url_value.startswith("http"):
            # Debounce - only fetch after user stops typing for 1 second
            if hasattr(self, '_ollama_fetch_timer'):
                self.root.after_cancel(self._ollama_fetch_timer)
            self._ollama_fetch_timer = self.root.after(1000, lambda: self.fetch_ollama_models(url_value))
    
    def fetch_ollama_models(self, base_url):
        """Fetch available Ollama models from the API."""
        def task():
            try:
                import requests
                
                self.logger.info("Fetching Ollama models...")
                
                # Ollama API endpoint for listing models
                # The base_url might be like "http://localhost:11434/api/generate"
                # We need to extract the base and use the /api/tags endpoint
                if "/api/" in base_url:
                    api_base = base_url.split("/api/")[0]
                else:
                    api_base = base_url.rstrip("/")
                
                tags_url = f"{api_base}/api/tags"
                
                response = requests.get(tags_url, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    models = data.get("models", [])
                    
                    # Extract model names
                    model_names = sorted([m.get("name", m.get("model", "")) for m in models if m.get("name") or m.get("model")])
                    
                    if model_names:
                        # Update the combobox with available models
                        model_combo = self.config_widgets.get("ollama_model")
                        if model_combo:
                            model_combo['values'] = model_names
                            self.logger.info(f"Loaded {len(model_names)} Ollama models")
                            self.status_var.set(f"Loaded {len(model_names)} Ollama models")
                    else:
                        self.logger.warning("No Ollama models found. Make sure Ollama is running and has models installed.")
                else:
                    self.logger.warning(f"Failed to fetch Ollama models: HTTP {response.status_code}")
                    
            except requests.ConnectionError:
                self.logger.warning("Cannot connect to Ollama. Make sure Ollama is running.")
            except requests.Timeout:
                self.logger.warning("Ollama request timed out. Check if Ollama is responsive.")
            except requests.RequestException as e:
                self.logger.error(f"Error fetching Ollama models: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error fetching Ollama models: {e}")
        
        # Run in background thread
        thread = threading.Thread(target=task, daemon=True)
        thread.start()
        
    def setup_questions_tab(self, parent):
        parent.columnconfigure(0, weight=1)
        
        # Questions section
        questions_frame = ttk.LabelFrame(parent, text="Questions", padding="10")
        questions_frame.pack(fill='x', padx=10, pady=10)
        
        # Buttons for all questions operations
        all_questions_frame = ttk.Frame(questions_frame)
        all_questions_frame.pack(pady=5)
        ttk.Button(all_questions_frame, text="Download All Questions", command=self.download_all_questions, width=30).pack(side='left', padx=5)
        ttk.Button(all_questions_frame, text="Check for Missing Downloads", command=self.check_missing_questions, width=30).pack(side='left', padx=5)
        
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
        
        # Add filtering
        self.question_id_var.trace_add('write', lambda *args: self.filter_questions('question_id'))
        
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
        self.question_from_id_var.trace_add('write', lambda *args: self.filter_questions('from_id'))
        
        ttk.Label(range_input_frame, text="To ID:").pack(side='left', padx=5)
        self.question_to_id_var = tk.StringVar()
        self.question_to_id_combo = ttk.Combobox(range_input_frame, textvariable=self.question_to_id_var, width=15)
        self.question_to_id_combo.pack(side='left', padx=5)
        self.question_to_id_combo['values'] = ()  # Will be populated with question list
        self.question_to_id_var.trace_add('write', lambda *args: self.filter_questions('to_id'))
        
        ttk.Button(range_input_frame, text="Download", command=self.download_question_range).pack(side='left', padx=5)
        ttk.Button(range_input_frame, text="Check Missing", command=self.check_question_range).pack(side='left', padx=5)
        
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
                    
                    # Store all questions for filtering
                    self.all_questions = question_list
                    
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
        
        # Buttons for all cards operations
        all_cards_frame = ttk.Frame(cards_frame)
        all_cards_frame.pack(pady=5)
        ttk.Button(all_cards_frame, text="Download All Cards", command=self.download_all_cards, width=30).pack(side='left', padx=5)
        ttk.Button(all_cards_frame, text="Check for Missing Downloads", command=self.check_missing_cards, width=30).pack(side='left', padx=5)
        
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
        
        # Add filtering
        self.card_slug_var.trace_add('write', lambda *args: self.filter_cards())
        
        ttk.Button(card_input_frame, text="Download", command=self.download_card).pack(side='left')
        ttk.Button(card_input_frame, text="Check Missing", command=self.check_missing_card).pack(side='left', padx=5)
        
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
                    
                    # Store all cards for filtering
                    self.all_cards = card_list
                    
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
        
        # Buttons for all company operations
        all_companies_frame = ttk.Frame(parent)
        all_companies_frame.pack(pady=10)
        ttk.Button(all_companies_frame, text="Download All Company Questions", command=self.download_all_companies, width=35).pack(side='left', padx=5)
        ttk.Button(all_companies_frame, text="Check for Missing Downloads", command=self.check_missing_companies, width=35).pack(side='left', padx=5)
        
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
        
        # Add filtering
        self.company_slug_var.trace_add('write', lambda *args: self.filter_companies('company'))
        
        ttk.Button(company_input_frame, text="Download", command=self.download_company_questions).pack(side='left', padx=5)
        ttk.Button(company_input_frame, text="Check Missing", command=self.check_missing_company_questions).pack(side='left', padx=5)
        
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
        
        # Add filtering
        self.fav_company_slug_var.trace_add('write', lambda *args: self.filter_companies('fav_company'))
        
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
                    
                    # Store all companies for filtering
                    self.all_companies = company_list
                    
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
        
        # Add filtering
        self.submission_question_id_var.trace_add('write', lambda *args: self.filter_submission_questions())
        
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
                    
                    # Store all submission questions for filtering
                    self.all_submission_questions = question_list
                    
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
    
    def filter_questions(self, field):
        """Filter questions based on user input in the specified field.
        
        Args:
            field: Which combobox to filter ('question_id', 'from_id', or 'to_id')
        """
        if field == 'question_id':
            typed = self.question_id_var.get().lower()
            combo = self.question_id_combo
        elif field == 'from_id':
            typed = self.question_from_id_var.get().lower()
            combo = self.question_from_id_combo
        elif field == 'to_id':
            typed = self.question_to_id_var.get().lower()
            combo = self.question_to_id_combo
        else:
            return
        
        if not typed:
            # If nothing typed, show all questions
            combo['values'] = self.all_questions
        else:
            # Filter questions that contain the typed text
            filtered = [q for q in self.all_questions if typed in q.lower()]
            combo['values'] = filtered
    
    def filter_cards(self):
        """Filter cards based on user input."""
        typed = self.card_slug_var.get().lower()
        
        if not typed:
            # If nothing typed, show all cards
            self.card_slug_combo['values'] = self.all_cards
        else:
            # Filter cards that contain the typed text
            filtered = [card for card in self.all_cards if typed in card.lower()]
            self.card_slug_combo['values'] = filtered
    
    def filter_companies(self, field):
        """Filter companies based on user input in the specified field.
        
        Args:
            field: Which combobox to filter ('company' or 'fav_company')
        """
        if field == 'company':
            typed = self.company_slug_var.get().lower()
            combo = self.company_slug_combo
        elif field == 'fav_company':
            typed = self.fav_company_slug_var.get().lower()
            combo = self.fav_company_slug_combo
        else:
            return
        
        if not typed:
            # If nothing typed, show all companies
            combo['values'] = self.all_companies
        else:
            # Filter companies that contain the typed text
            filtered = [company for company in self.all_companies if typed in company.lower()]
            combo['values'] = filtered
    
    def filter_submission_questions(self):
        """Filter submission questions based on user input."""
        typed = self.submission_question_id_var.get().lower()
        
        if not typed:
            # If nothing typed, show all questions
            self.submission_question_id_combo['values'] = self.all_submission_questions
        else:
            # Filter questions that contain the typed text
            filtered = [q for q in self.all_submission_questions if typed in q.lower()]
            self.submission_question_id_combo['values'] = filtered
        
    def setup_utilities_tab(self, parent):
        parent.columnconfigure(0, weight=1)
        
        # PDF Conversion
        pdf_frame = ttk.LabelFrame(parent, text="PDF Conversion", padding="10")
        pdf_frame.pack(fill='x', padx=10, pady=5)
        
        # Directory conversion
        dir_label = ttk.Label(pdf_frame, text="Convert Directory:", font=('Arial', 9, 'bold'))
        dir_label.pack(anchor='w', pady=(5, 2))
        
        self.pdf_dir_var = tk.StringVar()
        pdf_dir_frame = ttk.Frame(pdf_frame)
        pdf_dir_frame.pack(pady=5, fill='x')
        ttk.Label(pdf_dir_frame, text="Directory:").pack(side='left', padx=5)
        ttk.Entry(pdf_dir_frame, textvariable=self.pdf_dir_var, width=40).pack(side='left', padx=5, fill='x', expand=True)
        ttk.Button(pdf_dir_frame, text="Browse", command=self.browse_pdf_directory).pack(side='left', padx=5)
        ttk.Button(pdf_dir_frame, text="Convert", command=self.convert_directory_to_pdf).pack(side='left', padx=5)
        ttk.Button(pdf_dir_frame, text="Check", command=self.check_missing_pdfs).pack(side='left', padx=5)
        
        ttk.Separator(pdf_frame, orient='horizontal').pack(fill='x', pady=10)
        
        # Single file conversion
        file_label = ttk.Label(pdf_frame, text="Convert Single File:", font=('Arial', 9, 'bold'))
        file_label.pack(anchor='w', pady=(5, 2))
        
        self.pdf_file_var = tk.StringVar()
        pdf_file_frame = ttk.Frame(pdf_frame)
        pdf_file_frame.pack(pady=5, fill='x')
        ttk.Label(pdf_file_frame, text="File:").pack(side='left', padx=5)
        ttk.Entry(pdf_file_frame, textvariable=self.pdf_file_var, width=40).pack(side='left', padx=5, fill='x', expand=True)
        ttk.Button(pdf_file_frame, text="Browse", command=self.browse_pdf_file).pack(side='left', padx=5)
        ttk.Button(pdf_file_frame, text="Convert", command=self.convert_file_to_pdf).pack(side='left', padx=5)
        
        ttk.Separator(parent, orient='horizontal').pack(fill='x', pady=10)
        
        # Cache Management
        cache_frame = ttk.LabelFrame(parent, text="Cache Management", padding="10")
        cache_frame.pack(fill='x', padx=10, pady=5)
        
        cache_input_frame = ttk.Frame(cache_frame)
        cache_input_frame.pack(pady=5, fill='x')
        ttk.Label(cache_input_frame, text="Cache Key:").pack(side='left', padx=5)
        self.cache_key_var = tk.StringVar()
        self.cache_key_combo = ttk.Combobox(cache_input_frame, textvariable=self.cache_key_var, width=40)
        self.cache_key_combo.pack(side='left', padx=5, fill='x', expand=True)
        ttk.Button(cache_input_frame, text="Refresh Keys", command=self.load_cache_keys).pack(side='left', padx=2)
        
        # Bind to filter as user types
        self.cache_key_var.trace_add('write', lambda *args: self.filter_cache_keys())
        
        # Action buttons
        cache_buttons_frame = ttk.Frame(cache_frame)
        cache_buttons_frame.pack(pady=5)
        ttk.Button(cache_buttons_frame, text="Get", command=self.get_cache).pack(side='left', padx=2)
        ttk.Button(cache_buttons_frame, text="Delete", command=self.delete_cache).pack(side='left', padx=2)
        
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
    
    def check_missing_cards(self):
        """Check for cards that haven't been downloaded yet."""
        def task():
            try:
                self.initialize_components()
                
                self.logger.info("Checking for missing cards...")
                self.status_var.set("Checking for missing cards...")
                
                # Get all cards from LeetCode
                all_cards = self.cards.get_cards()
                
                if not all_cards:
                    self.logger.warning("Could not retrieve cards list")
                    messagebox.showwarning("Error", "Could not retrieve cards from LeetCode")
                    return
                
                # Check which cards are downloaded by looking for their directories
                downloaded = []
                not_downloaded = []
                
                for card in all_cards:
                    cards_chapter_dir = os.path.join(self.config.cards_directory, card.slug)
                    index_file = os.path.join(cards_chapter_dir, "index.html")
                    
                    if os.path.exists(index_file):
                        downloaded.append(card)
                    else:
                        not_downloaded.append(card)
                
                total = len(all_cards)
                downloaded_count = len(downloaded)
                missing_count = len(not_downloaded)
                
                # Log summary
                self.logger.info(f"Total cards: {total}")
                self.logger.info(f"Downloaded: {downloaded_count}")
                self.logger.info(f"Missing: {missing_count}")
                
                if missing_count == 0:
                    self.status_var.set("All cards downloaded!")
                    messagebox.showinfo("Complete", 
                                      f"All {total} cards are downloaded!\n\n"
                                      f"✓ Downloaded: {downloaded_count}\n"
                                      f"✗ Missing: 0")
                else:
                    # Create a list of missing card slugs
                    missing_slugs = sorted([card.slug for card in not_downloaded])
                    
                    # Log missing slugs
                    self.logger.info("Missing card slugs:")
                    for slug in missing_slugs:
                        self.logger.info(f"  {slug}")
                    
                    self.status_var.set(f"Found {missing_count} missing cards")
                    
                    # Show dialog with missing cards (limit to first 50 for readability)
                    display_slugs = missing_slugs[:50]
                    more_text = f"\n... and {missing_count - 50} more" if missing_count > 50 else ""
                    
                    message = (f"Download Status:\n\n"
                             f"Total cards: {total}\n"
                             f"✓ Downloaded: {downloaded_count}\n"
                             f"✗ Missing: {missing_count}\n\n"
                             f"Missing card slugs:\n{', '.join(display_slugs)}{more_text}\n\n"
                             f"Check the log output for the complete list.")
                    
                    messagebox.showinfo("Missing Cards", message)
                    
            except Exception as e:
                self.logger.error(f"Error checking missing cards: {e}")
                messagebox.showerror("Error", f"Failed to check missing cards: {e}")
        
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
    
    def check_missing_card(self):
        """Check for missing items in a specific card."""
        card_slug = self.card_slug_var.get().strip()
        if not card_slug:
            messagebox.showwarning("Input Required", "Please enter or select a card name")
            return
        
        def task():
            try:
                self.initialize_components()
                
                self.logger.info(f"Checking missing items for card: {card_slug}")
                self.status_var.set(f"Checking card {card_slug}...")
                
                # Validate card exists
                cards = self.cards.get_cards()
                card_slugs = {card.slug for card in cards}
                
                if not cards or card_slug not in card_slugs:
                    self.logger.error(f"Card not found: {card_slug}")
                    messagebox.showerror("Invalid Card", f"Card '{card_slug}' not found")
                    return
                
                # Get chapters with items for this card
                chapters = self.cards.lc.get_chapters_with_items(card_slug)
                
                if not chapters:
                    self.logger.error(f"Could not retrieve chapters for card: {card_slug}")
                    messagebox.showerror("Error", f"Could not retrieve chapters for {card_slug}")
                    return
                
                # Check which items are downloaded
                total_items = 0
                downloaded_items = 0
                missing_items = []
                
                cards_chapter_dir = os.path.join(self.config.cards_directory, card_slug)
                
                for chapter in chapters:
                    chapter_title = chapter.get('title', 'Unknown Chapter')
                    
                    for item in chapter['items']:
                        item_id = item['id']
                        item_title = Util.sanitize_title(item['title'])
                        total_items += 1
                        
                        # Check if item file exists
                        item_file = os.path.join(cards_chapter_dir, Util.qhtml(item_id, item_title))
                        
                        if os.path.exists(item_file):
                            downloaded_items += 1
                        else:
                            missing_items.append((item_id, item_title, chapter_title))
                
                missing_count = len(missing_items)
                
                # Log summary
                self.logger.info(f"Card '{card_slug}' check complete:")
                self.logger.info(f"  Total items: {total_items}")
                self.logger.info(f"  Downloaded: {downloaded_items}")
                self.logger.info(f"  Missing: {missing_count}")
                
                if missing_count > 0:
                    self.logger.info("Missing items:")
                    for item_id, title, chapter in missing_items[:30]:  # Log first 30
                        self.logger.info(f"  {item_id} - {title} (Chapter: {chapter})")
                    if missing_count > 30:
                        self.logger.info(f"  ... and {missing_count - 30} more")
                
                # Create message
                if missing_count == 0:
                    self.status_var.set(f"All items for card {card_slug} downloaded!")
                    message = (f"Card Check Complete!\n\n"
                             f"Card: {card_slug}\n"
                             f"Total items: {total_items}\n"
                             f"✓ All items are downloaded!")
                else:
                    self.status_var.set(f"Found {missing_count} missing items for {card_slug}")
                    
                    # Show first 10 missing items
                    display_items = missing_items[:10]
                    display_list = '\n'.join([f"{item_id} - {title}\n  (Chapter: {chap})" for item_id, title, chap in display_items])
                    more_text = f"\n... and {missing_count - 10} more" if missing_count > 10 else ""
                    
                    message = (f"Card Check: {card_slug}\n\n"
                             f"Total items: {total_items}\n"
                             f"✓ Downloaded: {downloaded_items}\n"
                             f"✗ Missing: {missing_count}\n\n"
                             f"Missing items:\n{display_list}{more_text}\n\n"
                             f"Check the log for the complete list.")
                
                messagebox.showinfo("Card Check Complete", message)
                
            except Exception as e:
                self.logger.error(f"Error checking card items: {e}")
                messagebox.showerror("Error", f"Failed to check card items: {e}")
        
        self.run_in_thread(task)
        
    def download_all_questions(self):
        def task():
            self.initialize_components()
            self.qued.download_all_questions()
        self.run_in_thread(task)
    
    def check_missing_questions(self):
        """Check for questions that haven't been downloaded yet."""
        def task():
            try:
                self.initialize_components()
                
                self.logger.info("Checking for missing questions...")
                self.status_var.set("Checking for missing questions...")
                
                # Get all questions from LeetCode
                all_questions = self.qued.lc.get_all_questions()
                
                if not all_questions:
                    self.logger.warning("Could not retrieve questions list")
                    messagebox.showwarning("Error", "Could not retrieve questions from LeetCode")
                    return
                
                # Filter to find which ones are not downloaded
                not_downloaded, downloaded = self.qued.filter_out_downloaded(all_questions)
                
                total = len(all_questions)
                downloaded_count = len(downloaded)
                missing_count = len(not_downloaded)
                
                # Log summary
                self.logger.info(f"Total questions: {total}")
                self.logger.info(f"Downloaded: {downloaded_count}")
                self.logger.info(f"Missing: {missing_count}")
                
                if missing_count == 0:
                    self.status_var.set("All questions downloaded!")
                    messagebox.showinfo("Complete", 
                                      f"All {total} questions are downloaded!\n\n"
                                      f"✓ Downloaded: {downloaded_count}\n"
                                      f"✗ Missing: 0")
                else:
                    # Create a list of missing question IDs
                    missing_ids = sorted([int(q.id) for q in not_downloaded])
                    
                    # Log missing IDs
                    self.logger.info("Missing question IDs:")
                    for qid in missing_ids:
                        self.logger.info(f"  {qid}")
                    
                    # Create ranges for better readability
                    ranges = self.create_id_ranges(missing_ids)
                    ranges_str = ", ".join(ranges)
                    
                    self.status_var.set(f"Found {missing_count} missing questions")
                    
                    # Show dialog with missing questions
                    message = (f"Download Status:\n\n"
                             f"Total questions: {total}\n"
                             f"✓ Downloaded: {downloaded_count}\n"
                             f"✗ Missing: {missing_count}\n\n"
                             f"Missing question IDs:\n{ranges_str}\n\n"
                             f"Check the log output for the complete list.")
                    
                    messagebox.showinfo("Missing Questions", message)
                    
            except Exception as e:
                self.logger.error(f"Error checking missing questions: {e}")
                messagebox.showerror("Error", f"Failed to check missing questions: {e}")
        
        self.run_in_thread(task)
    
    def create_id_ranges(self, ids):
        """Convert a list of IDs into readable ranges (e.g., [1,2,3,5,6,7] -> ['1-3', '5-7'])."""
        if not ids:
            return []
        
        ranges = []
        start = ids[0]
        end = ids[0]
        
        for i in range(1, len(ids)):
            if ids[i] == end + 1:
                end = ids[i]
            else:
                if start == end:
                    ranges.append(str(start))
                else:
                    ranges.append(f"{start}-{end}")
                start = ids[i]
                end = ids[i]
        
        # Add the last range
        if start == end:
            ranges.append(str(start))
        else:
            ranges.append(f"{start}-{end}")
        
        return ranges
        
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
    
    def check_question_range(self):
        """Check for missing questions within a specified range."""
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
        
        def task():
            try:
                self.initialize_components()
                
                range_size = to_id - from_id + 1
                self.logger.info(f"Checking range {from_id} to {to_id} ({range_size} questions)...")
                self.status_var.set(f"Checking range {from_id}-{to_id}...")
                
                # Get all questions to validate IDs exist
                all_questions = self.qued.lc.get_all_questions()
                all_question_ids = {int(q.id): q for q in all_questions}
                
                # Check each question in the range
                downloaded = []
                missing = []
                non_existent = []
                
                for question_id in range(from_id, to_id + 1):
                    if question_id not in all_question_ids:
                        non_existent.append(question_id)
                        continue
                    
                    question = all_question_ids[question_id]
                    question_dir = self.qued.get_question_directory(question.id)
                    filepath = os.path.join(question_dir, Util.qhtml(question.id, question.title))
                    
                    if os.path.exists(filepath):
                        downloaded.append(question_id)
                    else:
                        missing.append(question_id)
                
                # Calculate statistics
                downloaded_count = len(downloaded)
                missing_count = len(missing)
                non_existent_count = len(non_existent)
                valid_count = range_size - non_existent_count
                
                # Log summary
                self.logger.info(f"Range check complete for {from_id}-{to_id}:")
                self.logger.info(f"  Total in range: {range_size}")
                self.logger.info(f"  Valid questions: {valid_count}")
                self.logger.info(f"  Downloaded: {downloaded_count}")
                self.logger.info(f"  Missing: {missing_count}")
                self.logger.info(f"  Non-existent: {non_existent_count}")
                
                if missing:
                    self.logger.info("Missing question IDs:")
                    for qid in missing:
                        self.logger.info(f"  {qid}")
                
                # Create ranges for better readability
                if missing:
                    missing_ranges = self.create_id_ranges(missing)
                    missing_ranges_str = ", ".join(missing_ranges)
                else:
                    missing_ranges_str = "None"
                
                if non_existent:
                    non_existent_ranges = self.create_id_ranges(non_existent)
                    non_existent_ranges_str = ", ".join(non_existent_ranges)
                else:
                    non_existent_ranges_str = "None"
                
                # Create message
                if missing_count == 0 and non_existent_count == 0:
                    self.status_var.set(f"All questions in range {from_id}-{to_id} are downloaded!")
                    message = (f"Range Check Complete!\n\n"
                             f"Range: {from_id} to {to_id} ({range_size} questions)\n"
                             f"✓ All {valid_count} valid questions are downloaded!")
                elif missing_count == 0:
                    self.status_var.set(f"All valid questions in range {from_id}-{to_id} are downloaded")
                    message = (f"Range Check Complete!\n\n"
                             f"Range: {from_id} to {to_id} ({range_size} questions)\n"
                             f"✓ Downloaded: {downloaded_count}\n"
                             f"⚠ Non-existent: {non_existent_count}\n\n"
                             f"Non-existent IDs: {non_existent_ranges_str}")
                else:
                    self.status_var.set(f"Found {missing_count} missing questions in range {from_id}-{to_id}")
                    message = (f"Range Check: {from_id} to {to_id}\n\n"
                             f"Total: {range_size} questions\n"
                             f"✓ Downloaded: {downloaded_count}\n"
                             f"✗ Missing: {missing_count}\n"
                             f"⚠ Non-existent: {non_existent_count}\n\n"
                             f"Missing IDs: {missing_ranges_str}\n"
                             f"Non-existent IDs: {non_existent_ranges_str}\n\n"
                             f"Check the log for the complete list.")
                
                messagebox.showinfo("Range Check Complete", message)
                
            except Exception as e:
                self.logger.error(f"Error checking question range: {e}")
                messagebox.showerror("Error", f"Failed to check question range: {e}")
        
        self.run_in_thread(task)
        
    def download_all_companies(self):
        def task():
            self.initialize_components()
            self.company.download_all_company_questions()
        self.run_in_thread(task)
    
    def check_missing_companies(self):
        """Check for company questions that haven't been downloaded yet."""
        def task():
            try:
                self.initialize_components()
                
                self.logger.info("Checking for missing company questions...")
                self.status_var.set("Checking for missing company questions...")
                
                # Get all companies from LeetCode
                all_companies = self.company.get_company_slugs()
                
                if not all_companies:
                    self.logger.warning("Could not retrieve companies list")
                    messagebox.showwarning("Error", "Could not retrieve companies from LeetCode")
                    return
                
                # Check which companies are downloaded by looking for their directories
                downloaded = []
                not_downloaded = []
                
                for company in all_companies:
                    company_dir = os.path.join(self.config.companies_directory, company.slug)
                    index_file = os.path.join(company_dir, "index.html")
                    
                    if os.path.exists(index_file):
                        downloaded.append(company)
                    else:
                        not_downloaded.append(company)
                
                total = len(all_companies)
                downloaded_count = len(downloaded)
                missing_count = len(not_downloaded)
                
                # Log summary
                self.logger.info(f"Total companies: {total}")
                self.logger.info(f"Downloaded: {downloaded_count}")
                self.logger.info(f"Missing: {missing_count}")
                
                if missing_count == 0:
                    self.status_var.set("All company questions downloaded!")
                    messagebox.showinfo("Complete", 
                                      f"All {total} company question sets are downloaded!\n\n"
                                      f"✓ Downloaded: {downloaded_count}\n"
                                      f"✗ Missing: 0")
                else:
                    # Create a list of missing company slugs
                    missing_slugs = sorted([f"{company.name} ({company.slug})" for company in not_downloaded])
                    
                    # Log missing slugs
                    self.logger.info("Missing company question sets:")
                    for slug in missing_slugs:
                        self.logger.info(f"  {slug}")
                    
                    self.status_var.set(f"Found {missing_count} missing companies")
                    
                    # Show dialog with missing companies (limit to first 30 for readability)
                    display_slugs = missing_slugs[:30]
                    more_text = f"\n... and {missing_count - 30} more" if missing_count > 30 else ""
                    
                    message = (f"Download Status:\n\n"
                             f"Total companies: {total}\n"
                             f"✓ Downloaded: {downloaded_count}\n"
                             f"✗ Missing: {missing_count}\n\n"
                             f"Missing companies:\n" + '\n'.join(display_slugs) + more_text + "\n\n"
                             f"Check the log output for the complete list.")
                    
                    messagebox.showinfo("Missing Companies", message)
                    
            except Exception as e:
                self.logger.error(f"Error checking missing companies: {e}")
                messagebox.showerror("Error", f"Failed to check missing companies: {e}")
        
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
    
    def check_missing_company_questions(self):
        """Check for missing downloads for a specific company."""
        company_input = self.company_slug_var.get().strip()
        if not company_input:
            messagebox.showwarning("Input Required", "Please enter or select a company slug")
            return
        
        # Extract company slug from input
        # Input can be either "slug" or "Company Name (slug)"
        if '(' in company_input and ')' in company_input:
            # Extract slug from "Company Name (slug)" format
            company_slug = company_input.split('(')[-1].split(')')[0].strip()
            company_name = company_input.split('(')[0].strip()
        else:
            # Direct slug input
            company_slug = company_input
            company_name = company_slug
        
        def task():
            try:
                self.initialize_components()
                
                self.logger.info(f"Checking missing questions for company: {company_slug}")
                self.status_var.set(f"Checking {company_slug}...")
                
                # Validate company exists
                companies = self.company.get_company_slugs()
                company_slugs = {company.slug for company in companies}
                
                if not companies or company_slug not in company_slugs:
                    self.logger.error(f"Company not valid: {company_slug}")
                    messagebox.showerror("Invalid Company", f"Company '{company_slug}' not found")
                    return
                
                # Get company question data
                favorite_details = self.company.get_company_question_data(company_slug)
                
                if not favorite_details:
                    self.logger.error(f"Could not retrieve questions for company: {company_slug}")
                    messagebox.showerror("Error", f"Could not retrieve questions for {company_slug}")
                    return
                
                # Check which questions are downloaded
                total_questions = 0
                downloaded_questions = 0
                missing_questions = []
                
                company_dir = os.path.join(self.config.companies_directory, company_slug)
                
                for favorite_slug, (display_name, questions) in favorite_details.items():
                    fav_dir = os.path.join(company_dir, favorite_slug)
                    
                    for question in questions:
                        total_questions += 1
                        
                        # Check if question file exists
                        question_file = os.path.join(fav_dir, Util.qhtml(question.id, question.title))
                        
                        if os.path.exists(question_file):
                            downloaded_questions += 1
                        else:
                            missing_questions.append((question.id, question.title, display_name))
                
                missing_count = len(missing_questions)
                
                # Log summary
                self.logger.info(f"Company '{company_slug}' check complete:")
                self.logger.info(f"  Total questions: {total_questions}")
                self.logger.info(f"  Downloaded: {downloaded_questions}")
                self.logger.info(f"  Missing: {missing_count}")
                
                if missing_count > 0:
                    self.logger.info("Missing questions:")
                    for qid, title, category in missing_questions[:50]:  # Log first 50
                        self.logger.info(f"  {qid} - {title} (Category: {category})")
                    if missing_count > 50:
                        self.logger.info(f"  ... and {missing_count - 50} more")
                
                # Create message
                if missing_count == 0:
                    self.status_var.set(f"All questions for {company_slug} downloaded!")
                    message = (f"Company Check Complete!\n\n"
                             f"Company: {company_name}\n"
                             f"Total questions: {total_questions}\n"
                             f"✓ All questions are downloaded!")
                else:
                    self.status_var.set(f"Found {missing_count} missing questions for {company_slug}")
                    
                    # Show first 15 missing questions
                    display_questions = missing_questions[:15]
                    display_list = '\n'.join([f"{qid} - {title} ({cat})" for qid, title, cat in display_questions])
                    more_text = f"\n... and {missing_count - 15} more" if missing_count > 15 else ""
                    
                    message = (f"Company Check: {company_name}\n\n"
                             f"Total questions: {total_questions}\n"
                             f"✓ Downloaded: {downloaded_questions}\n"
                             f"✗ Missing: {missing_count}\n\n"
                             f"Missing questions:\n{display_list}{more_text}\n\n"
                             f"Check the log for the complete list.")
                
                messagebox.showinfo("Company Check Complete", message)
                
            except Exception as e:
                self.logger.error(f"Error checking company questions: {e}")
                messagebox.showerror("Error", f"Failed to check company questions: {e}")
        
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
        
    def browse_pdf_directory(self):
        """Browse for a directory to convert."""
        directory = filedialog.askdirectory(title="Select Directory to Convert")
        if directory:
            self.pdf_dir_var.set(directory)
    
    def browse_pdf_file(self):
        """Browse for a single file to convert."""
        file = filedialog.askopenfilename(
            title="Select File to Convert",
            filetypes=[
                ("HTML files", "*.html *.htm"),
                ("All files", "*.*")
            ]
        )
        if file:
            self.pdf_file_var.set(file)
            
    def convert_directory_to_pdf(self):
        """Convert all files in a directory to PDF."""
        from utils.Config import Config
        from utils.PdfConverter import PdfConverter
        import os
        
        path = self.pdf_dir_var.get().strip()
        if not path:
            messagebox.showwarning("Input Required", "Please select a directory")
            return
        if not os.path.exists(path):
            messagebox.showerror("Error", "Directory doesn't exist")
            return
        if not os.path.isdir(path):
            messagebox.showerror("Error", "Selected path is not a directory")
            return
            
        def task():
            self.initialize_components()
            converter = PdfConverter(
                config=self.config,
                logger=self.logger,
                images_dir=Config.get_images_dir(path))
            converter.convert_folder(path)
        self.run_in_thread(task)
    
    def check_missing_pdfs(self):
        """Check for HTML files that haven't been converted to PDF."""
        path = self.pdf_dir_var.get().strip()
        if not path:
            messagebox.showwarning("Input Required", "Please select a directory")
            return
        if not os.path.exists(path):
            messagebox.showerror("Error", "Directory doesn't exist")
            return
        if not os.path.isdir(path):
            messagebox.showerror("Error", "Selected path is not a directory")
            return
        
        def task():
            try:
                self.logger.info(f"Checking for missing PDFs in: {path}")
                self.status_var.set("Checking for missing PDFs...")
                
                # Find all HTML files in the directory and subdirectories
                html_files = []
                for root, dirs, files in os.walk(path):
                    for file in files:
                        if file.endswith('.html') or file.endswith('.htm'):
                            html_files.append(os.path.join(root, file))
                
                if not html_files:
                    self.logger.info("No HTML files found in directory")
                    self.status_var.set("No HTML files found")
                    messagebox.showinfo("No HTML Files", "No HTML files found in the selected directory")
                    return
                
                # Check which HTML files have corresponding PDFs
                missing_pdfs = []
                existing_pdfs = []
                
                for html_file in html_files:
                    # Get the expected PDF path
                    pdf_file = os.path.splitext(html_file)[0] + '.pdf'
                    
                    # Check if in pdf subdirectory (common pattern)
                    html_dir = os.path.dirname(html_file)
                    html_name = os.path.basename(html_file)
                    pdf_subdir = os.path.join(html_dir, 'pdf', os.path.splitext(html_name)[0] + '.pdf')
                    
                    # Check both possible locations
                    if os.path.exists(pdf_file) or os.path.exists(pdf_subdir):
                        existing_pdfs.append(html_file)
                    else:
                        missing_pdfs.append(html_file)
                
                # Calculate statistics
                total = len(html_files)
                converted = len(existing_pdfs)
                missing = len(missing_pdfs)
                
                # Log summary
                self.logger.info(f"PDF Conversion Check Complete:")
                self.logger.info(f"  Total HTML files: {total}")
                self.logger.info(f"  Already converted: {converted}")
                self.logger.info(f"  Missing PDFs: {missing}")
                
                if missing > 0:
                    self.logger.info("HTML files missing PDFs:")
                    for html_file in missing_pdfs[:50]:  # Log first 50
                        rel_path = os.path.relpath(html_file, path)
                        self.logger.info(f"  {rel_path}")
                    if missing > 50:
                        self.logger.info(f"  ... and {missing - 50} more")
                
                # Create message
                if missing == 0:
                    self.status_var.set("All HTML files have been converted!")
                    message = (f"PDF Conversion Check Complete!\n\n"
                             f"Directory: {os.path.basename(path)}\n"
                             f"Total HTML files: {total}\n"
                             f"✓ All files have been converted to PDF!")
                else:
                    self.status_var.set(f"Found {missing} HTML files without PDFs")
                    
                    # Show first 20 missing files
                    display_files = missing_pdfs[:20]
                    display_list = '\n'.join([os.path.relpath(f, path) for f in display_files])
                    more_text = f"\n... and {missing - 20} more" if missing > 20 else ""
                    
                    message = (f"PDF Conversion Check\n\n"
                             f"Directory: {os.path.basename(path)}\n"
                             f"Total HTML files: {total}\n"
                             f"✓ Converted: {converted}\n"
                             f"✗ Missing PDFs: {missing}\n\n"
                             f"Files without PDFs:\n{display_list}{more_text}\n\n"
                             f"Check the log for the complete list.")
                
                messagebox.showinfo("PDF Check Complete", message)
                
            except Exception as e:
                self.logger.error(f"Error checking missing PDFs: {e}")
                messagebox.showerror("Error", f"Failed to check missing PDFs: {e}")
        
        self.run_in_thread(task)
    
    def convert_file_to_pdf(self):
        """Convert a single file to PDF."""
        from utils.Config import Config
        from utils.PdfConverter import PdfConverter
        import os
        
        path = self.pdf_file_var.get().strip()
        if not path:
            messagebox.showwarning("Input Required", "Please select a file")
            return
        if not os.path.exists(path):
            messagebox.showerror("Error", "File doesn't exist")
            return
        if not os.path.isfile(path):
            messagebox.showerror("Error", "Selected path is not a file")
            return
            
        def task():
            self.initialize_components()
            converter = PdfConverter(
                config=self.config,
                logger=self.logger,
                images_dir=Config.get_images_dir(path))
            converter.convert_single_file(path)
        self.run_in_thread(task)
        
    def load_cache_keys(self, show_message=True):
        """Load all cache keys from diskcache."""
        def task():
            try:
                self.initialize_components()
                
                # Get all keys from the cache
                keys = sorted(list(self.cache.iterkeys()))
                
                if keys:
                    # Store all keys for filtering
                    self.all_cache_keys = keys
                    
                    # Update combobox values
                    self.cache_key_combo['values'] = keys
                    
                    self.cache_keys_loaded = True
                    self.logger.info(f"Loaded {len(keys)} cache keys")
                    self.status_var.set(f"Loaded {len(keys)} cache keys")
                    if show_message:
                        messagebox.showinfo("Success", f"Loaded {len(keys)} cache keys")
                else:
                    self.all_cache_keys = []
                    self.cache_key_combo['values'] = []
                    self.cache_keys_loaded = True
                    self.logger.info("No cache keys found")
                    self.status_var.set("No cache keys found")
                    if show_message:
                        messagebox.showinfo("Info", "No cache keys found")
            except Exception as e:
                self.logger.error(f"Failed to load cache keys: {e}")
                self.status_var.set("Failed to load cache keys")
                if show_message:
                    messagebox.showerror("Error", f"Failed to load cache keys: {e}")
        
        self.run_in_thread(task)
    
    def filter_cache_keys(self):
        """Filter cache keys based on what user types."""
        typed = self.cache_key_var.get().lower()
        
        if not typed:
            # If nothing typed, show all keys
            self.cache_key_combo['values'] = self.all_cache_keys
        else:
            # Filter keys that contain the typed text
            filtered = [key for key in self.all_cache_keys if typed in key.lower()]
            self.cache_key_combo['values'] = filtered
    
    def get_cache(self):
        key = self.cache_key_var.get().strip()
        if not key:
            messagebox.showwarning("Input Required", "Please select a cache key")
            return
        def task():
            self.initialize_components()
            result = self.cache.get(key)
            self.logger.info(f"Cache value for key '{key}': {result}")
            messagebox.showinfo("Cache Value", str(result))
        self.run_in_thread(task)
        
    def delete_cache(self):
        key = self.cache_key_var.get().strip()
        if not key:
            messagebox.showwarning("Input Required", "Please select a cache key")
            return
        def task():
            self.initialize_components()
            self.cache.delete(key=key)
            self.logger.info(f"Deleted cache key: {key}")
            # Refresh the cache keys list after deletion
            self.cache_keys_loaded = False
            self.load_cache_keys(show_message=False)
        self.run_in_thread(task)
        
    def clear_cache(self):
        if messagebox.askyesno("Confirm", "Are you sure you want to clear all cache?"):
            def task():
                self.initialize_components()
                self.cache.clear()
                self.logger.info("Cache cleared")
                # Refresh the cache keys list after clearing
                self.cache_keys_loaded = False
                self.load_cache_keys(show_message=False)
            self.run_in_thread(task)


def main():
    root = tk.Tk()
    app = LeetcodeScraperGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()

