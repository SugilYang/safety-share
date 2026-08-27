# -*- coding: utf-8 -*-
"""기존에 쓰시던 통합 파이썬 코드를 넣는 자리.

이 파일을 custom_integrate.py 로 복사한 뒤, 아래 integrate() 함수 안에
기존 통합 로직을 옮겨 넣으면 자동화 마지막 단계에서 그대로 실행됩니다.

files      : {"secom": "다운로드된 세콤 엑셀 경로",
              "erp_attendance": "ERP 근태 엑셀 경로",
              "erp_leave": "ERP 휴가 엑셀 경로"}  (config.yaml 의 name 기준)
output_path: 결과를 저장할 전체 경로 (예: C:\\근태자동화\\결과\\통합근태_20260827.xlsx)
"""
import pandas as pd


def integrate(files: dict, output_path: str):
    # ▼▼▼ 여기부터 기존 통합 코드로 교체 ▼▼▼
    secom = pd.read_excel(files["secom"])
    erp = pd.read_excel(files["erp_attendance"])

    # 예시: 사번 기준으로 병합
    # merged = erp.merge(secom, on="사번", how="left")

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        secom.to_excel(writer, sheet_name="세콤출입", index=False)
        erp.to_excel(writer, sheet_name="ERP근태", index=False)
    # ▲▲▲ 여기까지 ▲▲▲
