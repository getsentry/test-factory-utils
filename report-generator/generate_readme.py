import click
from report_generator import main


# TODO really ugly hack try to fix!!!!
#    see if we can get generate_readme to be a subcommand of main that does *NOT* need all required arguments of
#    main to be passed in
def generate_readme():
    print("Generating README.md")

    with open("README-template.md") as f:
        content = f.read()
    ctx = click.Context(main)
    ctx.terminal_width = 80
    cli_help = ctx.get_help()
    content = content.format(cli_help=cli_help)
    with open("README.md", "w") as f:
        f.write(content)


if __name__ == "__main__":
    generate_readme()
