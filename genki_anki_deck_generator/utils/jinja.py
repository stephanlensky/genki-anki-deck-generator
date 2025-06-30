from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

TEMPLATES_DIR = Path("templates")
ENV = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=select_autoescape())


def render_template(template_path: Path, context: dict[str, Any]) -> str:
    template = ENV.get_template(template_path.as_posix())
    return template.render(context)
