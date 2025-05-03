# classify.py

import openai
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

async def classify_urgency(symptoms: str) -> str:
    prompt = f"""
You are an expert mental health triage AI. Classify the urgency level of the following user-described symptoms into one of three categories: LOW, MEDIUM, or HIGH.

User symptoms:
\"\"\"
{symptoms}
\"\"\"

Respond with only the urgency level (LOW, MEDIUM, or HIGH).
"""
    try:
        response = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful mental health assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=5,
            temperature=0.3,
        )
        urgency = response.choices[0].message.content.strip().upper()
        if urgency in {"LOW", "MEDIUM", "HIGH"}:
            return urgency
        else:
            return "LOW"
    except Exception as e:
        print("OpenAI error:", e)
        return "LOW"
