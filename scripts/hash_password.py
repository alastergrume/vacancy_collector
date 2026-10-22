"""Хеш пароля для AUTH_ADMIN_PASSWORD_HASH: python scripts/hash_password.py"""
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from web.security import hash_password  # noqa: E402

if __name__ == "__main__":
    pwd = sys.argv[1] if len(sys.argv) > 1 else getpass.getpass("Пароль: ")
    if len(pwd) < 10:
        sys.exit("Пароль должен быть не короче 10 символов")
    print(hash_password(pwd))
