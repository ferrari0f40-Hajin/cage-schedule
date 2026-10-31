import streamlit as st
import pandas as pd
import json
import os
import calendar
import datetime
import re
import streamlit.components.v1 as components
import base64

DATA_FILE = "cage_schedule_data.json"
LOGO_FILE = "logo.png"

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
    1: [1], 3: [1], 5: [5], 6: [6], 8: [15], 10: [3, 9], 12: [25]
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
                    data.get("members", ["문석환과장", "정하진주임", "이윤원사원", "황선미사원"]),
                    data.get("schedule", {}),
                    data.get("shifts", DEFAULT_SHIFTS),
                    data.get("summary", {}),
                    data.get("fixed_holidays", {}),
                    data.get("custom_holidays", [])
                )
        except Exception:
            pass
    return ["문석환과장", "정하진주임", "이윤원사원", "황선미사원"], {}, DEFAULT_SHIFTS, {}, {}, []

def save_data(members, schedule, shifts, summary, fixed_holidays, custom_holidays):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "members": members, "schedule": schedule, "shifts": shifts, 
            "summary": summary, "fixed_holidays": fixed_holidays, "custom_holidays": custom_holidays
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
    for p in match_plus: base_ot += int(p)
    for m in match_minus: base_ot -= int(m)
    return base_ot

members, schedule_data, shift_types, summary_data, fixed_holidays_data, custom_holidays_list = load_data()

st.set_page_config(page_title="CAGE 팀 근무스케줄", layout="wide")

def get_image_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

logo_base64 = get_image_base64(LOGO_FILE)

# --- 상단 로고 및 타이틀 (제작자 정하진 포인트 적용) ---
col_logo, col_title = st.columns([1, 4])
with col_logo:
    if os.path.exists(LOGO_FILE):
        st.image(LOGO_FILE, width=120)
    else:
        st.markdown("🎰 **CAGE LOGO**")
with col_title:
    st.markdown("""
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <h1 style="margin: 0; font-size: 1.8rem;">CAGE 팀 근무스케줄 관리 시스템</h1>
            <span style="background: linear-gradient(135deg, #6366f1, #a855f7); color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.85rem; font-weight: bold; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">✨ Designer. 정하진</span>
        </div>
    """, unsafe_allow_html=True)

st.sidebar.header("🔐 접속 및 권한 설정")
mode = st.sidebar.radio("모드 선택", ["일반 팀원 (조회 전용)", "관리자 (로그인 필요)"])

is_admin = False
if mode == "관리자 (로그인 필요)":
    admin_pw = st.sidebar.text_input("관리자 비밀번호 입력", type="password")
    if admin_pw == "msh1014":
        is_admin = True
        st.sidebar.success("✅ 관리자 권한 활성화됨")
    elif admin_pw:
        st.sidebar.error("❌ 비밀번호가 틀렸습니다.")

now_dt = datetime.datetime.now()
col_y, col_m = st.sidebar.columns(2)
with col_y:
    year = st.selectbox("연도 선택", [now_dt.year - 1, now_dt.year, now_dt.year+1], index=1)
with col_m:
    default_month_idx = now_dt.month - 1 if year == now_dt.year else 0
    month = st.selectbox("월 선택", list(range(1, 13)), index=default_month_idx)

_, days_in_month = calendar.monthrange(year, month)
public_holidays = get_public_holidays(year, custom_holidays_list)
days_korean = ["월", "화", "수", "목", "금", "토", "일"]

# 관리자 엑셀 업로드 및 정밀 파싱 로직
if is_admin:
    st.sidebar.markdown("---")
    st.sidebar.subheader("📅 공휴일 직접 추가 관리")
    custom_holidays_text = st.sidebar.text_area("추가 공휴일 목록 (YYYY-MM-DD)", value="\n".join(custom_holidays_list))
    new_custom_list = [line.strip() for line in custom_holidays_text.split("\n") if line.strip()]
    if new_custom_list != custom_holidays_list:
        custom_holidays_list = new_custom_list
        save_data(members, schedule_data, shift_types, summary_data, fixed_holidays_data, custom_holidays_list)

    st.sidebar.markdown("---")
    st.sidebar.subheader("📂 기존 엑셀 불러오기 (즉시 적용)")
    uploaded_file = st.sidebar.file_uploader("엑셀 파일 업로드", type=["xlsx", "xls"])
    if uploaded_file is not None:
        try:
            xls_file = pd.ExcelFile(uploaded_file)
            s_name = xls_file.sheet_names[0]
            df_up = pd.read_excel(xls_file, sheet_name=s_name, header=None)
            
            p_y, p_m = year, month
            try:
                parts = s_name.split('.')
                if len(parts) == 2:
                    p_y, p_m = int(parts[0]), int(parts[1])
            except:
                pass
                
            date_col_map = {}
            header_row_idx = -1
            for r in range(len(df_up)):
                row_vals = df_up.iloc[r].values
                if 1 in row_vals or '1' in [str(x) for x in row_vals]:
                    for col_idx, val in enumerate(row_vals):
                        try:
                            v_int = int(val)
                            if 1 <= v_int <= 31:
                                date_col_map[v_int] = col_idx
                                header_row_idx = r
                        except:
                            pass
                    if len(date_col_map) > 5:
                        break
            
            new_mems = []
            new_sched = dict(schedule_data)
            new_fh = dict(fixed_holidays_data)
            new_sum = dict(summary_data)
            
            start_row = header_row_idx + 2 if header_row_idx != -1 else 4
            
            for r_idx in range(start_row, len(df_up)):
                row_vals = df_up.iloc[r_idx].values
                no_val = str(row_vals[1]).strip() if len(row_vals) > 1 and pd.notna(row_vals[1]) else ""
                m_name = str(row_vals[2]).strip() if len(row_vals) > 2 and pd.notna(row_vals[2]) else ""
                
                if "* 개인사정" in no_val or no_val == "NO" or "O.T" in str(row_vals[7] if len(row_vals) > 7 else ""):
                    break
                    
                if not no_val.isdigit() or not m_name or m_name == "nan":
                    continue
                    
                new_mems.append(m_name)
                m_idx = len(new_mems) - 1
                
                fh_val = str(row_vals[3]).strip() if len(row_vals) > 3 and pd.notna(row_vals[3]) else "11"
                new_fh[f"{p_y}-{p_m}-{m_idx}"] = fh_val
                
                _, dim_up = calendar.monthrange(p_y, p_m)
                for d in range(1, dim_up + 1):
                    if d in date_col_map:
                        col_idx = date_col_map[d]
                        if col_idx < len(row_vals):
                            val = row_vals[col_idx]
                            if pd.notna(val) and str(val).strip() != "" and str(val).strip() != "nan":
                                new_sched[f"{p_y}-{p_m}-{m_idx}-{d}"] = str(val).strip()

            summary_start = False
            for r_idx in range(start_row, len(df_up)):
                row_vals = df_up.iloc[r_idx].values
                no_val = str(row_vals[1]).strip() if len(row_vals) > 1 and pd.notna(row_vals[1]) else ""
                if no_val == "NO" or "휴일 및 연차" in str(row_vals):
                    summary_start = True
                    continue
                if summary_start and no_val.isdigit():
                    m_idx = int(no_val) - 1
                    s_val = str(row_vals[12]).strip() if len(row_vals) > 12 and pd.notna(row_vals[12]) else "연차"
                    s_memo = str(row_vals[17]).strip() if len(row_vals) > 17 and pd.notna(row_vals[17]) else ""
                    if s_memo == "nan": s_memo = ""
                    new_sum[f"{p_y}-{p_m}-{m_idx}"] = {"val": s_val, "memo": s_memo}

            if new_mems:
                save_data(new_mems, new_sched, shift_types, new_sum, new_fh, custom_holidays_list)
                st.sidebar.success(f"✅ [{p_y}년 {p_m}월] 엑셀 스케줄이 밀림 없이 완벽 적용되었습니다!")
                st.rerun()
        except Exception as e:
            st.sidebar.error(f"❌ 엑셀 불러오기 오류: {e}")

# PDF 인쇄 HTML 생성 함수
def generate_pdf_html(year, month, members, schedule_data, summary_data, fixed_holidays_data, logo_b64):
    _, dim = calendar.monthrange(year, month)
    days_korean_abbr = ["월", "화", "수", "목", "금", "토", "일"]
    
    header_days_1 = ""
    header_days_2 = ""
    for d in range(1, dim + 1):
        dt = datetime.date(year, month, d)
        wd = dt.weekday()
        k_day = days_korean_abbr[wd]
        cls = 'class="sat"' if wd == 5 else ('class="sun"' if wd == 6 or dt in public_holidays else "")
        header_days_1 += f"<th style='width: 25px;'>{d}</th>"
        header_days_2 += f"<th style='width: 25px;' {cls}>{k_day}</th>"

    sched_rows = ""
    for i, m in enumerate(members):
        fh = fixed_holidays_data.get(f"{year}-{month}-{i}", "11")
        off_c, ot_c = 0, 0
        day_tds = ""
        m_parts = re.split(r'[\(\s]+', m.strip())
        m_name, m_rank = m_parts[0], " ".join(m_parts[1:]).replace(")", "") if len(m_parts) > 1 else ""
        name_display = f"{m_name}<br><span class='rank-text'>{m_rank}</span>" if m_rank else m_name
        
        for d in range(1, dim + 1):
            dt = datetime.date(year, month, d)
            wd = dt.weekday()
            c = str(schedule_data.get(f"{year}-{month}-{i}-{d}", "")).strip()
            
            if not c:
                c_html = ""
            elif c.upper() == "OFF":
                off_c += 1
                c_html = f"<span style='color: #dc2626; font-weight: bold;'>{c}</span>"
            elif '+' in c:
                parts = c.split('+')
                c_html = f"{parts[0]}<span style='font-size: 75%; color: #dc2626; font-weight: bold;'>+{parts[1]}</span>"
            elif '-' in c:
                parts = c.split('-')
                c_html = f"{parts[0]}<span style='font-size: 75%; color: #2563eb; font-weight: bold;'>-{parts[1]}</span>"
            else:
                c_html = c
                
            ot_c += get_ot_for_code(c, shift_types)
            day_tds += f"<td style='width: 25px;'>{c_html}</td>"
            
        sched_rows += f"<tr style='height: 24px;'><td>{i+1}</td><td style='font-weight: 700; line-height: 1.1; padding: 2px 0;'>{name_display}</td><td>{fh}</td>{day_tds}<td style='font-weight: 700;'>{off_c}</td><td class='ot-cell'>{ot_c}</td></tr>"

    sum_rows, app_headers, app_tds = "", "", ""
    for i, m in enumerate(members):
        m_ot = sum(get_ot_for_code(schedule_data.get(f"{year}-{month}-{i}-{d}", "OFF"), shift_types) for d in range(1, dim + 1))
        sum_key = f"{year}-{month}-{i}"
        s_val = summary_data.get(sum_key, {}).get("val", "연차")
        s_memo = summary_data.get(sum_key, {}).get("memo", "")
        m_name = re.split(r'[\(\s]+', m.strip())[0]
        sum_rows += f"<tr style='height: 24px;'><td>{i+1}</td><td style='font-weight: 700;'>{m}</td><td class='ot-cell'>{m_ot} 시간</td><td>{s_val}</td><td style='color: #64748b; font-size: 7.5pt;'>{s_memo}</td></tr>"
        app_headers += f"<th>{m_name}</th>"
        app_tds += "<td>(인 / 서명)</td>"

    logo_img_tag = f'<img src="data:image/png;base64,{logo_b64}" style="max-height: 35px; vertical-align: middle;" />' if logo_b64 else '<span style="font-weight: 800; font-size: 12pt;">CAGE</span>'

    return f"""
    <!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"><title>CAGE 팀 근무스케줄 ({year}년 {month}월)</title>
    <style>
        @page {{ size: 297mm 210mm; margin: 0; }}
        body {{ margin: 0; padding: 10px; font-family: 'Malgun Gothic', sans-serif; color: #1e293b; background: #fff; font-size: 7.5pt; }}
        .page {{ width: 275mm; margin: 0 auto; }}
        .header-container {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #0f172a; padding-bottom: 5px; margin-bottom: 8px; }}
        .doc-title {{ font-size: 14pt; font-weight: 800; color: #0f172a; text-align: center; }}
        .table-schedule, .table-summary, .table-approval {{ width: 100%; border-collapse: collapse; text-align: center; margin-bottom: 8px; table-layout: fixed; }}
        .table-schedule th, .table-schedule td, .table-summary th, .table-summary td, .table-approval th, .table-approval td {{ border: 1px solid #b0b8c1; padding: 1px 0px; font-size: 7.5pt; overflow: hidden; white-space: nowrap; }}
        .table-schedule th, .table-summary th {{ background-color: #f1f5f9; font-weight: 700; height: 22px; }}
        .rank-text {{ font-size: 6pt; color: #64748b; font-weight: normal; }}
        .sat {{ color: #2563eb; font-weight: 700; }}
        .sun {{ color: #dc2626; font-weight: 700; }}
        .ot-cell {{ color: #16a34a; font-weight: 700; }}
        .bottom-container {{ display: flex; gap: 12px; align-items: flex-start; margin-top: 4px; }}
        .table-approval td {{ height: 35px; vertical-align: bottom; padding-bottom: 3px; color: #94a3b8; font-size: 7pt; }}
        @media print {{ .no-print {{ display: none !important; }} }}
    </style></head><body>
    <div class="no-print" style="margin-bottom: 10px; text-align: right;"><button onclick="window.print()" style="padding: 6px 14px; background-color: #2563eb; color: #fff; border: none; border-radius: 4px; font-weight: bold; cursor: pointer;">🖨️ PDF 다운로드 / 인쇄하기</button></div>
    <div class="page">
        <div class="header-container"><div style="width: 120px;">{logo_img_tag}</div><div class="doc-title">{year}년 {month}월 근무 스케줄표</div><div style="width: 120px; text-align: right; font-weight: 600; color: #475569; font-size: 8.5pt;">소속: CAGE 팀</div></div>
        <table class="table-schedule"><thead><tr><th rowspan="2" style="width: 26px;">NO</th><th rowspan="2" style="width: 50px;">성명</th><th rowspan="2" style="width: 35px;">고정<br>휴일</th>{header_days_1}<th rowspan="2" style="width: 32px;">휴일수</th><th rowspan="2" style="width: 32px;">O.T</th></tr><tr>{header_days_2}</tr></thead><tbody>{sched_rows}</tbody></table>
        <div class="bottom-container">
            <div style="flex: 1.3;"><div style="font-weight: bold; font-size: 8pt; margin-bottom: 3px;">📌 [휴일 및 연차(잔여) 현황]</div><table class="table-summary"><thead><tr><th style="width: 26px;">NO</th><th>성명</th><th>O.T 합계</th><th>휴일 및 연차(잔여)</th><th>비고</th></tr></thead><tbody>{sum_rows}</tbody></table></div>
            <div style="flex: 1;"><div style="font-weight: bold; font-size: 8pt; margin-bottom: 3px;">✍️ [팀원 확인 결재란]</div><table class="table-approval"><thead><tr>{app_headers}</tr></thead><tbody><tr>{app_tds}</tr></tbody></table></div>
        </div>
    </div></body></html>
    """

st.sidebar.markdown("---")
st.sidebar.subheader("📄 PDF 인쇄 및 저장")
if st.sidebar.button("🖨️ PDF / 인쇄용 문서 생성"):
    pdf_html = generate_pdf_html(year, month, members, schedule_data, summary_data, fixed_holidays_data, logo_base64)
    components.html(pdf_html, height=750, scrolling=True)

day_cols = [f"{d}({days_korean[datetime.date(year, month, d).weekday()]})" for d in range(1, days_in_month + 1)]
edit_columns = ["NO", "성명", "고정휴일"] + day_cols

st.divider()
st.subheader(f"📅 {year}년 {month}월 근무 스케줄표")

edit_rows = []
for m_idx, member in enumerate(members):
    fh_key = f"{year}-{month}-{m_idx}"
    default_fh = fixed_holidays_data.get(fh_key, "11")
    row_data = [m_idx + 1, member, default_fh]
    for d in range(1, days_in_month + 1):
        key = f"{year}-{month}-{m_idx}-{d}"
        row_data.append(schedule_data.get(key, ""))
    edit_rows.append(row_data)

edit_df = pd.DataFrame(edit_rows, columns=edit_columns)

if is_admin:
    st.info("💡 **관리자 모드 (다중 셀 편집 지원)**: 스마트폰이나 PC에서 여러 셀을 드래그하여 선택하거나 엑셀 내용을 복사해서 붙여넣을 수 있습니다. 수정 후 **[💾 전체 변경사항 저장]**을 누르세요.")
    
    # 모바일 다중 선택 및 편집 최적화 데이터 에디터
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
            if not m_name or m_name == "nan": continue
            m_idx = len(updated_members)
            updated_members.append(m_name)
            new_fixed_holidays[f"{year}-{month}-{m_idx}"] = str(row["고정휴일"]).strip()

            for d in range(1, days_in_month + 1):
                val = str(row[day_cols[d - 1]]).strip()
                if val and val != "nan":
                    new_schedule[f"{year}-{month}-{m_idx}-{d}"] = val

        save_data(updated_members, new_schedule, shift_types, summary_data, new_fixed_holidays, custom_holidays_list)
        st.success("✅ 스케줄이 저장되었습니다!")
        st.rerun()

# --- 조회용 스케줄표 (가로 스크롤 및 달 이동 최적화) ---
view_rows = []
for m_idx, member in enumerate(members):
    off_cnt, ot_sum = 0, 0
    row_data = [m_idx + 1, member, fixed_holidays_data.get(f"{year}-{month}-{m_idx}", "11")]
    for d in range(1, days_in_month + 1):
        code = schedule_data.get(f"{year}-{month}-{m_idx}-{d}", "")
        row_data.append(code)
        if str(code).strip().upper() == "OFF": off_cnt += 1
        ot_sum += get_ot_for_code(code, shift_types)
    row_data.extend([off_cnt, ot_sum])
    view_rows.append(row_data)

view_df = pd.DataFrame(view_rows, columns=["NO", "성명", "고정휴일"] + day_cols + ["휴일수", "O.T"])

st.markdown("""
<style>
  div[data-testid="stDataFrame"] { width: 100%; overflow-x: auto; }
</style>
""", unsafe_allow_html=True)

def style_dataframe_cells(val):
    v = str(val).strip().upper()
    if v == 'OFF':
        return 'color: #dc2626; font-weight: bold;'
    return ''

styled_view_df = view_df.style.map(style_dataframe_cells, subset=day_cols)
st.dataframe(styled_view_df, use_container_width=True, hide_index=True)

# --- 하단 잔여 현황 및 동적 결재란 (휴대폰 가독성 개선 스타일 적용) ---
st.markdown("---")
col_sum_title, col_approval = st.columns([1, 2])
with col_sum_title:
    st.subheader("📌 [휴일 및 연차(잔여) 현황]")
with col_approval:
    # 휴대폰 다크모드/라이트모드에서도 선명하게 보이도록 배경과 글자색 지정
    app_h = "".join([f"<th style='border: 1px solid #94a3b8; background-color: #f8fafc; color: #0f172a; padding: 6px; min-width: 65px; font-weight: bold;'>{m.split('(')[0].split()[0]}</th>" for m in members])
    app_td = "".join(["<td style='border: 1px solid #cbd5e1; background-color: #ffffff; color: #1e293b; height: 40px;'></td>" for _ in members])
    st.markdown(f'''
        <div style="text-align: right; overflow-x: auto;">
            <table style="display: inline-table; border-collapse: collapse; text-align: center; font-size: 11px; width: 100%;">
                <tr>{app_h}</tr>
                <tr>{app_td}</tr>
            </table>
        </div>
    ''', unsafe_allow_html=True)

sum_rows = [[i + 1, m, sum(get_ot_for_code(schedule_data.get(f"{year}-{month}-{i}-{d}", "OFF"), shift_types) for d in range(1, days_in_month + 1)), summary_data.get(f"{year}-{month}-{i}", {}).get("val", "연차"), summary_data.get(f"{year}-{month}-{i}", {}).get("memo", "")] for i, m in enumerate(members)]
sum_df = pd.DataFrame(sum_rows, columns=["NO", "성명", "O.T 합계", "휴일 및 연차(잔여)", "비고"])

if is_admin:
    edited_sum_df = st.data_editor(sum_df, use_container_width=True, hide_index=True, disabled=["NO", "성명", "O.T 합계"])
    if st.button("💾 잔여 현황 저장"):
        for row_idx, row in edited_sum_df.iterrows():
            summary_data[f"{year}-{month}-{row_idx}"] = {"val": str(row["휴일 및 연차(잔여)"]), "memo": str(row["비고"])}
        save_data(members, schedule_data, shift_types, summary_data, fixed_holidays_data, custom_holidays_list)
        st.success("✅ 잔여 현황이 저장되었습니다!")
        st.rerun()
else:
    st.dataframe(sum_df, use_container_width=True, hide_index=True)