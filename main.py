from fastapi import FastAPI

app = FastAPI()


@app.get("/book")
def get_books():
    return 
