# """
# Device discovery core logic.
# Automatically detects OS and calls appropriate platform module.
# """

# import platform
# from platforms.platform_windows import WindowsPlatform
# from pathlib import Path
# import string

# class DeviceDiscovery:
#     @staticmethod
#     def list_drives():
#         drives = []
#         for letter in string.ascii_uppercase:
#             drive = Path(f"{letter}:/")
#             if drive.exists():
#                 drives.append(drive)
#         return drives

#     @staticmethod
#     def get_user_home():
#         return Path.home()

#     @staticmethod
#     def list_user_folders():
#         user_home = Path.home()
#         return [f for f in user_home.iterdir() if f.is_dir()]
#     def __init__(self, platform_handler=None):
#         self.platform_handler = platform_handler
#         self.current_os = platform.system()
    
#     def list_devices(self):
#         if self.current_os == "Windows":
#             return WindowsPlatform.list_devices()
#         elif self.current_os == "Linux":
#             print("Linux support coming soon.")
#             return []
#         elif self.current_os == "Darwin":
#             print("macOS support coming soon.")
#             return []
#         else:
#             raise Exception(f"Unsupported OS: {self.current_os}")
#     def scan_directory(self, path: str):
#         files = []
#         path_obj = Path(path)

#         if not path_obj.exists():
#             return files

#         for item in path_obj.iterdir():
#             if item.is_file():
#                 files.append({
#                     "path": str(item),
#                     "size": item.stat().st_size
#                 })

#         return files

import platform
from pathlib import Path
import string


class DeviceDiscovery:

    @staticmethod
    def list_drives():
        system = platform.system()

        # ---------------------------
        # WINDOWS
        # ---------------------------
        if system == "Windows":
            drives = []
            for letter in string.ascii_uppercase:
                drive = Path(f"{letter}:/")
                if drive.exists():
                    drives.append(drive)
            return drives

        # ---------------------------
        # LINUX
        # ---------------------------
        elif system == "Linux":
            drives = [Path("/")]

            # /mnt and /media are common mount points
            for base in ["/mnt", "/media"]:
                base_path = Path(base)
                if base_path.exists():
                    for item in base_path.iterdir():
                        if item.is_dir():
                            drives.append(item)

            return drives

        # ---------------------------
        # macOS
        # ---------------------------
        elif system == "Darwin":
            drives = [Path("/")]

            volumes = Path("/Volumes")
            if volumes.exists():
                for item in volumes.iterdir():
                    if item.is_dir():
                        drives.append(item)

            return drives

        # ---------------------------
        # UNKNOWN OS
        # ---------------------------
        else:
            return [Path("/")]

    @staticmethod
    def get_user_home():
        return Path.home()

    @staticmethod
    def list_user_folders():
        user_home = Path.home()
        return [f for f in user_home.iterdir() if f.is_dir()]

    def __init__(self, platform_handler=None):
        self.platform_handler = platform_handler
        self.current_os = platform.system()

    def list_devices(self):
        # Now just reuse list_drives()
        return self.list_drives()

    def scan_directory(self, path: str):
        files = []
        path_obj = Path(path)

        if not path_obj.exists():
            return files

        for item in path_obj.iterdir():
            if item.is_file():
                files.append({
                    "path": str(item),
                    "size": item.stat().st_size
                })

        return files