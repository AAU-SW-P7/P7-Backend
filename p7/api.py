"""API routing for the P7 backend."""
from ninja import NinjaAPI
# from getDropboxFiles.api import router as dropbox_router
from p7.get_dropbox_files.api import fetch_dropbox_files_router
from p7.get_google_drive.api import fetch_google_drive_files_router
from p7.get_onedrive_files.api import fetch_onedrive_files_router

from repository.service import create_user_router, find_user_by_email_router, create_service_router, find_services_router

api = NinjaAPI()

api.add_router("/fetch_dropbox_files/", fetch_dropbox_files_router)
api.add_router("/fetch_google_drive_files/", fetch_google_drive_files_router)
api.add_router("/fetch_onedrive_files/", fetch_onedrive_files_router)

api.add_router("/find_user_by_email/", find_user_by_email_router)
api.add_router("/create_user/", create_user_router)
api.add_router("/create_service/", create_service_router)
api.add_router("/find_service/", find_services_router)
# api.add_router("/getDropboxFiles/", dropbox_router)
# You can add other routers similarly
