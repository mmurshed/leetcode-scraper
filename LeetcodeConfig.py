import os
import json

class LeetcodeConfig:
    def __init__(self):
        pass

    def create_base_config_dir(self):
        base_config_path = os.path.join(OS_ROOT, ".leetcode-scraper")
        os.makedirs(base_config_path, exist_ok=True)
        return base_config_path


    def select_config(self):
        global selected_config
        base_config_path = self.create_base_config_dir()
        print("\nIf you are creating a new config, Please select 1 in Main Menu to setup the new config\n")

        if len(os.listdir(base_config_path)) > 0:
            for configs in os.listdir(base_config_path):
                if ".json" in configs:
                    print(configs)
            selected_config = input(
                "\nSelect a config or Enter a number to create a new config: ") or "0"


    def generate_config(self):
        clear()
        base_config_path = self.create_base_config_dir()
        config_file_path = os.path.join(base_config_path, f"config_{selected_config}.json")
        print(f'''
            Leave Blank and press Enter if you don't want to overwrite Previous Values
            Config Save Folder: {config_file_path}
        ''')

        # Try to load existing config, or initialize empty config if it doesn't exist
        config = DEFAULT_CONFIG
        try:
            config = self.load_config_dict()
        except Exception:
            print('''
                Config doesn't exist, creating a new one.
                Enter the paths for your config:
            ''')

        # Default configuration keys and their prompts
        config_prompts = {
            "leetcode_cookie": "Enter the LEETCODE_SESSION Cookie Value: ",
            "cards_url_path": "Enter Cards URL Save Path: ",
            "questions_url_path": "Enter Questions URL Save Path: ",
            "save_path": "Enter Save Path: ",
            "company_tag_save_path": "Enter Company Tag Save Path: ",
            "cache_data": "Cache temporary data files locally T/F? (T/F): ",
            "force_download": "Download again even if the file exists T/F? (T/F): ",
            "preferred_language_order": "Enter order of the preferred solution language (all or a command separate list of languages c, cpp, csharp, java, python3, javascript, typescript, golang): ",
            "include_submissions_count": "How many of your own submissions should be incldued (0 for none, a large integer for all): ",
            "include_default_code": "Include default code section? (T/F): ",
            "convert_to_pdf": "Convert to pdf? (T/F): "
        }

        # Prompt user for values and retain existing config if no new input is provided
        for key, prompt in config_prompts.items():
            if "T/F" in prompt:
                config[key] = bool(input(prompt) == 'T') if input(prompt) else config.get(key, False)
            else:
                config[key] = input(prompt) or config.get(key, "")

        # Write config to JSON file
        with open(config_file_path, "w") as config_file:
            json.dump(config, config_file, indent=4)

    def load_default_config(self):
        config_path = os.path.join(get_script_dir(), "defaultconfig.json")

        # Check if config file exists
        if not os.path.exists(config_path):
            raise Exception("Default config not found.")

        # Load the JSON config file
        with open(config_path, "r") as config_file:
            config = json.load(config_file)

        return config

    def load_config_dict(self):
        global selected_config
        config_dir = os.path.join(OS_ROOT, ".leetcode-scraper")
        config_path = os.path.join(config_dir, f"config_{selected_config}.json")

        # Check if config file exists
        if not os.path.exists(config_path):
            raise Exception("No config found, please create one")

        # Load the JSON config file
        with open(config_path, "r") as config_file:
            config = json.load(config_file)

        # Use the default config for missing fields
        for key in DEFAULT_CONFIG:
            config[key] = config.get(key, DEFAULT_CONFIG[key])

        return config

    def load_config(self, config = None):
        if not config:
            config = self.load_config_dict()
        
        # Dynamically create an anonymous class with attributes from config
        config_class = type('Config', (object,), config)
        return config_class()

    def create_headers(self, leetcode_cookie=""):
        headers = DEFAULT_HEADERS
        headers["cookie"] = f"LEETCODE_SESSION={leetcode_cookie}"
        return headers
