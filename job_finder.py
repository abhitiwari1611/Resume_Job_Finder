import os
import requests
import json
from dotenv import load_dotenv
from openai import OpenAI

# Load ENV
load_dotenv()

OPENAI_KEY = os.getenv("OPENAI_API_KEY")
RAPID_KEY = os.getenv("RAPIDAPI_KEY")
RAPID_HOST = os.getenv("RAPIDAPI_HOST")

client = OpenAI(api_key=OPENAI_KEY)

# -----------------------------
# Search LIVE JOBS
# -----------------------------
def search_jobs(query, location="India"):
    url = "https://jsearch.p.rapidapi.com/search"

    headers = {
        "x-rapidapi-key": RAPID_KEY,
        "x-rapidapi-host": RAPID_HOST
    }

    params = {
        "query": f"{query} in {location}",
        "num_pages": "1"
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    return response.json().get("data", [])

# -----------------------------
# AI MATCH & SCORING
# -----------------------------
def score_job(profile, job):
    prompt = f"""
Candidate profile:
{profile}

Job Title: {job.get('job_title')}
Company: {job.get('employer_name')}
Description: {job.get('job_description')}

Return JSON format:
{{
  "score": "0-100",
  "reason": "why matched",
  "message": "short linkedin message"
}}
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "You are a job matching AI"},
            {"role": "user", "content": prompt}
        ]
    )

    return json.loads(response.choices[0].message.content)

# -----------------------------
# MAIN AUTOMATION
# -----------------------------
def run_job_matcher():
    profile = input("Paste your PROFILE SUMMARY from job_plan.md:\n")

    jobs = search_jobs("Data Analyst Internship")
    print(f"\n{len(jobs)} jobs found...\n")

    final = []

    for job in jobs[:15]:
        result = score_job(profile, job)

        final.append({
            "title": job.get("job_title"),
            "company": job.get("employer_name"),
            "score": result["score"],
            "reason": result["reason"],
            "message": result["message"],
            "link": job.get("job_apply_link")
        })

        print(f"✅ {job.get('job_title')} | Score: {result['score']}")

    # SAVE RESULTS
    with open("matched_jobs.json", "w", encoding="utf8") as f:
        json.dump(final, f, indent=2)

    print("\n🎉 Saved as matched_jobs.json")

if __name__ == "__main__":
    run_job_matcher()
