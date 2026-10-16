"""Verify the active Hummingbot master password without changing any files."""

from getpass import getpass
import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from hummingbot.client.config.config_crypt import (
    ETHKeyFileSecretManger,
    PASSWORD_VERIFICATION_PATH,
    PASSWORD_VERIFICATION_WORD,
)


def validate_password_file(manager: ETHKeyFileSecretManger, verification_path: Path) -> bool:
    encrypted_word = verification_path.read_text(encoding="utf-8").strip()
    try:
        decrypted_word = manager.decrypt_secret_value(PASSWORD_VERIFICATION_WORD, encrypted_word)
        return decrypted_word == PASSWORD_VERIFICATION_WORD
    except ValueError:
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify a Hummingbot password without changing files.")
    parser.add_argument(
        "--verification-file",
        type=Path,
        default=PASSWORD_VERIFICATION_PATH,
        help="Verification file to test; defaults to the active Hummingbot file.",
    )
    args = parser.parse_args()
    password = getpass("Masukkan password utama Hummingbot: ")
    manager = ETHKeyFileSecretManger(password)
    if validate_password_file(manager, args.verification_file):
        print(f"VALID: password cocok dengan {args.verification_file}")
        return 0
    print(f"INVALID: password tidak cocok dengan {args.verification_file}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
