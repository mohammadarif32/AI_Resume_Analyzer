
import os
import re
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

def generate_questions(role, skills, projects, experience):

    api_key = os.getenv("GROQ_API_KEY")
    model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

    if not api_key:
        raise ValueError("GROQ_API_KEY is missing from .env")

    client = Groq(api_key=api_key)

    has_experience = bool(experience)

    question_count = 15 if has_experience else 12

    prompt = f"""
You are an expert technical interviewer.

Role: {role}
Skills: {skills}
Projects: {projects}
Experience: {experience}

Generate exactly {question_count} interview questions.

Follow this exact order:

1. Question 1 - DSA Coding Question (Easy)
2. Question 2 - DSA Coding Question (Medium)

The first two coding questions MUST include:
- Problem statement
- Input
- Output
- Constraints

3-6: Skill-based questions based on candidate skills.
7-10: Project-based questions based on candidate projects.

"""

    if has_experience:
        prompt += """
11-13: Experience-based questions based on candidate work experience.
14-15: HR questions.
"""
    else:
        prompt += """
11-12: HR questions.
"""

    prompt += """
CRITICAL RULES:

- Generate EXACTLY the required number of questions.
- Questions 1 and 2 must be coding questions.
- Questions 3 onwards must be non-coding questions.
- Do not generate any additional coding questions.
- Do not print instructions or explanations.
- Return only numbered questions.
"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    questions_text = response.choices[0].message.content

    lines = questions_text.split("\n")

    questions = []
    current_question = ""

    for line in lines:

        line = line.strip()

        if not line:
            continue

        if re.match(r"^\d+\.\s", line):

            if current_question:
                questions.append(current_question.strip())

            current_question = line

        else:
            current_question += " " + line

    if current_question:
        questions.append(current_question.strip())

    questions = questions[:question_count]

    return questions
