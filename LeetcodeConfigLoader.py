import os

from LeetcodeConstants import LeetcodeConstants
from LeetcodeUtility import LeetcodeUtility
from LeetcodeConfig import LeetcodeConfig

class LeetcodeConfigLoader:
    def __init__(self):
        pass

    @staticmethod
    def create_base_config_dir():
        base_config_path = os.path.join(LeetcodeConstants.OS_ROOT, ".leetcode-scraper")
        os.makedirs(base_config_path, exist_ok=True)
        return base_config_path


    @staticmethod
    def generate_config():
        LeetcodeUtility.clear()
        base_config_path = LeetcodeConfigLoader.create_base_config_dir()
        config_file_path = os.path.join(base_config_path, "config.json")

        config_found = False
        # Load existing config if available
        if os.path.exists(config_file_path):
            config = LeetcodeConfig.from_json_file(config_file_path)
            config_found = True
        else:
            config = LeetcodeConfig()

        # Prompt user for new config values
        print(f'''
            Leave Blank and press Enter if you don't want to overwrite Previous Values
            Config Save Folder: {config_file_path}
        ''')

        config_prompts = LeetcodeConfig.prompt_from_dataclass()

        # Prompt user for values and retain existing config if no new input is provided
        for key, prompt in config_prompts.items():
            current_value = getattr(config, key, None)

            newprompt = f"Current value: {current_value}\n{prompt}"

            if "T/F" in prompt:
                # For boolean values, use a case-insensitive check for 'T'
                new_value = input(newprompt).strip().upper()
                if new_value:
                    setattr(config, key, new_value == 'T')
            elif "Enter order" in prompt:
                # For preferred_language_order, allow comma-separated values
                new_value = input(newprompt).strip()
                if new_value:
                    setattr(config, key, new_value.split(','))
            elif "count" in prompt:
                new_value = input(newprompt).strip()
                if new_value:
                    setattr(config, key, int(new_value))
            else:
                # For other fields, check if a new value was entered
                new_value = input(newprompt).strip()
                if new_value:
                    setattr(config, key, new_value)

        if not config_found:
            # setting derived values
            config.set_derivative_values()


        # Save the updated configuration to a JSON file
        config.to_json_file(config_file_path)
        print(f"Configuration saved to {config_file_path}")

    @staticmethod
    def load_config():
        config_dir = os.path.join(LeetcodeConstants.OS_ROOT, ".leetcode-scraper")
        config_path = os.path.join(config_dir, "config.json")

        # Check if config file exists
        if not os.path.exists(config_path):
            raise Exception("No config found, please create one")

        return LeetcodeConfig.from_json_file(config_path)