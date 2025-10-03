"""API routing for the P7 backend."""
from ninja import NinjaAPI
from .get_dropbox_files.api import router as dropbox_router
from .get_onedrive_files.api import router as onedrive_router
from .get_google_drive.api import router as google_drive_router


api = NinjaAPI()


api.add_router("/getDropboxFiles/", dropbox_router)
api.add_router("/getOnedriveFiles/", onedrive_router)
api.add_router("/getGoogleDrive/", google_drive_router)
# You can add other routers similarly
