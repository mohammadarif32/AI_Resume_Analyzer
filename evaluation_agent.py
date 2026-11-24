
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


def evaluate_answer(question, answer, question_number):

    api_key = os.getenv("GROQ_API_KEY")
    model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

    if not api_key:
        raise ValueError("GROQ_API_KEY is missing from .env")

    client = Groq(api_key=api_key)

    # Check if answer is empty or too short
    if not answer or not answer.strip() or len(answer.strip()) < 5:
        if question_number < 2:
            return (
                "Result: Not Attempted\n"
                "Score: 0/10\n"
                "Feedback: No code was provided.\n"
                "Improvement: Write code to solve the problem."
            )
        else:
            return (
                "Result: Not Attempted\n"
                "Feedback: No response was provided.\n"
                "Improvement: Provide a detailed answer."
            )

    is_coding = question_number < 2

    if is_coding:
        evaluation_rules = """
CODING QUESTION EVALUATION:

Evaluate the candidate's code based on:
- Correctness of logic
- Problem-solving approach
- Edge cases
- Time and space complexity

Return:
Result: Correct or Incorrect
Score: X/10
Logic Feedback: Explain what is right or wrong.
Improvement: Suggest one improvement.
"""
    else:
        evaluation_rules = """
NON-CODING QUESTION EVALUATION:

First decide whether the answer is relevant and technically correct.

If completely wrong or irrelevant:
Result: Incorrect
Do not provide a score.

If partially correct or correct:
Result: Correct
Score: X/10
Feedback: Brief evaluation.
Improvement: Explain how to improve the answer.
"""

    prompt = f"""
You are an expert technical interviewer.

{evaluation_rules}

Question Number: {question_number + 1}

Question:
{question}

Candidate Answer:
{answer}

Evaluate fairly. Do not assume information that the candidate
has not provided.

Return the evaluation in a clean structured format.
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

    return response.choices[0].message.content
