from fastapi.middleware.cors import CORSMiddleware

def add_middlewares(app):
    """
    Add middlewares to the FastAPI app.
    """

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # or ["*"] for all origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )