import os
from pathlib import Path

from dotenv import dotenv_values


def _resolve_upwards(file_path: str) -> Path:
    path = Path(file_path)
    if path.is_absolute():
        return path

    matches = []
    for base in [Path.cwd(), *Path.cwd().parents]:
        candidate = base / path
        if candidate.exists():
            matches.append(candidate)

    return matches[-1] if matches else path

def summarize_value(value: str) -> str:
    """Return masked form: ****last4 or boolean string."""
    lower = value.lower()
    if lower in ("true", "false"):
        return lower
    return "****" + value[-4:] if len(value) > 4 else "****" + value

def doublecheck_env(file_path: str):
    """Check environment variables against a .env file and print summaries."""
    resolved_path = _resolve_upwards(file_path)
    if not resolved_path.exists():
        print(f"Did not find file {resolved_path}.")
        print("This is used to double check the key settings for the notebook.")
        print("This is just a check and is not required.\n")
        return

    parsed = dotenv_values(resolved_path)
    for key in parsed.keys():
        current = os.getenv(key)
        if current is not None:
            print(f"{key}={summarize_value(current)}")
        else:
            print(f"{key}=<not set>")


