import streamlit as st
import requests
import pandas as pd
import time
import json
import os
import re

API_KEY = "SPDdJ_kP7zKiKjX806J_CQ"

#webhook_url = "https://unmutative-alvera-unmineralised.ngrok-free.dev/apollo_webhook"

RESULT_FILE = "webhook_results.json"

st.set_page_config(page_title="Apollo LinkedIn Enrichment", layout="wide")

st.title("Apollo LinkedIn Bulk Enrichment Tool")

linkedin_input = st.text_area(
    "Paste LinkedIn URLs (one per line)",
    height=200
)

process = st.button("Start Enrichment")


def is_valid(url):
    pattern = r"^https:\/\/(www\.)?linkedin\.com\/in\/[A-Za-z0-9\-_%]+\/?$"
    return re.match(pattern, url)


def call_apollo(linkedin):

    url = "https://api.apollo.io/api/v1/people/match"

    headers = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY
    }

    payload = {
    "linkedin_url": linkedin,
    "reveal_phone_number": True,
    "reveal_personal_emails": True,
    "webhook_url": "https://unmutative-alvera-unmineralised.ngrok-free.dev/apollo_webhook"
}

    r = requests.post(url, headers=headers, json=payload)

    if r.status_code == 200:
        return r.json()

    return None


def load_webhook_data():

    if not os.path.exists(RESULT_FILE):
        return {}

    with open(RESULT_FILE) as f:
        data = json.load(f)

    return {d["person_id"]: d["phone"] for d in data}


if process:

    urls = [u.strip() for u in linkedin_input.split("\n") if u.strip()]

    results = []

    progress = st.progress(0)

    for i, url in enumerate(urls):

        if not is_valid(url):
            continue

        data = call_apollo(url)

        if data and "person" in data:

            person = data["person"]

            results.append({
                "person_id": person.get("id"),
                "LinkedIn": url,
                "Name": person.get("name"),
                "Title": person.get("title"),
                "Company": person.get("organization", {}).get("name"),
                "Email": person.get("email"),
                "Phone": "Waiting..."
            })

        progress.progress((i+1)/len(urls))

        time.sleep(1)

    df = pd.DataFrame(results)

    st.session_state["df"] = df

    st.success("Apollo enrichment started")

    st.dataframe(df)


if st.button("Refresh Phone Numbers"):

    if "df" not in st.session_state:
        st.warning("Run enrichment first")
    else:

        df = st.session_state["df"]

        phones = load_webhook_data()

        df["Phone"] = df["person_id"].map(phones).fillna("Waiting...")

        st.dataframe(df)

        csv = df.to_csv(index=False).encode()

        st.download_button(
            "Download CSV",
            csv,
            "apollo_results.csv"
        )
