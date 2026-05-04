# main.py
import streamlit as st
import pandas as pd
import requests
import io
import unicodedata
import streamlit.components.v1 as components

# ---------------- CONFIG ----------------
GOOGLE_SHEET_FILE_ID = "1MKgETtpCs4MOTL8ErQuPIjIR2peBXADx"

st.set_page_config(page_title="Marksheet Viewer", layout="wide")


# ---------------- GOOGLE SHEET LOADER ----------------
@st.cache_data(ttl=300)
def download_sheet_xlsx(file_id: str) -> bytes:
    url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.content


def load_excel(file_id):
    content = download_sheet_xlsx(file_id)
    return pd.ExcelFile(io.BytesIO(content), engine="openpyxl")


def read_sheet(file_id, sheet_name):
    content = download_sheet_xlsx(file_id)
    return pd.read_excel(
        io.BytesIO(content),
        sheet_name=sheet_name,
        skiprows=6,
        engine="openpyxl"
    )


# ---------------- HELPERS ----------------
def to_float(val):
    try:
        if pd.isna(val):
            return None
    except:
        pass

    s = str(val).strip()
    if s == "":
        return None

    s = unicodedata.normalize("NFKC", s)

    try:
        return float(s.replace(",", "").replace("%", ""))
    except:
        return None


def parse_sheet(sheetname: str):
    parts = sheetname.rsplit(" ", 1)
    if len(parts) == 2 and parts[1].isdigit():
        return parts[0], parts[1], sheetname
    return sheetname, "", sheetname


def find_column(df, keywords):
    for col in df.columns:
        col_clean = col.strip().lower()
        for key in keywords:
            if key in col_clean:
                return col
    return None


def format_mark(val):
    if val is None:
        return "ABS"   # change to "ML" if needed
    return val


# ---------------- MAIN ----------------
def main():

    # ---------- Banner ----------
    try:
        st.image("banner.png", use_container_width=True)
    except:
        pass

    st.title("📄 Marksheet Viewer")

    # ---------- Print ----------
    if st.button("🖨️ Print Marksheet"):
        components.html("<script>window.print();</script>", height=0)

    # ---------- Load Sheets ----------
    xls = load_excel(GOOGLE_SHEET_FILE_ID)
    sheets = xls.sheet_names
    parsed = [parse_sheet(s) for s in sheets]

    # ---------- University ----------
    universities = sorted({u for u, y, o in parsed})
    uni = st.selectbox("Select University", ["-- choose --"] + universities)
    if uni == "-- choose --":
        return

    # ---------- Admission Year ----------
    years = sorted({y for u, y, o in parsed if u == uni})
    year = st.selectbox("Select Admission Year", ["-- choose --"] + years)
    if year == "-- choose --":
        return

    sheet_name = [o for u, y, o in parsed if u == uni and y == year][0]

    # ---------- Load Data ----------
    df = read_sheet(GOOGLE_SHEET_FILE_ID, sheet_name)
    df.columns = [str(c).strip() for c in df.columns]

    # ---------- Detect Columns ----------
    student_col = find_column(df, ["student", "name"])
    admission_col = find_column(df, ["admission"])
    father_col = find_column(df, ["father"])

    if not student_col:
        st.error("Student column not found")
        st.write(df.columns.tolist())
        return

    # ---------- Student ----------
    students = df[student_col].dropna().astype(str).tolist()
    student = st.selectbox("Select Student", ["-- choose --"] + students)
    if student == "-- choose --":
        return

    row = df[df[student_col].astype(str) == student].iloc[0]

    # ---------- Student Details ----------
    st.subheader("👤 Student Details")
    st.write(f"**Name:** {row[student_col]}")
    if admission_col:
        st.write(f"**Admission No:** {row[admission_col]}")
    if father_col:
        st.write(f"**Father Name:** {row[father_col]}")

    # ---------- Attendance Placeholder ----------
    st.subheader("📅 Attendance")

    attendance_df = pd.DataFrame({
        " ": ["Present", "Out of", "Percentage"],
        "Semester 2": ["", "", ""],
        "Semester 3": ["", "", ""],
        "Semester 4": ["", "", ""],
        "Semester 5": ["", "", ""],
        "Semester 6": ["", "", ""],
    })

    st.table(attendance_df)

    # ---------- MARKS ----------
    sessional_cols = df.columns[16:21]   # Q-U
    put_cols = df.columns[23:28]         # X-AB

    subjects, sess_marks, put_marks = [], [], []

    for i in range(len(sessional_cols)):
        s_col = sessional_cols[i]
        p_col = put_cols[i]

        subject = str(s_col).strip()

        s_val = to_float(row[s_col])
        p_val = to_float(row[p_col])

        if subject == "" and s_val is None and p_val is None:
            continue

        subjects.append(subject)
        sess_marks.append(format_mark(s_val))
        put_marks.append(format_mark(p_val))

    # ---------- RULE ----------
    if "MGKVP" in uni.upper():
        sess_max = 25
        put_max = 75
    elif "VBSPU" in uni.upper():
        sess_max = 30
        put_max = 70
    else:
        sess_max = 25
        put_max = 75

    # ---------- TOTAL ----------
    sessional_total = sum([x for x in sess_marks if isinstance(x, (int, float))])
    put_total = sum([x for x in put_marks if isinstance(x, (int, float))])

    n = len(subjects)
    sessional_max = n * sess_max
    put_maximum = n * put_max

    sessional_percent = round((sessional_total / sessional_max) * 100, 2) if sessional_max else 0
    put_percent = round((put_total / put_maximum) * 100, 2) if put_maximum else 0

    # ---------- TABLE ----------
    table_data = []

    for i in range(len(subjects)):
        table_data.append({
            "Subject": subjects[i],
            "Sessional Marks": sess_marks[i],
            "PUT Marks": put_marks[i]
        })

    table_data.append({
        "Subject": "Total",
        "Sessional Marks": sessional_total,
        "PUT Marks": put_total
    })

    table_data.append({
        "Subject": "Percentage",
        "Sessional Marks": f"{sessional_percent}%",
        "PUT Marks": f"{put_percent}%"
    })

    marks_df = pd.DataFrame(table_data)

    st.subheader("📊 Result")
    st.table(marks_df)


if __name__ == "__main__":
    main()
