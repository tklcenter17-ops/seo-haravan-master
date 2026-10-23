"""Cấu hình ứng dụng và thẩm định biến môi trường."""
from __future__ import annotations

import os
from pathlib import Path
from typing import NamedTuple

from dotenv import load_dotenv

# Tải biến môi trường từ .env nếu có
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class AppConfig(NamedTuple):
    bot_token: str
    owner_id: int
    db_path: Path
    backup_dir: Path
    price_high_threshold_jpy: int
    owner_ids: tuple[int, ...] = ()
    gemini_api_key: str = ""


def load_config() -> AppConfig:
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    raw_owner_id = os.getenv("TELEGRAM_OWNER_ID", "").strip()
    
    owner_ids_list: list[int] = []
    if raw_owner_id:
        for part in raw_owner_id.split(","):
            part_clean = part.strip()
            if part_clean.isdigit():
                try:
                    owner_ids_list.append(int(part_clean))
                except ValueError:
                    pass
    owner_ids = tuple(owner_ids_list)
    owner_id = owner_ids[0] if owner_ids else 0

    raw_db_path = os.getenv("DB_PATH", "data/quet_vault.db").strip()
    db_path = Path(raw_db_path)
    if not db_path.is_absolute():
        db_path = BASE_DIR / db_path

    raw_backup_dir = os.getenv("BACKUP_DIR", "backups").strip()
    backup_dir = Path(raw_backup_dir)
    if not backup_dir.is_absolute():
        backup_dir = BASE_DIR / backup_dir

    try:
        price_high_threshold = int(os.getenv("PRICE_HIGH_THRESHOLD_JPY", "500000"))
    except ValueError:
        price_high_threshold = 500000

    gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()

    return AppConfig(
        bot_token=bot_token,
        owner_id=owner_id,
        db_path=db_path,
        backup_dir=backup_dir,
        price_high_threshold_jpy=price_high_threshold,
        owner_ids=owner_ids,
        gemini_api_key=gemini_api_key,
    )


def save_owner_id_to_env(owner_id: int) -> None:
    """Lưu owner_id vào file .env để cố định quyền sở hữu."""
    env_file = BASE_DIR / ".env"
    lines = []
    found = False
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("TELEGRAM_OWNER_ID="):
                current_val = line.split("=", 1)[1].strip()
                ids = [x.strip() for x in current_val.split(",") if x.strip()]
                if str(owner_id) not in ids:
                    ids.append(str(owner_id))
                lines.append(f"TELEGRAM_OWNER_ID={','.join(ids)}")
                found = True
            else:
                lines.append(line)
    if not found:
        lines.append(f"TELEGRAM_OWNER_ID={owner_id}")
    env_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


