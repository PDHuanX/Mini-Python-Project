from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings:
    def __init__(self):
        self.resources_dir = BASE_DIR / "resources"
        self.logs_dir = BASE_DIR / "logs"
        self.excel_templates_dir = self.resources_dir / "excel_templates"