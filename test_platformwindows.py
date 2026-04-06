from platforms.platform_windows import WindowsPlatform

devices = WindowsPlatform.list_devices()

for device in devices:
    print(device)
