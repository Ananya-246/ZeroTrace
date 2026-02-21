from core.device_info import DeviceInfo

device = DeviceInfo(
    name="USB Drive",
    path="/dev/sdb1",
    size=32000000000,
    filesystem="FAT32",
    is_removable=True,
    mount_point="/media/usb"
)

print(device)
print(device.to_dict())
