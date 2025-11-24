
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="Unified Billing Dashboard", layout="wide")
st.title("Unified Billing & Reporting — Streamlit Frontend (Python Backend)")

st.sidebar.header("Config")
api_base = st.sidebar.text_input("API base URL", value="http://localhost:8000")
client_id = st.sidebar.number_input("Client ID", min_value=1, value=1)
month = st.sidebar.text_input("Month (YYYY-MM) or blank", value="2025-11")
show_pdf = st.sidebar.checkbox("Show case study PDF", value=True)

token = st.sidebar.text_input("Auth token (optional)", value="")

cols = st.columns([3,1])
with cols[0]:
    st.header("Client Report")
    if st.button("Fetch report"):
        try:
            headers = {}
            if token:
                headers['X-Auth-Token'] = token
            url = f"{api_base}/reports/client/{client_id}"
            if month:
                url += f"?month={month}"
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            st.success("Report fetched")
            totals = data.get('totals', {})
            st.metric("Total Charge", f"₹{totals.get('totalCharge',0):,.2f}")
            st.metric("Total Incentive", f"₹{totals.get('totalIncentive',0):,.2f}")
            st.metric("Trips", totals.get('trips',0))
            trips = data.get('tripCharges', [])
            if trips:
                df = pd.DataFrame(trips)
                st.subheader("Trips (sample)")
                st.dataframe(df)
                if set(['distance_km','charge']).issubset(df.columns):
                    fig = px.scatter(df, x='distance_km', y='charge', hover_data=['id','vendor_id','trip_date'])
                    st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Failed to fetch report: {e}")

with cols[1]:
    st.header("Controls")
    if st.button("Import sample trips"):
        try:
            resp = requests.post(f"{api_base}/trips/import-sample", timeout=10)
            st.success(f"Imported: {resp.json().get('imported')}")
        except Exception as e:
            st.error(f"Import failed: {e}")

st.markdown('---')
st.header("Case Study PDF")
pdf_path = "/mnt/data/Unified Billing & Reporting Platform.pdf"
if show_pdf:
    if Path(pdf_path).exists():
        st.markdown(f"Local case study path: `{pdf_path}`")
        try:
            with open(pdf_path, 'rb') as f:
                data = f.read()
            st.download_button("Download Case Study PDF", data=data, file_name="Unified Billing & Reporting Platform.pdf")
        except Exception as e:
            st.info("Could not embed PDF for download in this environment.")
    else:
        st.info("PDF not found at expected path.")
