"""API routing for the P7 backend."""
from ninja import NinjaAPI

from p7.get_dropbox_files.api import fetch_dropbox_files_router
from p7.get_google_drive_files.api import fetch_google_drive_files_router
from p7.get_onedrive_files.api import fetch_onedrive_files_router

from p7.download_google_drive_files.api import download_google_drive_files_router
from p7.download_dropbox_files.api import download_dropbox_files_router

from p7.sync_files.api import sync_files_router
from p7.create_user.api import create_user_router
from p7.delete_user.api import delete_user_router
from p7.find_services.api import find_services_router
from p7.create_service.api import create_service_router
from p7.find_user_by_email.api import find_user_by_email_router
from p7.search_files_by_filename.api import search_files_by_filename_router

api = NinjaAPI()

api.add_router("/fetch_dropbox_files/", fetch_dropbox_files_router)
api.add_router("/fetch_google_drive_files/", fetch_google_drive_files_router)
api.add_router("/fetch_onedrive_files/", fetch_onedrive_files_router)

api.add_router("/download_google_drive_files/", download_google_drive_files_router)
api.add_router("/download_dropbox_files/", download_dropbox_files_router)

api.add_router("/sync_files/", sync_files_router)

api.add_router("/find_user_by_email/", find_user_by_email_router)
api.add_router("/delete_user/", delete_user_router)
api.add_router("/create_user/", create_user_router)
api.add_router("/create_service/", create_service_router)
api.add_router("/find_service/", find_services_router)
api.add_router("/search_files_by_filename/", search_files_by_filename_router)
