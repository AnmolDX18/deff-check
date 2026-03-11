import streamlit as st
import requests
import pandas as pd
import re
import time

API_KEY = "SPDdJ_kP7zKiKjX806J_CQ"

MATCH_URL = "https://api.apollo.io/api/v1/people/match"
REVEAL_URL = "https://api.apollo.io/api/v1/people/reveal"

headers = {
    "Content-Type": "application/json",
    "x-api-key": API_KEY
}

st.set_page_config(page_title="Apollo Enrichment", layout="wide")

st.title("Apollo LinkedIn Enrichment Tool")

linkedin_input = st.text_area(
    "Paste LinkedIn URLs",
    height=200
)

start = st.button("Match Profiles")


def is_valid(url):
    pattern = r"^https:\/\/(www\.)?linkedin\.com\/in\/"
    return re.match(pattern, url)


def match_person(linkedin):

    payload = {
        "linkedin_url": linkedin
    }

    r = requests.post(MATCH_URL, headers=headers, json=payload)

    if r.status_code == 200:
        return r.json()

    return None


def reveal_phone(person_id):

    payload = {
        "id": person_id,
        "reveal_phone_number": True
    }

    r = requests.post(REVEAL_URL, headers=headers, json=payload)

    if r.status_code == 200:

        data = r.json()

        phones = data.get("person", {}).get("phone_numbers", [])

        if phones:
            return phones[0].get("sanitized_number")

    return None


# --------------------
# MATCH PROFILES
# --------------------

if start:

    urls = [u.strip() for u in linkedin_input.split("\n") if u.strip()]

    results = []

    progress = st.progress(0)

    for i, url in enumerate(urls):

        if not is_valid(url):
            continue

        data = match_person(url)

        if data and "person" in data:

            p = data["person"]

            results.append({
                "person_id": p.get("id"),
                "LinkedIn": url,
                "Name": p.get("name"),
                "Title": p.get("title"),
                "Company": p.get("organization", {}).get("name"),
                "Email": p.get("email"),
                "Phone": ""
            })

        progress.progress((i + 1) / len(urls))

        time.sleep(0.7)

    df = pd.DataFrame(results)

    st.session_state["df"] = df


# --------------------
# SHOW TABLE
# --------------------

if "df" in st.session_state:

    df = st.session_state["df"]

    for i, row in df.iterrows():

        col1, col2, col3, col4, col5 = st.columns([3,2,2,2,1])

        col1.write(row["Name"])
        col2.write(row["Company"])
        col3.write(row["Email"])
        col4.write(row["Phone"])

        if col5.button("Reveal Phone", key=i):

            phone = reveal_phone(row["person_id"])

            df.loc[i, "Phone"] = phone

            st.session_state["df"] = df

            st.rerun()

    st.download_button(
        "Download CSV",
        df.to_csv(index=False).encode(),
        "apollo_results.csv"
    )
