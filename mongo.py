import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = os.getenv('MONGO_URI', 'mongodb+srv://Abhijit:RStoKAluIWB4x1Pg@cluster0.zvgvv7n.mongodb.net/')
MONGO_DB = os.getenv('MONGO_DB', 'insurance_ai')


async def connect_to_mongo(app):
    """Attach a Motor client and selected DB to the FastAPI app state."""
    # creating AsyncIOMotorClient is thread-safe and non-blocking for our usage
    client = AsyncIOMotorClient(MONGO_URI)
    app.state.mongo_client = client
    app.mongodb = client[MONGO_DB]


async def close_mongo(app):
    client = getattr(app.state, 'mongo_client', None)
    if client:
        client.close()


def get_collection(app_or_request, name: str):
    """Helper to retrieve a collection from the attached DB.

    Accepts either the FastAPI `app` or `request` object that has `.app` attribute.
    """
    app = getattr(app_or_request, 'app', app_or_request)
    return app.mongodb[name]
