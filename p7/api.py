from ninja import NinjaAPI
from .hello.api import router as hello_router
from .getDropboxFiles.api import router as dropbox_router


api = NinjaAPI()


api.add_router("/hello/", hello_router)
api.add_router("/getDropboxFiles/", dropbox_router)
# You can add other routers similarly