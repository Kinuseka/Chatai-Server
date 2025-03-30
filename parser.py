from dotenv import load_dotenv
import os, sys
import yaml
from loguru import logger


logger.remove()
logging = logger.bind(name="ServerAI")
logging.add(sys.stdout, colorize=True, format="<green>[ServerAI]</green><yellow>{time}</yellow><level>[{level}]{message}</level>")



class Constants:
    config_default = {
        "AI": {
            "base_url": "https://example.com/v1",
            "instruction_file": "Concise",
            "optimizer_file": "Default",
            "internet_access": True,
            "model": "gpt-4o-mini",
            "temperature": 1.2
        },
        "Chat": {
            "max_history": 6,
            "optimize_memory": False,
            "context": 2,
            "longterm_memory": 10
        },
        "Server": {
            "IP": "127.0.0.1",
            "PORT": 3009,
            "KEY": "UnsecurePassword"
        }
    }

class _ConfigLoader:
    def __init__(self, name="config.yaml") -> None:
        self.name = name
        self.data_template = Constants.config_default
        load_dotenv()

    def self_check(self):
        if not self.base_url:
            raise ValueError(f"{self.base_url} is empty")
        if not self.model:
            raise ValueError(f"{self.model} is empty")

    def load(self):
        "Loads the configuration"
        with open(self.name, "r") as f:
            self.data = yaml.safe_load(f)
        return self
    
    def generate_config(self):
        "Create an empty template of the config"
        with open(self.name, "w") as f:
            yaml.dump(self.data_template, f)
    
    @property
    def base_url(self):
        return self.data["AI"]["base_url"]
    
    @property
    def model(self):
        return self.data["AI"]["model"]
    
    @property
    def internet_access(self):
        return self.data["AI"]["internet_access"]    
    
    @property
    def max_token(self):
        return self.data["AI"]["max_token"]    

    @property
    def max_history(self):
        return int(self.data["Chat"]["max_history"])

    @property
    def key(self):
        return os.getenv("KEY")
    
    @property
    def instructions(self):
        file = self.data["AI"]["instruction_file"] + ".txt"
        return file
    
    @property
    def optimizer(self):
        file = self.data["AI"]["optimizer_file"] + ".txt"
        return file
    
    @property
    def base_optimizer(self):
        base =  self.data["AI"]["base_optimizer"]
        if not self.base_optimizer:
            return self.base_url
        return base

    @property
    def temperature(self):
        return self.data["AI"]["temperature"]

    @property
    def ip(self):
        return self.data["Server"]["IP"]
    
    @property
    def port(self):
        return int(self.data["Server"]["PORT"])
    
    @property
    def optimize_memory(self):
        return self.data["Chat"]["optimize_memory"]
    
    
    @property
    def context(self):
        return self.data["Chat"]["context"]
    
    @property
    def longterm_memory(self):
        return self.data["Chat"]["longterm_memory"]

    def get_instructions(self, optimizer=False):
        if optimizer:
            directory = os.path.join("optimizer", self.optimizer)
            with open(directory, "r",encoding="utf-8") as f:
                return f.read()
        directory = os.path.join("instructions", self.instructions)
        with open(directory, "r", encoding="utf-8") as f:
            return f.read()
    
    def get_information(self):
        version_c = None
        version_s = None
        with open(resource_path("information.txt"), "r") as f:
            for each in f:
                stripped = each.strip()
                if "client_version:" in stripped:
                    version_c = stripped.replace("client_version: ", "")
                if "server_version:" in stripped:
                    version_s = stripped.replace("server_version: ", "")
        return version_c, version_s
    
    @property
    def client_version(self):
        return self.get_information()[0]
    
    @property
    def server_version(self):
        return self.get_information()[1]
    
    @property
    def key_auth(self):
        return self.data["Server"]["KEY"]
    
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

Config = _ConfigLoader()
Config.load()

if __name__ == "__main__":
    Config.generate_config()