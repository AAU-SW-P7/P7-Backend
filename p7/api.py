from ninja import NinjaAPI
from .hello.api import router as hello_router
from .getDropboxFiles.api import router as dropbox_router
from .getGoogleDrive.api import router as google_drive_router


api = NinjaAPI()


api.add_router("/hello/", hello_router)
api.add_router("/getDropboxFiles/", dropbox_router)
api.add_router("/getGoogleDrive/", google_drive_router)
# You can add other routers similarly
