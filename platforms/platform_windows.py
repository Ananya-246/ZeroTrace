import subprocess
import csv
from io import StringIO
from core.device_info import DeviceInfo


class WindowsPlatform:

    @staticmethod
    def is_removable(path: str) -> bool:
        devices = WindowsPlatform.list_devices()
        for device in devices:
            if device.path.upper() == path.upper():
                return device.is_removable
        return False
    def list_devices():
        devices = []

        try:
            command = [
                "wmic",
                "logicaldisk",
                "get",
                "Name,DriveType,Size",
                "/format:csv"
            ]

            result = subprocess.run(
                command,
                capture_output=True,
                text=True
            )

            output = result.stdout.strip()

            csv_reader = csv.DictReader(StringIO(output))

            for row in csv_reader:
                name = row.get("Name")
                drive_type = row.get("DriveType")
                size = row.get("Size")

                if name:
                    try:
                        size = int(size) if size else 0
                    except:
                        size = 0

                    is_removable = drive_type == "2"

                    device = DeviceInfo(
                        name=name,
                        path=name,
                        size=size,
                        filesystem="Unknown",
                        is_removable=is_removable,
                        mount_point=name
                    )

                    devices.append(device)

        except Exception as e:
            print("Error detecting Windows devices:", e)

        return devices
