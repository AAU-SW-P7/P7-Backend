"""API routing for the P7 backend."""
from ninja import NinjaAPI
from p7.get_dropbox_files.api import fetch_dropbox_files_router, sync_dropbox_files_router
from p7.get_google_drive.api import fetch_google_drive_files_router, sync_google_drive_files_router
from p7.get_onedrive_files.api import fetch_onedrive_files_router, sync_onedrive_files_router
from p7.create_user.api import create_user_router
from p7.find_services.api import find_services_router
from p7.create_service.api import create_service_router
from p7.find_user_by_email.api import find_user_by_email_router
api = NinjaAPI()

api.add_router("/fetch_dropbox_files/", fetch_dropbox_files_router)
api.add_router("/fetch_google_drive_files/", fetch_google_drive_files_router)
api.add_router("/fetch_onedrive_files/", fetch_onedrive_files_router)

api.add_router("/sync_dropbox_files/", sync_dropbox_files_router)
api.add_router("/sync_google_drive_files/", sync_google_drive_files_router)
api.add_router("/sync_onedrive_files/", sync_onedrive_files_router)

api.add_router("/find_user_by_email/", find_user_by_email_router)
api.add_router("/create_user/", create_user_router)
api.add_router("/create_service/", create_service_router)
api.add_router("/find_service/", find_services_router)
