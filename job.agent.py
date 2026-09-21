# ============================================================
# JOB SEARCH AGENT
# India Remote + Kolkata
# Experience: 0-6 Years
# ============================================================

import os
import re
import json
from datetime import date
from urllib.parse import quote, urljoin

import requests
import pandas as pd
from bs4 import BeautifulSoup
import gspread
from google.oauth2.service_account import Credentials


# ============================================================
# 1. JOB PROFILE
# ============================================================

TARGET_ROLES = [
    "HR Executive",
    "HR Manager",
    "HR Shared Services",
    "HR Operations",
    "Payroll HR",
    "Junior Data Analyst",
    "Report Analyst"
]

TARGET_SKILLS = [
    "SQL",
    "Power BI",
    "Excel",
    "HR Analytics",
    "Data Analysis",
    "Payroll",
    "HR Operations",
    "HR Shared Services",
    "HRIS",
    "SAP HCM"
]

MAX_YEARS = 6

TODAY = str(date.today())


# ============================================================
# 2. SEARCH TYPES
# ============================================================

SEARCH_TYPES = [
    "India Remote",
    "Kolkata"
]


# ============================================================
# 3. PORTALS
# ============================================================

PORTALS = [
    "Naukri",
    "LinkedIn India",
    "Indeed India",
    "Internshala",
    "Foundit",
    "Cutshort",
    "Hirist",
    "Shine",
    "TimesJobs"
]


# ============================================================
# 4. REQUEST SETTINGS
# ============================================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/153.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-IN,en;q=0.9"
}

session = requests.Session()
session.headers.update(HEADERS)


# ============================================================
# 5. CREATE SEARCH LINKS
# ============================================================

def create_search_links():

    search_links = []

    for role in TARGET_ROLES:

        r = quote(role)

        role_slug = role.lower().replace(" ", "-")

        # ----------------------------------------------------
        # INDIA REMOTE
        # ----------------------------------------------------

        remote_links = {

            "Naukri":
                f"https://www.naukri.com/{role_slug}-jobs?jobType=remote",

            "LinkedIn India":
                f"https://www.linkedin.com/jobs/search/"
                f"?keywords={r}&location=India&f_WT=2",

            "Indeed India":
                f"https://in.indeed.com/jobs?"
                f"q={r}&l=India",

            "Internshala":
                "https://internshala.com/remote-jobs/",

            "Foundit":
                f"https://www.foundit.in/search/"
                f"{role_slug}-jobs",

            "Cutshort":
                f"https://cutshort.io/search-jobs?"
                f"query={r}&location=India",

            "Hirist":
                f"https://www.hirist.tech/"
                f"{role_slug}-jobs",

            "Shine":
                f"https://www.shine.com/job-search/"
                f"{role_slug}-jobs",

            "TimesJobs":
                f"https://www.timesjobs.com/"
                f"candidate/job-search.html?"
                f"searchType=personalizedSearch&"
                f"txtKeywords={r}&txtLocation=India"
        }

        for portal, link in remote_links.items():

            search_links.append({
                "Role": role,
                "Portal": portal,
                "Search Type": "India Remote",
                "Search Link": link
            })


        # ----------------------------------------------------
        # KOLKATA
        # ----------------------------------------------------

        kolkata_links = {

            "Naukri":
                f"https://www.naukri.com/"
                f"{role_slug}-jobs-in-kolkata",

            "LinkedIn India":
                f"https://www.linkedin.com/jobs/search/"
                f"?keywords={r}&"
                f"location=Kolkata%2C%20West%20Bengal%2C%20India",

            "Indeed India":
                f"https://in.indeed.com/jobs?"
                f"q={r}&l=Kolkata%2C%20West%20Bengal",

            "Internshala":
                f"https://internshala.com/jobs/"
                f"{role_slug}-jobs-in-kolkata/",

            "Foundit":
                f"https://www.foundit.in/search/"
                f"{role_slug}-jobs-in-kolkata",

            "Cutshort":
                f"https://cutshort.io/search-jobs?"
                f"query={r}&location=Kolkata",

            "Hirist":
                f"https://www.hirist.tech/"
                f"{role_slug}-jobs-in-kolkata",

            "Shine":
                f"https://www.shine.com/job-search/"
                f"{role_slug}-jobs-in-kolkata",

            "TimesJobs":
                f"https://www.timesjobs.com/"
                f"candidate/job-search.html?"
                f"searchType=personalizedSearch&"
                f"txtKeywords={r}&txtLocation=Kolkata"
        }

        for portal, link in kolkata_links.items():

            search_links.append({
                "Role": role,
                "Portal": portal,
                "Search Type": "Kolkata",
                "Search Link": link
            })

    return pd.DataFrame(search_links)


# ============================================================
# 6. CHECK IF ROLE IS RELEVANT
# ============================================================

def role_is_relevant(title):

    title = str(title).lower()

    return any(
        role.lower() in title
        for role in TARGET_ROLES
    )


# ============================================================
# 7. EXPERIENCE FILTER
# ============================================================

def experience_is_allowed(text):

    text = str(text).lower()

    if text in ["", "nan", "none", "not shown"]:
        return True

    # Examples: 0-3 years, 2-5 years, 3 to 6 years
    ranges = re.findall(
        r"(\d+)\s*(?:-|to)\s*(\d+)",
        text
    )

    if ranges:

        for low, high in ranges:

            low = int(low)
            high = int(high)

            # Reject ranges that start above our maximum
            if low > MAX_YEARS:
                return False

            # Allow ranges overlapping 0-6
            return True

    # Examples: 3+ years
    plus_values = re.findall(
        r"(\d+)\s*\+",
        text
    )

    if plus_values:

        for value in plus_values:

            if int(value) <= MAX_YEARS:
                return True

        return False

    # Examples: "5 years"
    single_values = re.findall(
        r"(\d+)\s*(?:years|year|yrs|yr)",
        text
    )

    if single_values:

        for value in single_values:

            if int(value) <= MAX_YEARS:
                return True

        return False

    # If experience isn't visible,
    # keep the job for manual checking.
    return True


# ============================================================
# 8. EXTRACT EXPERIENCE
# ============================================================

def extract_experience(text):

    patterns = [

        r"\d+\s*-\s*\d+\s*(?:years|year|yrs|yr)",

        r"\d+\s*to\s*\d+\s*(?:years|year|yrs|yr)",

        r"\d+\+\s*(?:years|year|yrs|yr)",

        r"\d+\s*(?:years|year|yrs|yr)"
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        if match:
            return match.group(0)

    return "Not shown"


# ============================================================
# 9. EXTRACT SALARY
# ============================================================

def extract_salary(text):

    patterns = [

        r"₹\s*[\d,]+(?:\s*-\s*₹?\s*[\d,]+)?",

        r"Rs\.?\s*[\d,]+(?:\s*-\s*Rs\.?\s*[\d,]+)?",

        r"\d+(?:\.\d+)?\s*-\s*\d+(?:\.\d+)?\s*LPA",

        r"\d+(?:\.\d+)?\s*LPA"
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        if match:
            return match.group(0)

    return "Not shown"


# ============================================================
# 10. EXTRACT COMPANY
# ============================================================

def extract_company(card_text, title):

    text = str(card_text)

    # Try common labels
    patterns = [

        r"company\s*[:\-]\s*([^\n|]+)",

        r"organisation\s*[:\-]\s*([^\n|]+)",

        r"organization\s*[:\-]\s*([^\n|]+)"
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        if match:
            return match.group(1).strip()[:150]

    return "Not shown"


# ============================================================
# 11. MATCHED SKILLS
# ============================================================

def find_matched_skills(text):

    text_lower = str(text).lower()

    matched = []

    for skill in TARGET_SKILLS:

        if skill.lower() in text_lower:

            matched.append(skill)

    return matched


# ============================================================
# 12. BAD LINK CHECK
# ============================================================

def valid_job_link(link):

    link = str(link).lower()

    if not (
        link.startswith("http://")
        or link.startswith("https://")
    ):
        return False

    bad_words = [
        "/login",
        "/signup",
        "/register",
        "/privacy",
        "/terms",
        "/about",
        "/contact"
    ]

    return not any(
        word in link
        for word in bad_words
    )


# ============================================================
# 13. SEARCH AND EXTRACT JOBS
# ============================================================

def search_jobs():

    search_links_df = create_search_links()

    print("=" * 60)
    print("JOB SEARCH AGENT STARTED")
    print("=" * 60)

    print("Roles:", len(TARGET_ROLES))
    print("Portals:", len(PORTALS))
    print("Search types:", len(SEARCH_TYPES))
    print("Total searches:", len(search_links_df))

    job_results = []

    for index, row in search_links_df.iterrows():

        portal = row["Portal"]
        role = row["Role"]
        search_type = row["Search Type"]
        search_url = row["Search Link"]

        print(
            f"\n[{index + 1}/{len(search_links_df)}] "
            f"{portal} | {role} | {search_type}"
        )

        try:

            response = session.get(
                search_url,
                timeout=20,
                allow_redirects=True
            )

            print("HTTP:", response.status_code)

            if response.status_code != 200:
                continue

            soup = BeautifulSoup(
                response.text,
                "html.parser"
            )

            links = soup.find_all(
                "a",
                href=True
            )

            found_for_search = 0

            for link in links:

                title = link.get_text(
                    " ",
                    strip=True
                )

                href = link.get("href")

                if not title or not href:
                    continue

                if len(title) < 5:
                    continue

                if not role_is_relevant(title):
                    continue

                application_link = urljoin(
                    search_url,
                    href
                )

                if not valid_job_link(
                    application_link
                ):
                    continue

                # ----------------------------------------
                # Surrounding job context
                # ----------------------------------------

                context_parts = [title]

                current = link

                # Walk up a few parent levels to capture
                # company, experience, salary and skills.
                for _ in range(3):

                    current = current.parent

                    if current is None:
                        break

                    parent_text = current.get_text(
                        " ",
                        strip=True
                    )

                    if parent_text:
                        context_parts.append(
                            parent_text[:2000]
                        )

                context = " ".join(
                    context_parts
                )

                context = context[:4000]

                # ----------------------------------------
                # Skills
                # ----------------------------------------

                matched_skills = find_matched_skills(
                    context
                )

                # ----------------------------------------
                # Experience
                # ----------------------------------------

                experience = extract_experience(
                    context
                )

                # ----------------------------------------
                # Salary
                # ----------------------------------------

                salary = extract_salary(
                    context
                )

                # ----------------------------------------
                # Company
                # ----------------------------------------

                company = extract_company(
                    context,
                    title
                )

                # ----------------------------------------
                # Match status
                # ----------------------------------------

                if len(matched_skills) >= 3:

                    match_status = "Strong Match"

                elif len(matched_skills) >= 1:

                    match_status = "Possible Match"

                else:

                    match_status = "Role Match"

                # ----------------------------------------
                # Match reason
                # ----------------------------------------

                match_reason = "Target role found"

                if matched_skills:

                    match_reason += (
                        " | Skills: "
                        + ", ".join(matched_skills)
                    )

                if search_type == "India Remote":

                    match_reason += (
                        " | India-wide remote"
                    )

                else:

                    match_reason += (
                        " | Kolkata"
                    )

                # ----------------------------------------
                # Save job
                # ----------------------------------------

                job_results.append({

                    "Date Found": TODAY,

                    "Job Title": title[:150],

                    "Company": company,

                    "Location": (
                        "India - Remote"
                        if search_type == "India Remote"
                        else "Kolkata"
                    ),

                    "Experience": experience,

                    "Salary": salary,

                    "Skills": ", ".join(
                        TARGET_SKILLS
                    ),

                    "Matched Skills": ", ".join(
                        matched_skills
                    ),

                    "Match Status": match_status,

                    "Match Reason": match_reason,

                    "Application Link": application_link,

                    "Status": "Not Applied",

                    "Source": portal,

                    "Search Type": search_type
                })

                found_for_search += 1

            print(
                "Listings extracted:",
                found_for_search
            )

        except Exception as e:

            print(
                "Error:",
                str(e)[:150]
            )

    jobs_df = pd.DataFrame(
        job_results
    )

    if jobs_df.empty:

        print("\nNo jobs extracted.")
        return jobs_df

    # Remove duplicate links
    jobs_df = jobs_df.drop_duplicates(
        subset=["Application Link"],
        keep="first"
    )

    jobs_df = jobs_df.reset_index(
        drop=True
    )

    print("\n" + "=" * 60)
    print("EXTRACTION COMPLETE")
    print("=" * 60)

    print(
        "Total jobs extracted:",
        len(jobs_df)
    )

    return jobs_df


# ============================================================
# 14. FILTER JOBS
# ============================================================

def filter_jobs(jobs_df):

    if jobs_df.empty:
        return jobs_df

    filtered = jobs_df.copy()

    # --------------------------------------------------------
    # Role
    # --------------------------------------------------------

    filtered = filtered[
        filtered["Job Title"].apply(
            role_is_relevant
        )
    ].copy()

    # --------------------------------------------------------
    # Location
    # --------------------------------------------------------

    filtered = filtered[
        filtered["Search Type"].isin(
            SEARCH_TYPES
        )
    ].copy()

    # --------------------------------------------------------
    # Experience
    # --------------------------------------------------------

    filtered = filtered[
        filtered["Experience"].apply(
            experience_is_allowed
        )
    ].copy()

    # --------------------------------------------------------
    # Remove duplicate links
    # --------------------------------------------------------

    filtered = filtered.drop_duplicates(
        subset=["Application Link"],
        keep="first"
    )

    # --------------------------------------------------------
    # Match score
    # --------------------------------------------------------

    def calculate_score(row):

        score = 0

        title = str(
            row["Job Title"]
        ).lower()

        matched_skills = str(
            row["Matched Skills"]
        ).strip()

        # Target role
        if any(
            role.lower() in title
            for role in TARGET_ROLES
        ):
            score += 40

        # Skills
        if matched_skills:

            skill_count = len([
                s for s in matched_skills.split(",")
                if s.strip()
            ])

            score += min(
                skill_count * 10,
                40
            )

        # Allowed location
        score += 20

        return min(score, 100)

    filtered["Match Score"] = filtered.apply(
        calculate_score,
        axis=1
    )

    # --------------------------------------------------------
    # Sort
    # --------------------------------------------------------

    filtered = filtered.sort_values(
        by="Match Score",
        ascending=False
    )

    filtered = filtered.reset_index(
        drop=True
    )

    return filtered


# ============================================================
# 15. CLEAN DATA
# ============================================================

def clean_jobs(jobs_df):

    if jobs_df.empty:
        return jobs_df

    clean_df = jobs_df.copy()

    text_columns = [
        "Job Title",
        "Company",
        "Location",
        "Experience",
        "Salary",
        "Matched Skills",
        "Source",
        "Search Type",
        "Application Link"
    ]

    for col in text_columns:

        if col in clean_df.columns:

            clean_df[col] = (
                clean_df[col]
                .fillna("")
                .astype(str)
                .str.replace(
                    r"\s+",
                    " ",
                    regex=True
                )
                .str.strip()
            )

    # Blank values
    for col in [
        "Company",
        "Experience",
        "Salary"
    ]:

        clean_df[col] = clean_df[col].replace(
            "",
            "Not shown"
        )

    # Salary
    clean_df["Salary"] = (
        clean_df["Salary"]
        .str.replace(
            "Rs.",
            "₹",
            regex=False
        )
        .str.replace(
            "Rs",
            "₹",
            regex=False
        )
        .str.replace(
            "INR",
            "₹",
            regex=False
        )
    )

    # Matched skills
    def clean_skills(value):

        if str(value).strip() in [
            "",
            "nan",
            "None"
        ]:
            return "None"

        skills = [
            s.strip()
            for s in str(value).split(",")
            if s.strip()
        ]

        skills = list(
            dict.fromkeys(skills)
        )

        return ", ".join(skills)

    clean_df["Matched Skills"] = (
        clean_df["Matched Skills"]
        .apply(clean_skills)
    )

    # Application links
    clean_df["Application Link"] = (
        clean_df["Application Link"]
        .astype(str)
        .str.strip()
    )

    # Date
    clean_df["Date Found"] = TODAY

    # Final column order
    final_columns = [
        "Date Found",
        "Job Title",
        "Company",
        "Location",
        "Experience",
        "Salary",
        "Matched Skills",
        "Match Status",
        "Match Reason",
        "Application Link",
        "Status",
        "Source",
        "Search Type",
        "Match Score"
    ]

    clean_df = clean_df[
        [
            col for col in final_columns
            if col in clean_df.columns
        ]
    ]

    return clean_df.reset_index(
        drop=True
    )


# ============================================================
# 16. CONNECT TO GOOGLE SHEET
# ============================================================

def connect_google_sheet():

    service_account_json = os.environ.get(
        "GOOGLE_SERVICE_ACCOUNT_JSON"
    )

    sheet_id = os.environ.get(
        "GOOGLE_SHEET_ID"
    )

    if not service_account_json:

        raise ValueError(
            "GOOGLE_SERVICE_ACCOUNT_JSON secret is missing."
        )

    if not sheet_id:

        raise ValueError(
            "GOOGLE_SHEET_ID secret is missing."
        )

    credentials_info = json.loads(
        service_account_json
    )

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    credentials = (
        Credentials
        .from_service_account_info(
            credentials_info,
            scopes=scopes
        )
    )

    gc = gspread.authorize(
        credentials
    )

    spreadsheet = gc.open_by_key(
        sheet_id
    )

    worksheet = spreadsheet.sheet1

    return spreadsheet, worksheet


# ============================================================
# 17. ADD ONLY NEW JOBS
# ============================================================

def upload_new_jobs(
    worksheet,
    clean_df
):

    if clean_df.empty:

        print(
            "No jobs available to upload."
        )

        return 0

    # --------------------------------------------------------
    # Read existing sheet
    # --------------------------------------------------------

    existing_data = (
        worksheet.get_all_records()
    )

    existing_df = pd.DataFrame(
        existing_data
    )

    print(
        "Existing jobs in Google Sheet:",
        len(existing_df)
    )

    # --------------------------------------------------------
    # Existing application links
    # --------------------------------------------------------

    if (
        not existing_df.empty
        and "Application Link"
        in existing_df.columns
    ):

        existing_links = set(
            existing_df[
                "Application Link"
            ]
            .dropna()
            .astype(str)
            .str.strip()
        )

    else:

        existing_links = set()

    # --------------------------------------------------------
    # Keep only new jobs
    # --------------------------------------------------------

    new_jobs = clean_df[
        ~clean_df[
            "Application Link"
        ].isin(existing_links)
    ].copy()

    # Remove duplicates inside today's results
    new_jobs = new_jobs.drop_duplicates(
        subset=["Application Link"],
        keep="first"
    )

    print(
        "New jobs to add:",
        len(new_jobs)
    )

    if new_jobs.empty:

        print(
            "No new jobs found today."
        )

        return 0

    # --------------------------------------------------------
    # Append to bottom
    # --------------------------------------------------------

    existing_rows = len(
        worksheet.get_all_values()
    )

    start_row = existing_rows + 1

    values = new_jobs.values.tolist()

    worksheet.update(
        range_name=(
            f"A{start_row}:"
            f"{chr(64 + len(new_jobs.columns))}"
            f"{start_row + len(values) - 1}"
        ),
        values=values
    )

    print(
        "Successfully added:",
        len(new_jobs),
        "new jobs."
    )

    return len(new_jobs)


# ============================================================
# 18. MAIN AGENT
# ============================================================

def main():

    print()
    print("=" * 60)
    print("🤖 JOB SEARCH AGENT")
    print("=" * 60)
    print(
        "Date:",
        TODAY
    )
    print(
        "Experience:",
        "0-6 years"
    )
    print(
        "Location:",
        "India Remote + Kolkata"
    )
    print("=" * 60)

    # Search
    jobs_df = search_jobs()

    if jobs_df.empty:
        print(
            "\nAgent finished: no jobs extracted."
        )
        return

    # Filter
    filtered_df = filter_jobs(
        jobs_df
    )

    print(
        "\nJobs after filtering:",
        len(filtered_df)
    )

    if filtered_df.empty:

        print(
            "Agent finished: no jobs matched "
            "the current criteria."
        )

        return

    # Clean
    clean_df = clean_jobs(
        filtered_df
    )

    # Backup CSV
    clean_df.to_csv(
        "clean_job_results.csv",
        index=False
    )

    print(
        "CSV backup created."
    )

    # Google Sheet
    spreadsheet, worksheet = (
        connect_google_sheet()
    )

    print(
        "Google Sheet connected:",
        spreadsheet.title
    )

    added = upload_new_jobs(
        worksheet,
        clean_df
    )

    print()
    print("=" * 60)
    print("✅ JOB AGENT FINISHED")
    print("=" * 60)
    print(
        "Jobs found:",
        len(clean_df)
    )
    print(
        "New jobs added:",
        added
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()
