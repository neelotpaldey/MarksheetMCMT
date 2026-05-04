import streamlit as st
import pandas as pd

def load_sheet(sheet_name):
    sheet_id = "1SId7izPI1if7v0npmNVc-ImAF4cTYLCO5hK6XjR9cmM"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    df = pd.read_csv(url)
    return df


def main():
    st.set_page_config(page_title="Student Report", layout="wide")

    # ---------------- BANNER ----------------
    st.image("banner.png", use_container_width=True)
    st.markdown("---")

    # ---------------- LOGIN / SELECTION ----------------
    st.subheader("Select Details")

    col1, col2 = st.columns(2)

    with col1:
        university = st.selectbox("University", ["VBSPU", "MGKVP"])

    with col2:
        semester = st.selectbox("Semester", ["2", "4", "6"])

    sheet_name = f"{university} {semester}"

    st.markdown("---")

    # ---------------- LOAD DATA ----------------
    try:
        df = load_sheet(sheet_name)

        # Clean dataframe (remove empty rows)
        df = df.dropna(how='all')

        # ---------------- STUDENT LIST ----------------
        names = df.iloc[6:, 2].dropna().tolist()  # Column C, row 7+

        student = st.selectbox("Select Student", names)

        if student:
            row = df[df.iloc[:, 2] == student].index[0]

            st.markdown("---")
            st.subheader("Student Data")

            # ---------------- ATTENDANCE / BASIC ----------------
            st.write("Name:", student)

            # ---------------- SESSIONAL ----------------
            st.subheader("Sessional Marks (N–R)")

            sessional_cols = df.columns[13:18]
            sessional_data = df.loc[row, sessional_cols]

            st.table(pd.DataFrame([sessional_data.values], columns=sessional_cols))

            # ---------------- PUT ----------------
            st.subheader("PUT Marks (U–Y)")

            put_cols = df.columns[20:25]
            put_data = df.loc[row, put_cols]

            st.table(pd.DataFrame([put_data.values], columns=put_cols))

    except Exception as e:
        st.error("Error loading sheet. Check sheet name or sharing settings.")


if __name__ == "__main__":
    main()
