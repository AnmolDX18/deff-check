import streamlit as st
import requests
import time
import pandas as pd
import re

# ---------------------------
# 🔐 Hardcoded API Key
# ---------------------------
API_KEY = "P1oBhoT_DH4c7QUej1bCBg"

# ---------------------------
# Page Config
# ---------------------------
st.set_page_config(page_title="Apollo LinkedIn Enrichment", layout="wide")
st.title("🔎 Apollo LinkedIn Bulk Enrichment Tool")

linkedin_input = st.text_area(
    "Paste LinkedIn Profile URLs (one per line)",
    height=200
)

process_button = st.button("🚀 Process Profiles")

# ---------------------------
# URL Validation
# ---------------------------
def is_valid_linkedin_url(url):
    pattern = r"^https:\/\/(www\.)?linkedin\.com\/in\/[A-Za-z0-9\-_%]+\/?$"
    return re.match(pattern, url)


# ---------------------------
# Retry Request Function
# ---------------------------
def make_request_with_retry(payload, max_retries=3, backoff=2):
    BASE_URL = "https://api.apollo.io/api/v1/people/match"

    PARAMS = {
        "run_waterfall_email": "false",
        "run_waterfall_phone": "false",
        "reveal_personal_emails": "false",
        "reveal_phone_number": "false"
    }

    headers = {
        "Cache-Control": "no-cache",
        "Content-Type": "application/json",
        "accept": "application/json",
        "x-api-key": API_KEY
    }

    for attempt in range(max_retries):
        try:
            response = requests.post(
                BASE_URL,
                headers=headers,
                params=PARAMS,
                json=payload,
                timeout=15
            )

            if response.status_code == 200:
                return response.json(), response.headers

            elif response.status_code == 429:
                wait = backoff ** attempt
                time.sleep(wait)

            elif 500 <= response.status_code < 600:
                wait = backoff ** attempt
                time.sleep(wait)

            else:
                return None, None

        except requests.exceptions.RequestException:
            wait = backoff ** attempt
            time.sleep(wait)

    return None, None


# ---------------------------
# Extract Required Fields
# ---------------------------
def extract_person_data(data, linkedin_url):
    if not data or "person" not in data:
        return {
            "LinkedIn URL": linkedin_url,
            "Name": None,
            "Title": None,
            "Seniority": None,
            "Departments": None,
            "Company": None,
            "Email": None,
            "Contact Number": None
        }

    person = data["person"]
    org = person.get("organization", {})

    return {
        "LinkedIn URL": linkedin_url,
        "Name": person.get("name"),
        "Title": person.get("title"),
        "Seniority": person.get("seniority"),
        "Departments": ", ".join(person.get("departments", [])),
        "Company": org.get("name"),
        "Email": person.get("email"),
        "Contact Number": org.get("phone")
    }


# ---------------------------
# Credit Session State
# ---------------------------
if "starting_credits" not in st.session_state:
    st.session_state.starting_credits = None

if "last_known_credits" not in st.session_state:
    st.session_state.last_known_credits = None


# ---------------------------
# Main Processing
# ---------------------------
if process_button:

    if not linkedin_input.strip():
        st.error("Please enter at least one LinkedIn URL")
        st.stop()

    linkedin_list = [
        url.strip()
        for url in linkedin_input.split("\n")
        if url.strip()
    ]

    valid_urls = []
    invalid_urls = []

    for url in linkedin_list:
        if is_valid_linkedin_url(url):
            valid_urls.append(url)
        else:
            invalid_urls.append(url)

    if invalid_urls:
        st.warning("⚠️ Invalid LinkedIn URLs:")
        for bad in invalid_urls:
            st.write(f"- {bad}")

    if not valid_urls:
        st.error("No valid LinkedIn URLs to process.")
        st.stop()

    results = []
    progress_bar = st.progress(0)

    for idx, url in enumerate(valid_urls):
        payload = {"linkedin_url": url}

        response_data, response_headers = make_request_with_retry(payload)

        # Capture credit headers (if available)
        if response_headers:
            remaining_credits = response_headers.get("x-ratelimit-remaining") or \
                                response_headers.get("x-credits-remaining")

            if remaining_credits:
                remaining_credits = int(remaining_credits)

                if st.session_state.starting_credits is None:
                    st.session_state.starting_credits = remaining_credits

                st.session_state.last_known_credits = remaining_credits

        extracted = extract_person_data(response_data, url)
        results.append(extracted)

        progress_bar.progress((idx + 1) / len(valid_urls))
        time.sleep(1)

    df = pd.DataFrame(results)

    st.success("✅ Processing Completed!")
    st.dataframe(df, use_container_width=True)

    # ---------------------------
    # Credit Metrics Display
    # ---------------------------
    if st.session_state.starting_credits and st.session_state.last_known_credits:

        credits_used = (
            st.session_state.starting_credits -
            st.session_state.last_known_credits
        )

        col1, col2, col3 = st.columns(3)

        col1.metric("💳 Starting Credits", st.session_state.starting_credits)
        col2.metric("📉 Credits Used (Session)", credits_used)
        col3.metric("🔢 Remaining Credits", st.session_state.last_known_credits)

    # ---------------------------
    # Download CSV
    # ---------------------------
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Results as CSV",
        data=csv,
        file_name="apollo_enrichment_results.csv",
        mime="text/csv"
    )

