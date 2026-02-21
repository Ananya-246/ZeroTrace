"""
DeviceInfo model
Represents a storage device in the system.
"""


class DeviceInfo:
    """
    A class to store information about a storage device.
    """

    def __init__(
        self,
        name: str,
        path: str,
        size: int,
        filesystem: str = "Unknown",
        is_removable: bool = False,
        mount_point: str = None
    ):
        self.name = name
        self.path = path
        self.size = size  # in bytes
        self.filesystem = filesystem
        self.is_removable = is_removable
        self.mount_point = mount_point

    def __str__(self):
        """
        Human-readable representation.
        """
        return (
            f"Device Name: {self.name}\n"
            f"Path: {self.path}\n"
            f"Size: {self.size} bytes\n"
            f"Filesystem: {self.filesystem}\n"
            f"Removable: {self.is_removable}\n"
            f"Mount Point: {self.mount_point}\n"
        )

    def to_dict(self):
        """
        Convert device information to dictionary.
        Useful for JSON export or certificates.
        """
        return {
            "name": self.name,
            "path": self.path,
            "size": self.size,
            "filesystem": self.filesystem,
            "is_removable": self.is_removable,
            "mount_point": self.mount_point,
        }
