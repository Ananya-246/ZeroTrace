import subprocess
import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.device_info import DeviceInfo


class MacOSPlatform:

    @staticmethod
    def is_removable(path: str) -> bool:
        devices = MacOSPlatform.list_devices()
        for device in devices:
            if device.path.rstrip('/') == path.rstrip('/'):
                return device.is_removable
        return False

    @staticmethod
    def list_devices():
        devices = []
        try:
            # Use diskutil to list all disks in JSON format
            result = subprocess.run(
                ["diskutil", "list", "-plist", "physical"],
                capture_output=True,
                text=True
            )

            # Parse the plist output using plutil
            plist_result = subprocess.run(
                ["plutil", "-convert", "json", "-o", "-", "-"],
                input=result.stdout,
                capture_output=True,
                text=True
            )
            disk_list = json.loads(plist_result.stdout)

            all_disks = disk_list.get("AllDisksAndPartitions", [])

            for disk in all_disks:
                disk_id = disk.get("DeviceIdentifier")  # e.g. "disk0"
                if not disk_id:
                    continue

                disk_path = f"/dev/{disk_id}"

                # Get detailed info for each disk
                info_result = subprocess.run(
                    ["diskutil", "info", "-plist", disk_path],
                    capture_output=True,
                    text=True
                )
                info_json = subprocess.run(
                    ["plutil", "-convert", "json", "-o", "-", "-"],
                    input=info_result.stdout,
                    capture_output=True,
                    text=True
                )

                if info_json.returncode != 0:
                    continue

                info = json.loads(info_json.stdout)

                name        = info.get("VolumeName") or disk_id
                size        = int(info.get("TotalSize", 0))
                filesystem  = info.get("FilesystemType") or info.get("Content", "Unknown")
                mount_point = info.get("MountPoint") or disk_path

                # macOS removable-media heuristics:
                # Ejectable or External flags indicate removable drives
                is_ejectable = info.get("Ejectable", False)
                is_external  = info.get("BusProtocol", "").lower() in (
                    "usb", "firewire", "thunderbolt", "sd"
                )
                is_removable = is_ejectable or is_external

                device = DeviceInfo(
                    name=name,
                    path=disk_path,
                    size=size,
                    filesystem=filesystem,
                    is_removable=is_removable,
                    mount_point=mount_point
                )
                devices.append(device)

        except Exception as e:
            print("Error detecting macOS devices:", e)

        return devices