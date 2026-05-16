import os
import random

import groq
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

#  set up the Groq client
GROQ_API_KEY = os.getenv("groq_api_key")
groq_client = Groq(api_key=GROQ_API_KEY)

sys_prompt = """
        You are a helpful assistant that answers questions 
        about the world. You have access to a knowledge base of facts about 
        the world, and you can use this knowledge base to answer questions. 
        You should use the knowledge base to answer questions, 
        and you should not make up answers that are not in the knowledge base. 
        If you don't know the answer to a question, you should say "I don't know".
    """
models = [
    "qwen/qwen3-32b",
    "openai/gpt--oss-20b",
    "llama-3.3-70b-versatile",
    "gamma2-9b-it",
]

def generate_information(question, model, temperature=0.0):
    """  generate a response to the question using the Groq client """
    try:
        response = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": question},  
            ],
            model=model,
            temperature=temperature
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating information: {str(e)}")
        return "I don't know."

if __name__ == "__main__":
    model = random.choice(models)
    question = "What is the capital of France?"
    print(generate_information(question, model))