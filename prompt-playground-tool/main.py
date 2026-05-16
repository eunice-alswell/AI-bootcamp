import os
import random

from dotenv import load_dotenv
# from fastapi import FastAPI
from groq import Groq

from prompt_styles import PROMPT_STYLES
from available_ai_models import models

load_dotenv()

#  set up the Groq client
GROQ_API_KEY = os.getenv("groq_api_key")

groq_client = Groq(api_key=GROQ_API_KEY)

def generate_information(question, model, style, temperature=0.0 ):

    systems_prompt = PROMPT_STYLES[style]
    try:
        response = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": systems_prompt},
                {"role": "user", "content": question},  
            ],
            model=model,
            temperature=temperature
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating information: {str(e)}")
        return "I don't know."
    

def stream_information(question, model, style, temperature=0.0):

    systems_prompt = PROMPT_STYLES[style]
    try:
        stream = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": systems_prompt},
                {"role": "user", "content": question},  
            ],
            model=model,
            temperature=temperature,
            stream=True
        )
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content

    except Exception as e:
        print(f"Error generating information: {str(e)}")
        yield "I don't know."
    
def main():
    model = random.choice(models)
    styles = list(PROMPT_STYLES.keys())

    question = input("Enter your question: ")

    for style in styles:
        print(f"\n--- Style: {style} ---")
        answer = generate_information(question, model, style)
        streamed_answer = stream_information(question, model, style)
        print(answer)
        print("\nStreamed Answer:")
        for chunk in streamed_answer:
            print(chunk, end="", flush=True)

if __name__ == "__main__":
    main()
