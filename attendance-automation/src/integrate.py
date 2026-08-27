"""다운로드된 엑셀 파일들을 하나로 통합.

동작 방식:
  1. 프로젝트 루트에 custom_integrate.py 가 있으면 → 그 안의
     integrate(files: dict[str, str], output_path: str) 함수를 호출한다.
     (기존에 쓰시던 통합 파이썬 코드를 이 파일에 넣으면 그대로 사용됨)
  2. 없으면 → 기본 통합: 소스별 시트로 합본 + 요약 시트 생성.

files 인자 예시:
  {"secom": "C:\\...\\세콤_출입기록_20260827.xlsx",
   "erp_attendance": "C:\\...\\근태현황.xlsx"}
"""
import glob
import importlib.util
import sys
from pathlib import Path

import pandas as pd

from .config import substitute
from .logger import get_logger

log = get_logger()
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _latest_file(download_dir: str, pattern: str) -> str | None:
    matches = glob.glob(str(Path(download_dir) / pattern))
    if not matches:
        return None
    return max(matches, key=lambda f: Path(f).stat().st_mtime)


def collect_files(cfg: dict) -> dict:
    """소스별 expect_file_pattern 에 맞는 최신 파일을 찾는다."""
    files = {}
    for src in cfg["sources"]:
        if not src.get("enabled", True):
            continue
        f = _latest_file(cfg["general"]["download_dir"], src["expect_file_pattern"])
        if f is None:
            log.warning("[%s] 패턴 '%s' 에 맞는 파일이 없습니다.", src["name"], src["expect_file_pattern"])
        else:
            files[src["name"]] = f
            log.info("[%s] 통합 대상: %s", src["name"], f)
    return files


def default_integrate(files: dict, output_path: str):
    """기본 통합: 각 파일을 시트로 넣고, 파일 목록 요약 시트를 추가."""
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        summary_rows = []
        for name, path in files.items():
            df = pd.read_excel(path)
            sheet = name[:31]  # 엑셀 시트명 31자 제한
            df.to_excel(writer, sheet_name=sheet, index=False)
            summary_rows.append({"소스": name, "파일": Path(path).name, "행수": len(df)})
        pd.DataFrame(summary_rows).to_excel(writer, sheet_name="요약", index=False)
    log.info("기본 통합 완료: %s", output_path)


def run(cfg: dict):
    files = collect_files(cfg)
    if not files:
        raise RuntimeError("통합할 파일이 하나도 없습니다. 다운로드 단계를 확인하세요.")

    out_name = substitute(cfg["integrate"]["output_filename"], cfg["_vars"])
    output_path = str(Path(cfg["general"]["output_dir"]) / out_name)

    custom_path = PROJECT_ROOT / "custom_integrate.py"
    if cfg["integrate"].get("use_custom", True) and custom_path.exists():
        log.info("custom_integrate.py 사용")
        spec = importlib.util.spec_from_file_location("custom_integrate", custom_path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["custom_integrate"] = mod
        spec.loader.exec_module(mod)
        mod.integrate(files, output_path)
    else:
        default_integrate(files, output_path)

    log.info("★ 최종 결과: %s", output_path)
    return output_path
