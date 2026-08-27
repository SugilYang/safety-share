"""콘솔 + 파일 로그. 자동 실행 시 문제 원인을 logs/ 폴더에서 확인할 수 있다."""
import logging
from datetime import date
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"


def get_logger(name: str = "attendance") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    LOG_DIR.mkdir(exist_ok=True)
    fh = logging.FileHandler(
        LOG_DIR / f"{date.today():%Y%m%d}.log", encoding="utf-8"
    )
    fh.setFormatter(fmt)
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    logger.addHandler(fh)
    logger.addHandler(sh)
    return logger
