from fastapi import FastAPI, Query, Body, Header, status
from starlette import status
from starlette.responses import Response
from fastapi.responses import JSONResponse

from fastapi.middleware.cors import CORSMiddleware

from functools import lru_cache

from pydantic import BaseSettings

from typing import List, Optional

import json

from models.nodes import \
    Node, \
    CRUDNode, \
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
        # "description": "",
        # "externalDocs": {
        #     "description": "",
        #     "url": "",
        # },
    },
]

app = FastAPI(
    title="Vector conf",
    description="API to operate with a Vector config",
    version="0.8.0",
    openapi_tags=tags_metadata
)  # noqa: pylint=invalid-name

origins = [
    "http://127.0.0.1:3000",
    "http://localhost",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Range"]
)

app.state.vector_conf = {
    "default": Conf()
}



# Fake config data to operate with:
src = """
[sources.nginx_error_log] 
type = 'file' 
include = ['/var/log/nginx*.log'] 
start_at_beginning = false 
ignore_older = 86400
[transforms.nginx_error_parser] 
inputs = ['nginx_error_log'] 
type = 'tokenizer' 
field_names = ['timestamp', 'message']
[transforms.nginx_transaction_sampler] 
inputs = ['nginx_error_parser'] 
type = 'sampler' 
key_field = 'request_id' 
rate = 10
[sinks.es_cluster] 
inputs = ['nginx_transaction_sampler'] 
type = 'elasticsearch' 
host = '123.123.123.123:5000'
"""


@app.on_event("startup")
async def startup():
    conf = app.state.vector_conf["default"]
    conf.deserialize(src)


@app.on_event("shutdown")
async def shutdown():
    pass


@app.post("/conf/{item_id}/text")
def load_conf(item_id: str, conf: ConfLoad):
    try:
        model = Conf()
        model.deserialize(conf.text)
        app.state.vector_conf[item_id] = model
        return JSONResponse(status_code=status.HTTP_201_CREATED, content="Ok")
    except Exception as e:
        return JSONResponse(status_code=500, content=str(e))


@app.get("/conf/{item_id}/text")
def get_conf(item_id: str):
    model = app.state.vector_conf[item_id]
    text = model.serialize()
    return JSONResponse(status_code=status.HTTP_200_OK, content={"toml": text})


@app.get("/conf/{conf_id}/items", response_model=List[CRUDNode])
def list_items(conf_id: str, sort: str=None, range: str=None, filter: str=None):
    range_vals, sort_vals, filter_obj = None, None, None
    if range:
        range_vals = [int(i) for i in list(json.loads(range))]
    if sort:
        sort = json.loads(sort)
    if filter:
        filter = json.loads(filter)
    model = app.state.vector_conf[conf_id]
    items = model.items.copy()
    js = [item.display_dict() for item in items]
    headers = {}
    if range_vals:
        lo, hi = range_vals
        total_len = len(js)
        hi = min(hi, total_len)
        js = js[lo: hi]
        headers = { 'Content-Range': f'posts : {lo}-{hi}/{total_len}'}
    return JSONResponse(status_code=status.HTTP_200_OK, content=js, headers=headers)


