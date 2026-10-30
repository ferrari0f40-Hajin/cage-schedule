import streamlit as st
import pandas as pd
import json
import os
import calendar
import datetime
import re

DATA_FILE = "cage_schedule_data.json"

DEFAULT_SHIFTS = [
    {"code": "10", "ot": 0, "off": 0}, {"code": "10+1", "ot": 1, "off": 0}, {"code": "10+2", "ot": 2, "off": 0}, {"code": "10+3", "ot": 3, "off": 0},
    {"code": "12", "ot": 0, "off": 0}, {"code": "12+1", "ot": 1, "off": 0}, {"code": "12+2", "ot": 2, "off": 0}, {"code": "12+3", "ot": 3, "off": 0},
    {"code": "14", "ot": 0, "off": 0}, {"code": "14+1", "ot": 1, "off": 0}, {"code": "14+2", "ot": 2, "off": 0}, {"code": "14+3", "ot": 3, "off": 0},
    {"code": "16", "ot": 0, "off": 0}, {"code": "16+1", "ot": 1, "off": 0}, {"code": "16+2", "ot": 2, "off": 0}, {"code": "16+3", "ot": 3, "off": 0},
    {"code": "18", "ot": 0, "off": 0}, {"code": "18+1", "ot": 1, "off": 0}, {"code": "18+2", "ot": 2, "off": 0}, {"code": "18+3", "ot": 3, "off": 0},
    {"code": "20", "ot": 0, "off": 0}, {"code": "20+1", "ot": 1, "off": 0}, {"code": "20+2", "ot": 2, "off": 0}, {"code": "20+3", "ot": 3, "off": 0},
    {"code": "OFF", "ot": 0, "off": 1}, {"code": "AL", "ot": 0, "off": 0}, {"code": "PL", "ot": 0, "off": 0}
]

STATIC_HOLIDAYS = {
    1: [1],       # 신정
    3: [1],       # 삼일절
    5: [5],       # 어린이날
    6: [6],       # 현충일
    8: [15],      # 광복절
    10: [3, 9],   # 개천절, 한글날
    12: [25]      # 크리스마스
}

def get_public_holidays(year, custom_holidays_list):
    holidays = set()
    for m, days in STATIC_HOLIDAYS.items():
        for d in days:
            try:
                holidays.add(datetime.date(year, m, d))
            except ValueError:
                pass
                
    if year == 2026:
        holidays.add(datetime.date(2026, 2, 16))
        holidays.add(datetime.date(2026, 2, 17))
        holidays.add(datetime.date(2026, 2, 18))
        holidays.add(datetime.date(2026, 5, 24))
        holidays.add(datetime.date(2026, 9, 24))
        holidays.add(datetime.date(2026, 9, 25))
        holidays.add(datetime.date(2026, 9, 26))

    for h_str in custom_holidays_list:
        try:
            parts = list(map(int, h_str.strip().split("-")))
            if len(parts) == 3 and parts[0] == year:
                holidays.add(datetime.date(parts[0], parts[1], parts[2]))
        except Exception:
            pass
            
    return holidays

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return (
                    data.get("members", ["문석환", "정하진", "이윤원", "황선미"]),
                    data.get("schedule", {}),
                    data.get("shifts", DEFAULT_SHIFTS),
                    data.get("summary", {}),
                    data.get("fixed_holidays", {}),
                    data.get("custom_holidays", [])
                )
        except Exception:
            pass
    return ["문석환", "정하진", "이윤원", "황선미"], {}, DEFAULT_SHIFTS, {}, {}, []

def save_data(members, schedule, shifts, summary, fixed_holidays, custom_holidays):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "members": members, 
            "schedule": schedule, 
            "shifts": shifts, 
            "summary": summary, 
            "fixed_holidays": fixed_holidays,
            "custom_holidays": custom_holidays
        }, f, ensure_ascii=False, indent=2)

def get_ot_for_code(code, shift_types):
    code = str(code).strip()
    for s in shift_types:
        if s["code"] == code:
            return s.get("ot", 0)
    
    base_code = re.split(r'[+-]', code)[0].strip()
    base_ot = 0
    for s in shift_types:
        if s["code"] == base_code:
            base_ot = s.get("ot", 0)
            break
            
    match_plus = re.findall(r'\+(\d+)', code)
    match_minus = re.findall(r'-(\d+)', code)
    
    for p in match_plus:
        base_ot += int(p)
    for m in match_minus:
        base_ot -= int(m)
        
    return base_ot

members, schedule_data, shift_types, summary_data, fixed_holidays_data, custom_holidays_list = load_data()

st.set_page_config(page_title="CAGE 팀 근무스케줄", layout="wide")
st.title("🎰 CAGE 팀 근무스케줄 관리 시스템")

st.sidebar.header("🔐 접속 및 권한 설정")
mode = st.sidebar.radio("모드 선택", ["일반 팀원 (조회 전용)", "관리자 (로그인 필요)"])

is_admin = False
if mode == "관리자 (로그인 필요)":
    admin_pw = st.sidebar.text_input("관리자 비밀번호 입력", type="password")
    if admin_pw == "admin1234":
        is_admin = True
        st.sidebar.success("✅ 관리자 권한 활성화됨")
    elif admin_pw:
        st.sidebar.error("❌ 비밀번호가 틀렸습니다.")

if is_admin:
    st.sidebar.markdown("---")
    st.sidebar.subheader("📅 공휴일 직접 추가 관리")
    st.sidebar.caption("형식: `YYYY-MM-DD` (엔터로 구분)")
    
    custom_holidays_text = st.sidebar.text_area(
        "추가 공휴일 목록", 
        value="\n".join(custom_holidays_list),
        help="예: 2026-11-25"
    )
    
    new_custom_list = [line.strip() for line in custom_holidays_text.split("\n") if line.strip()]
    if new_custom_list != custom_holidays_list:
        custom_holidays_list = new_custom_list
        save_data(members, schedule_data, shift_types, summary_data, fixed_holidays_data, custom_holidays_list)

now = datetime.datetime.now()
col_y, col_m = st.sidebar.columns(2)
with col_y:
    year = st.selectbox("연도", [now.year - 1, now.year, now.year + 1], index=1)
with col_m:
    month = st.selectbox("월", list(range(1, 13)), index=now.month - 1)

_, days_in_month = calendar.monthrange(year, month)
public_holidays = get_public_holidays(year, custom_holidays_list)
days_korean = ["월", "화", "수", "목", "금", "토", "일"]

# 요일에 따른 색상 기호 부여 (토요일: 💙 파란색, 일요일/공휴일: ❤️ 빨간색)
day_cols = []
for d in range(1, days_in_month + 1):
    dt = datetime.date(year, month, d)
    wd = dt.weekday()
    k_day = days_korean[wd]
    if wd == 5:
        day_cols.append(f"{d}({k_day})💙")
    elif wd == 6 or dt in public_holidays:
        day_cols.append(f"{d}({k_day})❤️")
    else:
        day_cols.append(f"{d}({k_day})")

edit_columns = ["NO", "성명", "고정휴일"] + day_cols

st.divider()
st.subheader(f"📅 {year}년 {month}월 근무 스케줄표")

edit_rows = []
for m_idx, member in enumerate(members):
    fh_key = f"{year}-{month}-{m_idx}"
    default_fh = fixed_holidays_data.get(fh_key, "9")
    row_data = [m_idx + 1, member, default_fh]
    
    for d in range(1, days_in_month + 1):
        key = f"{year}-{month}-{m_idx}-{d}"
        code = schedule_data.get(key, "OFF")
        row_data.append(code)
    edit_rows.append(row_data)

edit_df = pd.DataFrame(edit_rows, columns=edit_columns)

if is_admin:
    st.info("💡 **관리자 모드**: 성명, 고정휴일, 스케줄 내용을 직접 수정하거나 **엑셀 내용을 복사(Ctrl+C)하여 붙여넣기(Ctrl+V)** 한 뒤, 하단의 **[💾 전체 변경사항 저장]** 버튼을 누르세요.")
    
    edited_df = st.data_editor(
        edit_df,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        disabled=["NO"]
    )

    if st.button("💾 전체 변경사항 저장", type="primary"):
        updated_members = []
        new_schedule = dict(schedule_data)
        new_fixed_holidays = dict(fixed_holidays_data)

        for row_idx, row in edited_df.iterrows():
            m_name = str(row["성명"]).strip()
            if not m_name or m_name == "nan":
                continue
            
            m_idx = len(updated_members)
            updated_members.append(m_name)
            
            fh_val = str(row["고정휴일"]).strip()
            new_fixed_holidays[f"{year}-{month}-{m_idx}"] = fh_val

            for d in range(1, days_in_month + 1):
                col_name = day_cols[d - 1]
                val = str(row[col_name]).strip()
                if val and val != "nan":
                    key = f"{year}-{month}-{m_idx}-{d}"
                    new_schedule[key] = val

        save_data(updated_members, new_schedule, shift_types, summary_data, new_fixed_holidays, custom_holidays_list)
        st.success("✅ 모든 변경사항이 성공적으로 저장되었습니다!")
        st.rerun()

    st.markdown("---")
    st.subheader("👁️ 현재 적용된 스케줄 및 자동 연산 결과 미리보기")

view_rows = []
for m_idx, member in enumerate(members):
    off_cnt = 0
    ot_sum = 0
    fh_key = f"{year}-{month}-{m_idx}"
    fixed_h = fixed_holidays_data.get(fh_key, "9")
    
    row_data = [m_idx + 1, member, fixed_h]
    
    for d in range(1, days_in_month + 1):
        key = f"{year}-{month}-{m_idx}-{d}"
        code = schedule_data.get(key, "OFF")
        row_data.append(code)
        
        if code.strip().upper() == "OFF":
            off_cnt += 1
        ot_sum += get_ot_for_code(code, shift_types)
        
    row_data.extend([off_cnt, ot_sum])
    view_rows.append(row_data)

view_columns = ["NO", "성명", "고정휴일"] + day_cols + ["휴일수", "O.T 합계"]
view_df = pd.DataFrame(view_rows, columns=view_columns)

def color_coding(val):
    val_str = str(val).strip().upper()
    if val_str == "OFF":
        return 'background-color: #fee2e2; color: #dc2626; font-weight: bold;'
    elif '+' in val_str or '-' in val_str:
        return 'color: #15803d; font-weight: bold;'
    return ''

styled_view_df = view_df.style.map(color_coding, subset=day_cols)
st.dataframe(styled_view_df, use_container_width=True, hide_index=True)

# --- 하단 휴일 및 연차(잔여) 현황 섹션 ---
st.markdown("---")
st.subheader("📌 [휴일 및 연차(잔여) 현황]")

sum_columns = ["NO", "성명", "O.T 합계", "휴일 및 연차(잔여)", "비고"]
sum_rows = []

for m_idx, member in enumerate(members):
    m_ot = 0
    for d in range(1, days_in_month + 1):
        k = f"{year}-{month}-{m_idx}-{d}"
        c = schedule_data.get(k, "OFF")
        m_ot += get_ot_for_code(c, shift_types)
        
    sum_key_val = f"{year}-{month}-{m_idx}"
    saved_val = summary_data.get(sum_key_val, {}).get("val", "연차")
    saved_memo = summary_data.get(sum_key_val, {}).get("memo", "")
    sum_rows.append([m_idx + 1, member, m_ot, saved_val, saved_memo])

sum_df = pd.DataFrame(sum_rows, columns=sum_columns)

if is_admin:
    edited_sum_df = st.data_editor(sum_df, use_container_width=True, hide_index=True, disabled=["NO", "성명", "O.T 합계"])
    if st.button("💾 잔여 현황 저장"):
        for row_idx, row in edited_sum_df.iterrows():
            sum_key_val = f"{year}-{month}-{row_idx}"
            summary_data[sum_key_val] = {
                "val": str(row["휴일 및 연차(잔여)"]),
                "memo": str(row["비고"])
            }
        save_data(members, schedule_data, shift_types, summary_data, fixed_holidays_data, custom_holidays_list)
        st.success("✅ 잔여 현황 및 비고 내용이 저장되었습니다!")
        st.rerun()
else:
    st.info("👀 일반 팀원(조회 전용) 모드입니다. 하단의 잔여 현황 및 비고 내용을 실시간으로 확인하실 수 있습니다.")
    st.dataframe(sum_df, use_container_width=True, hide_index=True)