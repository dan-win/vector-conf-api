from fastapi import FastAPI, Query, Body, status
from starlette import status
from starlette.responses import Response
from fastapi.responses import JSONResponse

from functools import lru_cache

from pydantic import BaseSettings

from typing import List

from models.nodes import \
    Node, \
    SourceFile, \
    SourceGenerator, \
    TransformLua, \
    SinkFile, \
    SinkConsole

from models.conf import Conf, ConfLoad
# import databases

# from db.meta import ensure_schemas


# DATABASE_URL = "sqlite:///./sql_app.db"
# # DATABASE_URL = "postgresql://user:password@postgresserver/db"

# database = databases.Database(DATABASE_URL)

# ensure_schemas(DATABASE_URL)


class Settings(BaseSettings):
    app_name: str = "Vector API"
    admin_email: str
    items_per_user: int = 50


tags_metadata = [
    {
        "name": "Conf",
        "description": "The root entity for config.",
    },
    {
        "name": "SourceFile",
        # "description": "Manage items. So _fancy_ they have their own docs.",
        # "externalDocs": {
        #     "description": "Items external docs",
        #     "url": "https://fastapi.tiangolo.com/",
        # },
    },
]

app = FastAPI(
    title="Vector conf",
    description="This is a very fancy project, with auto docs for the API and everything",
    version="0.8.0",
    openapi_tags=tags_metadata
)  # noqa: pylint=invalid-name


@app.on_event("startup")
async def startup():
    pass
    # await database.connect()


@app.on_event("shutdown")
async def shutdown():
    pass
    # await database.disconnect()


# @app.post("/release/")
# async def release(*,
#                   body: Body,
#                   chat_id: str = None):
#     await proceed_release(body, chat_id)
#     return Response(status_code=status.HTTP_200_OK)


# @lru_cache()
# @app.get("/mapping/", response_model=MediaSet)
# async def release(x_country: str = Query(None, max_length=3)) -> MediaSet:
#     # await proceed_release(body, chat_id)
#     response = MediaSet(sequences=[])
#     return response


# file_root = 

db = {}

@app.post("/conf/{item_id}/text")
def load_conf(item_id: str, conf: ConfLoad):
    try:
        model = Conf()
        model.deserialize(conf.text)
        db[item_id] = model
        return JSONResponse(status_code=status.HTTP_201_CREATED, content="Ok")
    except Exception as e:
        return JSONResponse(status_code=500, content=str(e))



@app.get("/conf/{item_id}/text")
def get_conf(item_id: str):
    model = db[item_id]
    text = model.serialize()
    return JSONResponse(status_code=status.HTTP_200_OK, content={"toml": text})

@app.get("/conf/{item_id}/items", response_model=List[Node])
def list_items(item_id: str):
    model = db[item_id]
    items = model.items.copy()
    js = [item.dict() for item in items]
    return JSONResponse(status_code=status.HTTP_200_OK, content=js)


