"""API routing for the P7 backend."""
from ninja import NinjaAPI
from .getDropboxFiles.api import router as dropbox_router
from .getOnedriveFiles.api import router as onedrive_router


api = NinjaAPI()


api.add_router("/getDropboxFiles/", dropbox_router)
api.add_router("/getOnedriveFiles/", onedrive_router)
# You can add other routers similarly
