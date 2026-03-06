# cloud_service.py
from abc import ABC, abstractmethod

class CloudService(ABC):
    @abstractmethod
    def list_files(self, page_size=10):
        """List files and storage info."""
        pass

    @abstractmethod
    def upload_file(self, file_path):
        """Uploads the given file."""
        pass

    @abstractmethod
    def download_file(self, file_id, save_dir):
        """Downloads the file with the given ID to save_dir."""
        pass

    @abstractmethod
    def get_storage_info(self):
        """Returns a tuple (used, total) as formatted strings."""
        pass

    @abstractmethod
    def get_remaining_space(self):
        """Returns the remaining space in bytes."""
        pass

    @abstractmethod
    def format_size(self, size_in_bytes):
        """Formats the given size in bytes into a human-readable string."""
        pass
