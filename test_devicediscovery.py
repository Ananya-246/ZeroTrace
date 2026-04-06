from core.device_discovery import DeviceDiscovery

devices = DeviceDiscovery.list_devices()

for device in devices:
    print(device)
