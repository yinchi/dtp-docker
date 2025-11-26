#!/usr/bin/env -S uv run --package dtp-docker-env-templates
"""Script to generate .env files from Jinja2 templates.

This script processes all .j2 template files in the TEMPLATE_DIR directory,
renders them using Jinja2, and outputs the resulting .env files to the OUTPUT_DIR directory.
If an output file already exists, the user is prompted before overwriting it.
"""

import base64
import os
import pathlib
import subprocess

import dotenv
import jinja2

dotenv.load_dotenv()

TEMPLATE_DIR = os.environ.get("TEMPLATE_DIR", "env_templates")
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "env")

print("Generating .env files...")

# Find the Git root directory

git_root = subprocess.check_output(["git", "rev-parse", "--show-toplevel"]).strip().decode("utf-8")
git_root = pathlib.Path(git_root).resolve()


def random_b64(len: int) -> str:
    """Generate a random URL-safe base64-encoded string of specified length.

    Note that the length is rounded up to the nearest multiple of 4, since base64 encoding
    works in 4-character groups.

    Args:
        len: Desired length of the output string.

    Returns:
        A random URL-safe base64-encoded string of at least the specified length.
    """
    # Calculate number of 4-character groups needed, rounding up
    n_groups = (len + 3) // 4
    # Each group of four base64 characters requires 3 bytes of input
    n_bytes = n_groups * 3
    random_bytes = os.urandom(n_bytes)
    return base64.urlsafe_b64encode(random_bytes).decode("utf-8")


def main():
    """Main function to generate .env files from templates."""
    templates_path = git_root / TEMPLATE_DIR
    assert templates_path.exists(), f"Templates path does not exist: {templates_path}"

    env_path = git_root / OUTPUT_DIR
    env_path.mkdir(parents=True, exist_ok=True)

    jinja_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(templates_path)),
        autoescape=jinja2.select_autoescape(),
    )

    jinja_env.filters["random_b64"] = random_b64

    for template_file in templates_path.glob("*.j2"):
        output_file = env_path / template_file.stem  # Remove .j2 extension

        # Prompt before overwriting existing files
        if output_file.exists():
            response = input(f"{output_file} already exists. Overwrite? (y/n): ")
            while response.lower() not in ("y", "n"):
                response = input("Please enter 'y' or 'n': ")
            if response.lower() != "y":
                print(f"Skipping {output_file}")
                continue

        template = jinja_env.get_template(template_file.name)
        rendered_content = template.render()

        with open(output_file, "w") as f:
            f.write(rendered_content)

        print(f"Generated {output_file}")


if __name__ == "__main__":
    main()
