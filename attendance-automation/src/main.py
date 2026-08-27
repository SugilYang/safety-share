"""근태자동화 전체 실행: 다운로드(세콤 + ERP) → 통합.

실행:  python -m src.main
옵션:  python -m src.main --only secom          특정 소스만 다운로드
       python -m src.main --skip-download      다운로드 생략, 통합만 실행
"""
import argparse
import sys

from . import integrate
from .config import load_config
from .downloaders.client import ClientDownloader
from .downloaders.web import WebDownloader
from .logger import get_logger

log = get_logger()


def run_downloads(cfg: dict, only: str | None = None) -> list[str]:
    failed = []
    for src in cfg["sources"]:
        if not src.get("enabled", True):
            continue
        if only and src["name"] != only:
            continue
        cls = WebDownloader if src["type"] == "web" else ClientDownloader
        try:
            cls(src, cfg["general"], cfg["_vars"]).run()
        except Exception as e:
            log.error("[%s] 다운로드 실패: %s", src["name"], e)
            failed.append(src["name"])
    return failed


def main():
    parser = argparse.ArgumentParser(description="근태자동화")
    parser.add_argument("--only", help="이 소스만 다운로드 (예: secom)")
    parser.add_argument("--skip-download", action="store_true", help="통합만 실행")
    args = parser.parse_args()

    cfg = load_config()
    log.info("========== 근태자동화 시작 ==========")

    failed = []
    if not args.skip_download:
        failed = run_downloads(cfg, only=args.only)

    if args.only and not args.skip_download:
        # 특정 소스만 테스트할 때는 통합 생략
        log.info("--only 모드: 통합 단계 생략")
    else:
        try:
            integrate.run(cfg)
        except Exception as e:
            log.error("통합 실패: %s", e)
            sys.exit(1)

    if failed:
        log.warning("일부 소스 다운로드 실패: %s (통합은 기존 파일로 진행됨)", ", ".join(failed))
        sys.exit(2)
    log.info("========== 근태자동화 정상 종료 ==========")


if __name__ == "__main__":
    main()
