"""Check local Microsoft Entra token acquisition without making a model call."""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from envfile import load_env


def main() -> None:
    load_env()
    endpoint = os.environ.get("FOUNDRY_PROJECT_ENDPOINT", "")
    model = os.environ.get("FOUNDRY_MODEL", "")
    if not endpoint or "/api/projects/" not in endpoint:
        raise SystemExit("FOUNDRY_PROJECT_ENDPOINT must look like https://<resource>.services.ai.azure.com/api/projects/<project>")
    if not model:
        raise SystemExit("FOUNDRY_MODEL must be the exact deployed model name")
    try:
        from azure.identity import DefaultAzureCredential
    except ImportError as exc:
        raise SystemExit("Install dependencies first: pip install -r requirements.txt") from exc

    token = DefaultAzureCredential().get_token("https://ai.azure.com/.default")
    print("Entra authentication succeeded.")
    print(f"Project endpoint: {endpoint}")
    print(f"Deployment name: {model}")
    print(f"Token expires in approximately {max(0, token.expires_on - __import__('time').time()) / 60:.0f} minutes.")


if __name__ == "__main__":
    main()
