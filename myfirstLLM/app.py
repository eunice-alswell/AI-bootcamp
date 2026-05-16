from fastapi import FastAPI
import random

from main import generate_information, models

app = FastAPI()


@app.get("/")
async def home():
    model = random.choice(models)

    response = generate_information(
        "What is the capital of France?",
        model
    )

    return {
        "model": model,
        "response": response
    }

