"""설정 로드 + 변수 치환(${SECOM_ID}, ${TODAY} 등)."""
import os
import re
from datetime import date, timedelta
from pathlib import Path

import yaml
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "config.yaml"


def _builtin_vars(days_back: int) -> dict:
    today = date.today()
    return {
        "TODAY": today.strftime("%Y%m%d"),
        "DATE_FROM": (today - timedelta(days=days_back)).strftime("%Y-%m-%d"),
        "DATE_TO": today.strftime("%Y-%m-%d"),
        "DATE_FROM_COMPACT": (today - timedelta(days=days_back)).strftime("%Y%m%d"),
        "DATE_TO_COMPACT": today.strftime("%Y%m%d"),
    }


def substitute(value: str, variables: dict) -> str:
    """문자열 안의 ${이름} 을 환경변수/내장변수로 치환한다."""
    def repl(m):
        key = m.group(1)
        if key in variables:
            return variables[key]
        env = os.getenv(key)
        if env is not None:
            return env
        raise KeyError(
            f"변수 '{key}' 를 찾을 수 없습니다. .env 파일에 {key}=값 을 추가하세요."
        )
    return re.sub(r"\$\{(\w+)\}", repl, value)


def load_config() -> dict:
    load_dotenv(PROJECT_ROOT / ".env")
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"{CONFIG_PATH} 가 없습니다. "
            "config/config.example.yaml 을 복사해 config.yaml 로 만드세요."
        )
    with open(CONFIG_PATH, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    days_back = cfg.get("general", {}).get("days_back", 1)
    cfg["_vars"] = _builtin_vars(days_back)

    for key in ("download_dir", "output_dir"):
        d = Path(cfg["general"][key])
        d.mkdir(parents=True, exist_ok=True)
        cfg["general"][key] = str(d)
    return cfg
