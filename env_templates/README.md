# env_templates

This directory contains Jinja templates for generating .env files.

To generate the files:
```bash
./scripts/gen_env.py
```

Each template file must contain the extension `.env.j2` and results in a corresponding `.env` file in `env/`.

### Changing the output directory

To enable separate sets of API keys, passwords, etc. for different deployments (e.g. test/prod), set the `OUTPUT_DIR` environment variable:

```bash
OUTPUT_DIR=env_prod gen_env.py
```

### Generating random passwords/keys

The `gen_env.py` script provides the `random_b64` Jinja filter.  An example of a Jinja template using this filter is `{{ 16 | random_b64 }}`.  Note that since Base64 converts 3 bytes to 4 output characters, the length argument in the filter will always be rounded up to the nearest multiple of 4.
