"""API routing for the P7 backend."""

from ninja import NinjaAPI

from p7.get_dropbox_files.api import fetch_dropbox_files_router
from p7.get_google_drive_files.api import fetch_google_drive_files_router
from p7.get_onedrive_files.api import fetch_onedrive_files_router
from p7.get_local_files.api import fetch_local_files_router
from p7.test_prepare_download_google_drive_files.api import fetch_test_prepare_download_google_drive_files_router

from p7.download_dropbox_files.api import download_dropbox_files_router
from p7.download_onedrive_files.api import download_onedrive_files_router
from p7.download_google_drive_files.api import download_google_drive_files_router
from p7.download_local_files.api import download_local_files_router
from p7.test_download_files.api import test_download_files_router

from p7.sync_files.api import sync_files_router
from p7.create_user.api import create_user_router
from p7.delete_user.api import delete_user_router
from p7.find_services.api import find_services_router
from p7.find_services_tokens.api import find_services_tokens_router
from p7.create_service.api import create_service_router
from p7.find_user_by_email.api import find_user_by_email_router
from p7.search.api import search_router

api = NinjaAPI()

api.add_router("/fetch_dropbox_files/", fetch_dropbox_files_router)
api.add_router("/fetch_google_drive_files/", fetch_google_drive_files_router)
api.add_router("/fetch_onedrive_files/", fetch_onedrive_files_router)
api.add_router("/fetch_local_files/", fetch_local_files_router)
api.add_router("/fetch_test_prepare_download_google_drive_files/", fetch_test_prepare_download_google_drive_files_router)

api.add_router("/download_google_drive_files/", download_google_drive_files_router)
api.add_router("/download_dropbox_files/", download_dropbox_files_router)
api.add_router("/download_onedrive_files/", download_onedrive_files_router)
api.add_router("/download_local_files/", download_local_files_router)
api.add_router("/test_download_files/", test_download_files_router)

api.add_router("/sync_files/", sync_files_router)

api.add_router("/find_user_by_email/", find_user_by_email_router)
api.add_router("/delete_user/", delete_user_router)
api.add_router("/create_user/", create_user_router)
api.add_router("/create_service/", create_service_router)
api.add_router("/find_service/", find_services_router)
api.add_router("/find_services_tokens/", find_services_tokens_router)
api.add_router("/search/", search_router)
