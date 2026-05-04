# main.py
import streamlit as st
import pandas as pd
import requests
import io
import unicodedata
import streamlit.components.v1 as components
import re

# ---------------- CONFIG ----------------
MARKSHEET_FILE_ID = "1MKgETtpCs4MOTL8ErQuPIjIR2peBXADx"
ATTENDANCE_FILE_ID = "1p9eBLQksJo_huyADppeFQ22nTIadmSqV"

st.set_page_config(page_title="Marksheet", layout="wide")


# ---------------- LOAD ----------------
@st.cache_data(ttl=300)
def download(file_id):
    url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
    return requests.get(url).content


def read_raw(file_id, sheet):
    return pd.read_excel(io.BytesIO(download(file_id)), sheet_name=sheet, header=None)


# ---------------- HELPERS ----------------
def clean(val):
    try: return str(val).strip().lower()
    except: return ""


def safe(val):
    try:
        if pd.isna(val): return "N/A"
        return val
    except:
        return "N/A"


def safe_percent(val):
    try:
        if pd.isna(val): return "N/A"
        return f"{float(val)}%"
    except:
        return "N/A"


def to_float(val):
    try:
        if pd.isna(val): return None
    except: pass
    try:
        return float(str(val).replace(",", "").replace("%", ""))
    except:
        return None


def format_mark(val):
    return "N/A" if val is None else val


def parse_sheet(name):
    parts = name.rsplit(" ", 1)
    return (parts[0], parts[1], name) if len(parts)==2 and parts[1].isdigit() else None


def excel_col_to_idx(col):
    idx = 0
    for ch in col.upper():
        if "A" <= ch <= "Z":
            idx = idx * 26 + (ord(ch) - ord("A") + 1)
    return idx - 1


def looks_numeric_roll(val):
    if pd.isna(val):
        return False
    s = str(val).strip()
    return bool(s) and bool(re.fullmatch(r"\d+(\.0+)?", s))


def find_first_data_row(df, roll_col, name_col):
    for i in range(len(df)):
        roll_val = df.iat[i, roll_col] if roll_col < df.shape[1] else None
        name_val = df.iat[i, name_col] if name_col < df.shape[1] else None
        if looks_numeric_roll(roll_val) and not pd.isna(name_val) and str(name_val).strip():
            return i
    return None


# ---------------- MAIN ----------------
def main():

    # Banner
    try:
        st.image("banner.png", use_container_width=True)
    except:
        pass

    # Sheet selection
    xls = pd.ExcelFile(io.BytesIO(download(MARKSHEET_FILE_ID)))
    parsed = [p for p in (parse_sheet(s) for s in xls.sheet_names) if p]

    uni = st.selectbox("University", ["--"] + sorted({u for u,y,o in parsed}))
    if uni == "--": return

    year = st.selectbox("Admission Year", ["--"] + sorted({y for u,y,o in parsed if u==uni}))
    if year == "--": return

    sheet = [o for u,y,o in parsed if u==uni and y==year][0]

    # Load raw sheets
    marks_df = read_raw(MARKSHEET_FILE_ID, sheet)
    att_df = read_raw(ATTENDANCE_FILE_ID, sheet)

    # Fixed columns from the template image
    marks_roll_col = excel_col_to_idx("A")
    marks_name_col = excel_col_to_idx("D")
    marks_admission_col = excel_col_to_idx("B")
    marks_univ_roll_col = excel_col_to_idx("C")
    marks_father_col = excel_col_to_idx("E")

    sessional_cols = [excel_col_to_idx(c) for c in ["Q", "R", "S", "T", "U"]]
    put_cols = [excel_col_to_idx(c) for c in ["X", "Y", "Z", "AA", "AB"]]

    att_roll_col = excel_col_to_idx("A")
    att_name_col = excel_col_to_idx("B")
    att_present_cols = [excel_col_to_idx(c) for c in ["I", "S", "AC", "AM", "AW"]]
    att_out_of_cols = [excel_col_to_idx(c) for c in ["I", "S", "AC", "AM", "AW"]]
    att_percent_cols = [excel_col_to_idx(c) for c in ["J", "T", "AD", "AN", "AX"]]

    marks_start = find_first_data_row(marks_df, marks_roll_col, marks_name_col)
    att_start = find_first_data_row(att_df, att_roll_col, att_name_col)

    if marks_start is None or att_start is None:
        st.error("Could not detect student rows in one or more sheets.")
        return

    marks_header = marks_start - 1 if marks_start > 0 else marks_start

    marks_data = marks_df.iloc[marks_start:].copy()
    marks_data = marks_data[
        marks_data[marks_name_col].notna() &
        marks_data[marks_name_col].astype(str).str.strip().ne("")
    ]

    student = st.selectbox("Student", ["--"] + marks_data[marks_name_col].astype(str).tolist())
    if student == "--": return

    row = marks_data[marks_data[marks_name_col].astype(str) == student].iloc[0]

    # ---------------- MATCH ATTENDANCE (COLUMN A) ----------------
    roll_marks = clean(row[marks_roll_col])
    att_data = att_df.iloc[att_start:].copy()
    att_data["_roll_clean"] = att_data[att_roll_col].astype(str).apply(clean)

    match = att_data[att_data["_roll_clean"] == roll_marks]
    att_row = match.iloc[0] if not match.empty else None

    # ---------------- DETAILS ----------------
    st.subheader("👤 Student Details")
    st.write(f"**Roll Number:** {safe(row[marks_roll_col])}")
    st.write(f"**Admission Number:** {safe(row[marks_admission_col])}")
    st.write(f"**University Roll No:** {safe(row[marks_univ_roll_col])}")
    st.write(f"**Name:** {safe(row[marks_name_col])}")
    st.write(f"**Father's Name:** {safe(row[marks_father_col])}")

    # ---------------- ATTENDANCE ----------------
    st.subheader("📅 Attendance")

    if att_row is None:
        att_table = [["N/A"]*5]*3
    else:
        out_row_idx = att_start - 1 if att_start > 0 else att_start
        out_row = att_df.iloc[out_row_idx] if out_row_idx < len(att_df) else None

        def g_row(r, col_idx):
            if r is None or col_idx >= len(r):
                return None
            return r.iloc[col_idx]

        att_table = [
            [safe(g_row(att_row, c)) for c in att_present_cols],
            [safe(g_row(out_row, c)) for c in att_out_of_cols],
            [safe_percent(g_row(att_row, c)) for c in att_percent_cols]
        ]

    st.table(pd.DataFrame(att_table,
        columns=["Sem2","Sem3","Sem4","Sem5","Sem6"],
        index=["Present","Out of","%"]
    ))

    # ---------------- MARKS ----------------
    sessional = sessional_cols
    put = put_cols

    subjects, sm, pm = [], [], []

    for i in range(len(sessional)):
        s_col = sessional[i]
        p_col = put[i]
        sv, pv = to_float(row[s_col]), to_float(row[p_col])

        if sv is None and pv is None: continue

        subject_name = marks_df.iat[marks_header, s_col] if marks_header is not None and s_col < marks_df.shape[1] else f"Subject {i+1}"
        if pd.isna(subject_name) or str(subject_name).strip() == "":
            subject_name = f"Subject {i+1}"

        subjects.append(str(subject_name).strip())
        sm.append(format_mark(sv))
        pm.append(format_mark(pv))

    if "VBSPU" in uni: smax, pmax = 30,70
    else: smax, pmax = 25,75

    stotal = sum([x for x in sm if isinstance(x,(int,float))])
    ptotal = sum([x for x in pm if isinstance(x,(int,float))])

    n = len(subjects)
    sp = round(stotal/(n*smax)*100,2) if n else 0
    pp = round(ptotal/(n*pmax)*100,2) if n else 0

    data = [{"Subject":subjects[i],"Sessional":sm[i],"PUT":pm[i]} for i in range(n)]
    data += [
        {"Subject":"Total","Sessional":stotal,"PUT":ptotal},
        {"Subject":"Percentage","Sessional":f"{sp}%","PUT":f"{pp}%"}
    ]

    st.subheader("📊 Result")
    st.table(pd.DataFrame(data))

    # ---------------- PRINT ----------------
    st.markdown("---")
    if st.button("🖨️ Print Marksheet"):
        components.html("<script>window.print();</script>", height=0)


if __name__ == "__main__":
    main()
