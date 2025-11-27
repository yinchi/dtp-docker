#!/usr/bin/env -S uv run
"""Generate missing environment variables in `.env` file based on `.env.template`."""

import pathlib
from base64 import urlsafe_b64encode
from pprint import pprint
from random import randbytes

import dotenv


def main():
    """Generate missing environment variables in `.env` file based on `.env.template`."""
    this_dir = pathlib.Path(__file__).parent

    # Load environment variables from .env file
    dotenv_file = (this_dir / "../.env").resolve()
    values = dotenv.dotenv_values(dotenv_file)
    # print(values)

    template_file = (this_dir / "../.env.template").resolve()
    template_values = dotenv.dotenv_values(template_file)
    # print(template_values)

    missing_keys = set(template_values.keys()) - set(values.keys())
    missing_keys = sorted(missing_keys)
    if not missing_keys:
        print("No missing keys in .env, nothing to do.")
        return

    print("Adding missing keys to .env:")
    pprint(missing_keys)

    # Append missing keys to .env, converting "changeme" to random values
    with open(dotenv_file, "a") as f:
        for key in missing_keys:
            val = template_values[key]
            if val is None:
                val = ""
            if val == "changeme":
                val = urlsafe_b64encode(randbytes(12)).decode("utf-8")
            print(f"{key}={val}", file=f)


if __name__ == "__main__":
    main()
