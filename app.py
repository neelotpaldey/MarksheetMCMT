# main.py
import streamlit as st
import pandas as pd
import requests
import io
import unicodedata
import streamlit.components.v1 as components

# ---------------- CONFIG ----------------
MARKSHEET_FILE_ID = "1MKgETtpCs4MOTL8ErQuPIjIR2peBXADx"
ATTENDANCE_FILE_ID = "1p9eBLQksJo_huyADppeFQ22nTIadmSqV"

st.set_page_config(page_title="Marksheet", layout="wide")


# ---------------- GOOGLE SHEET ----------------
@st.cache_data(ttl=300)
def download_sheet(file_id):
    url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.content


def load_excel(file_id):
    return pd.ExcelFile(io.BytesIO(download_sheet(file_id)), engine="openpyxl")


def read_sheet(file_id, sheet):
    return pd.read_excel(
        io.BytesIO(download_sheet(file_id)),
        sheet_name=sheet,
        skiprows=6,
        engine="openpyxl"
    )


# ---------------- HELPERS ----------------
def to_float(val):
    try:
        if pd.isna(val): return None
    except: pass

    s = str(val).strip()
    if s == "": return None

    try:
        return float(s.replace(",", "").replace("%", ""))
    except:
        return None


def find_column(df, keys):
    for col in df.columns:
        c = col.strip().lower()
        if any(k in c for k in keys):
            return col
    return None


def parse_sheet(name):
    parts = name.rsplit(" ", 1)
    if len(parts) == 2 and parts[1].isdigit():
        return parts[0], parts[1], name
    return None


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


def format_mark(val):
    return "ABS" if val is None else val


# ---------------- MAIN ----------------
def main():

    # Banner
    try:
        st.image("banner.png", use_container_width=True)
    except:
        pass

    # Load sheets
    marks_xls = load_excel(MARKSHEET_FILE_ID)
    parsed = [p for p in (parse_sheet(s) for s in marks_xls.sheet_names) if p]

    # University
    uni = st.selectbox("University", ["--"] + sorted({u for u, y, o in parsed}))
    if uni == "--": return

    # Year
    year = st.selectbox("Admission Year", ["--"] + sorted({y for u, y, o in parsed if u == uni}))
    if year == "--": return

    sheet = [o for u, y, o in parsed if u == uni and y == year][0]

    # Load both sheets
    marks_df = read_sheet(MARKSHEET_FILE_ID, sheet)
    att_df = read_sheet(ATTENDANCE_FILE_ID, sheet)

    marks_df.columns = [str(c).strip() for c in marks_df.columns]
    att_df.columns = [str(c).strip() for c in att_df.columns]

    # Columns
    student_col = find_column(marks_df, ["student", "name"])
    father_col = find_column(marks_df, ["father"])
    adm_col = find_column(marks_df, ["admission"])

    if not student_col:
        st.error("Student column not found")
        return

    # Student selection
    student = st.selectbox("Student", ["--"] + marks_df[student_col].dropna().astype(str).tolist())
    if student == "--": return

    row = marks_df[marks_df[student_col].astype(str) == student].iloc[0]

    # Match attendance row
    att_row = att_df[att_df[student_col].astype(str) == student]
    att_row = att_row.iloc[0] if not att_row.empty else None

    # ---------------- STUDENT DETAILS ----------------
    st.subheader("👤 Student Details")
    st.write(f"**Name:** {row[student_col]}")
    if adm_col: st.write(f"**Admission No:** {row[adm_col]}")
    if father_col: st.write(f"**Father Name:** {row[father_col]}")

    # ---------------- ATTENDANCE ----------------
    st.subheader("📅 Attendance")

    if att_row is None:
        attendance_df = pd.DataFrame({
            " ": ["Present", "Out of", "Percentage"],
            "Semester 2": ["N/A"]*3,
            "Semester 3": ["N/A"]*3,
            "Semester 4": ["N/A"]*3,
            "Semester 5": ["N/A"]*3,
            "Semester 6": ["N/A"]*3,
        })
    else:
        attendance_df = pd.DataFrame({
            " ": ["Present", "Out of", "Percentage"],
            "Semester 2": [safe(att_row.get("I")), safe(att_row.get("I6")), safe_percent(att_row.get("J"))],
            "Semester 3": [safe(att_row.get("S")), safe(att_row.get("S6")), safe_percent(att_row.get("T"))],
            "Semester 4": [safe(att_row.get("AC")), safe(att_row.get("AC6")), safe_percent(att_row.get("AD"))],
            "Semester 5": [safe(att_row.get("AM")), safe(att_row.get("AM6")), safe_percent(att_row.get("AN"))],
            "Semester 6": [safe(att_row.get("AW")), safe(att_row.get("AW6")), safe_percent(att_row.get("AX"))],
        })

    st.table(attendance_df)

    # ---------------- MARKS ----------------
    sessional_cols = marks_df.columns[16:21]
    put_cols = marks_df.columns[23:28]

    subjects, s_marks, p_marks = [], [], []

    for i in range(len(sessional_cols)):
        s = sessional_cols[i]
        p = put_cols[i]

        subject = str(s).strip()
        sv = to_float(row[s])
        pv = to_float(row[p])

        if subject == "" and sv is None and pv is None:
            continue

        subjects.append(subject)
        s_marks.append(format_mark(sv))
        p_marks.append(format_mark(pv))

    # Rules
    if "MGKVP" in uni.upper():
        sm, pm = 25, 75
    elif "VBSPU" in uni.upper():
        sm, pm = 30, 70
    else:
        sm, pm = 25, 75

    # Totals
    s_total = sum([x for x in s_marks if isinstance(x, (int, float))])
    p_total = sum([x for x in p_marks if isinstance(x, (int, float))])

    n = len(subjects)
    s_max = n * sm
    p_max = n * pm

    s_pct = round((s_total / s_max) * 100, 2) if s_max else 0
    p_pct = round((p_total / p_max) * 100, 2) if p_max else 0

    # Table
    data = []
    for i in range(n):
        data.append({
            "Subject": subjects[i],
            "Sessional": s_marks[i],
            "PUT": p_marks[i]
        })

    data.append({"Subject": "Total", "Sessional": s_total, "PUT": p_total})
    data.append({"Subject": "Percentage", "Sessional": f"{s_pct}%", "PUT": f"{p_pct}%"})

    st.subheader("📊 Result")
    st.table(pd.DataFrame(data))

    # ---------------- PRINT ----------------
    st.markdown("---")
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.button("🖨️ Print Marksheet"):
            components.html("<script>window.print();</script>", height=0)


if __name__ == "__main__":
    main()
