
from click import get_current_context


def generate_readme():
    with open("README-template.md") as f:
        content = f.read()
    with open("settings-example.yaml") as f:
        settings_example = f.read()

    ctx = get_current_context()
    ctx.terminal_width = 80
    cli_help = ctx.get_help()
    content = content.format(cli_help=cli_help, settings_example=settings_example)
    with open("README.md", "w") as f:
        f.write(content)
