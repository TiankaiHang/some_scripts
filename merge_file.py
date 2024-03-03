import os
import glob

import click
import re


@click.group()
def cli():
    pass


@cli.command()
@click.option("--input", "-i", type=click.Path(exists=True), required=True)
def merge_python(input):
    r"""
    the input is the directory of the python files, merge to
    a markdown file for gpt-4-turbo analysis
    """
    python_files = glob.glob(os.path.join(input, "**/*.py"), recursive=True)
    python_files = sorted(python_files)

    with open("gpt-4-turbo.md", "w") as f:
        for file in python_files:
            with open(file, "r") as py:
                f.write(f"The file `{file}` is\n\n```python\n{py.read()}\n```\n\n")



@cli.command()
@click.option("--input", "-i", type=click.Path(exists=True), required=True)
def merge_latex(input):
    r"""
    the input is the file of `main.tex`, replace the `input{}` 
    with the content of the file, save as `merged.tex`

    ```
    python parse_for_gpt.py merge-latex -i cvpr2024/main.tex
    ```
    """

    directory = os.path.dirname(input)
    with open(input, "r") as f:
        content = f.read()
    for line in content.split("\n"):
        pattern = re.compile(r"\\input{(.+?)}")
        match = pattern.search(line)
        if match:
            filename = match.group(1)
            if not filename.endswith(".tex"):
                filename += ".tex"
            filename = os.path.join(directory, filename)
            with open(filename, "r") as f:
                content = content.replace(line, f.read())

    # remove comments (each line starts with %)
    content = "\n".join([line for line in content.split("\n") if not line.strip().startswith("%")])

    with open("merged.tex", "w") as f:
        f.write(content)


if __name__ == "__main__":
    cli()
