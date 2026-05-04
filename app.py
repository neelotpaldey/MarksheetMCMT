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


# ---------------- LOAD ----------------
@st.cache_data(ttl=300)
def download(file_id):
    url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
    return requests.get(url).content


def read(file_id, sheet):
    return pd.read_excel(io.BytesIO(download(file_id)), sheet_name=sheet, skiprows=6)


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
    return "ABS" if val is None else val


def parse_sheet(name):
    parts = name.rsplit(" ", 1)
    return (parts[0], parts[1], name) if len(parts)==2 and parts[1].isdigit() else None


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

    # Load data
    marks_df = read(MARKSHEET_FILE_ID, sheet)
    att_df = read(ATTENDANCE_FILE_ID, sheet)

    marks_df.columns = [str(c).strip() for c in marks_df.columns]
    att_df.columns = [str(c).strip() for c in att_df.columns]

    # Student column
    student_col = [c for c in marks_df.columns if "name" in c.lower()][0]

    student = st.selectbox("Student", ["--"] + marks_df[student_col].dropna().astype(str).tolist())
    if student == "--": return

    row = marks_df[marks_df[student_col].astype(str)==student].iloc[0]

    # ---------------- MATCH ATTENDANCE (COLUMN A) ----------------
    roll_marks = clean(row[marks_df.columns[0]])
    att_df["_roll_clean"] = att_df[att_df.columns[0]].astype(str).apply(clean)

    match = att_df[att_df["_roll_clean"] == roll_marks]
    att_row = match.iloc[0] if not match.empty else None

    # ---------------- DETAILS ----------------
    st.subheader("👤 Student Details")
    st.write(f"**Name:** {row[student_col]}")

    # ---------------- ATTENDANCE ----------------
    st.subheader("📅 Attendance")

    if att_row is None:
        att_table = [["N/A"]*5]*3
    else:
        def g(k): return att_row.get(k, None)

        att_table = [
            [safe(g("I")), safe(g("S")), safe(g("AC")), safe(g("AM")), safe(g("AW"))],
            [safe(g("I6")), safe(g("S6")), safe(g("AC6")), safe(g("AM6")), safe(g("AW6"))],
            [safe_percent(g("J")), safe_percent(g("T")), safe_percent(g("AD")), safe_percent(g("AN")), safe_percent(g("AX"))]
        ]

    st.table(pd.DataFrame(att_table,
        columns=["Sem2","Sem3","Sem4","Sem5","Sem6"],
        index=["Present","Out of","%"]
    ))

    # ---------------- MARKS ----------------
    sessional = marks_df.columns[16:21]
    put = marks_df.columns[23:28]

    subjects, sm, pm = [], [], []

    for i in range(len(sessional)):
        s = sessional[i]; p = put[i]
        sv, pv = to_float(row[s]), to_float(row[p])

        if sv is None and pv is None: continue

        subjects.append(s)
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
