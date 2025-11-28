import os
from pathlib import Path
import json

from dotenv import load_dotenv
from pypdf import PdfReader
from openai import OpenAI

# 1) Load environment variables from .env
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("Please set OPENAI_API_KEY in your .env file")

client = OpenAI(api_key=OPENAI_API_KEY)


# 2) Helper: read resume PDF
def extract_text_from_pdf(file_path: str) -> str:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Resume file not found: {file_path}")

    reader = PdfReader(str(path))
    texts = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        texts.append(page_text)

    full_text = "\n".join(texts)
    # Light cleaning
    return " ".join(full_text.split())


# 3) Call ChatGPT to build a career plan + job search strategy
def analyze_resume_with_gpt(resume_text: str) -> dict:
    """
    Ask ChatGPT to:
    - understand your profile
    - suggest roles & internships
    - give job search queries
    - write outreach messages
    """

    instructions = (
        "You are an expert career coach helping a student/early-career candidate.\n"
        "You will receive RAW RESUME TEXT. It may be messy.\n"
        "You must return a JSON object ONLY (no extra text) with this exact schema:\n"
        "{\n"
        '  "profile_summary": "2-3 sentence summary of candidate",\n'
        '  "best_fit_roles": ["role1", "role2", ...],\n'
        '  "internship_ideas": ["internship type 1", "internship type 2", ...],\n'
        '  "key_skills": ["skill1", "skill2", ...],\n'
        '  "suggested_job_search_queries": ["query to use on LinkedIn/Naukri", ...],\n'
        '  "application_strategy": "step-by-step strategy for next 4 weeks to get interviews",\n'
        '  "outreach_messages": [\n'
        '     "short message to send to a recruiter on LinkedIn",\n'
        '     "short message to send to a hiring manager",\n'
        '     "short email-style message for cold outreach"\n'
        "  ]\n"
        "}\n"
        "Be very concrete and practical. Focus on roles and queries where the candidate is likely to hear back."
    )

    response = client.responses.create(
        model="gpt-5.1-mini",  # use gpt-4.1-mini / gpt-4.1 if you have access
        instructions=instructions,
        input=resume_text,
    )

    # New OpenAI client returns output in a structured way
    # We grab the text part and parse JSON
    content = response.output[0].content[0].text  # type: ignore
    data = json.loads(content)
    return data


# 4) Pretty print and also save to a text/markdown file
def save_and_show_results(results: dict, output_path: str = "job_plan.md"):
    lines = []

    lines.append("# Resume-Based Job & Internship Plan\n")

    lines.append("## 🧾 Profile Summary\n")
    lines.append(results.get("profile_summary", "") + "\n")

    lines.append("## 🎯 Best Fit Roles\n")
    for role in results.get("best_fit_roles", []):
        lines.append(f"- {role}")
    lines.append("")

    lines.append("## 🧪 Internship Ideas\n")
    for idea in results.get("internship_ideas", []):
        lines.append(f"- {idea}")
    lines.append("")

    lines.append("## 🛠️ Key Skills (according to resume)\n")
    for skill in results.get("key_skills", []):
        lines.append(f"- {skill}")
    lines.append("")

    lines.append("## 🔍 Job Search Queries (use on LinkedIn / Naukri / Indeed)\n")
    for q in results.get("suggested_job_search_queries", []):
        lines.append(f"- `{q}`")
    lines.append("")

    lines.append("## 📅 4-week Application Strategy\n")
    lines.append(results.get("application_strategy", "") + "\n")

    lines.append("## 💬 Outreach Messages\n")
    for i, msg in enumerate(results.get("outreach_messages", []), start=1):
        lines.append(f"### Message {i}\n")
        lines.append(msg)
        lines.append("")

    output_text = "\n".join(lines)

    # Save to file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output_text)

    print("\n============================")
    print("Plan generated and saved to:", output_path)
    print("============================\n")
    print(output_text[:2000])  # show first 2000 chars in console


def main():
    # 1) Ask for resume path (with default)
    default_path = "data/resume.pdf"
    print("Enter path to your resume PDF "
          f"(press Enter to use default: {default_path})")
    user_input = input("> ").strip()

    resume_path = user_input or default_path

    print("\n📄 Reading resume:", resume_path)
    resume_text = extract_text_from_pdf(resume_path)

    print("\n🤖 Sending resume to ChatGPT for analysis...")
    results = analyze_resume_with_gpt(resume_text)

    print("\n📝 Saving results...")
    save_and_show_results(results, output_path="job_plan.md")


if __name__ == "__main__":
    main()
