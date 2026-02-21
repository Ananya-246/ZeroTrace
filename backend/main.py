from core.device_discovery import DeviceDiscovery
from core.file_scanner import FileScanner
from core.wiping_engine import WipingEngine
from utils.logging import Logger
from pathlib import Path


def navigate_and_select(start_path: Path):
    current_path = start_path

    while True:
        print(f"\nCurrent Location: {current_path}\n")

        try:
            items = list(current_path.iterdir())
        except PermissionError:
            print("Access Denied.")
            return None

        # Sort: folders first, then files
        items.sort(key=lambda x: (x.is_file(), x.name.lower()))

        for i, item in enumerate(items):
            if item.is_dir():
                print(f"{i+1}. [DIR]  {item.name}")
            else:
                print(f"{i+1}. [FILE] {item.name}")

        print("\n0. Go Back")
        print("W. Wipe This Folder")
        print("Q. Cancel")

        choice = input("\nSelect option: ").strip()

        if choice == "0":
            if current_path.parent == current_path:
                return None
            current_path = current_path.parent
            continue

        if choice.upper() == "Q":
            return None

        if choice.upper() == "W":
            return current_path

        if choice.isdigit():
            index = int(choice) - 1
            if 0 <= index < len(items):
                selected = items[index]
                if selected.is_dir():
                    current_path = selected
                else:
                    return selected
        else:
            print("Invalid selection.")


def main():

    logger = Logger()
    wiping_engine = WipingEngine()

    print("\nZeroTrace Secure Data Sanitization Tool")
    print("---------------------------------------")

    print("\nSelect Mode:")
    print("1. Wipe User Data (Navigate)")
    print("2. Wipe Entire Drive")

    mode = input("Enter choice: ").strip()

    # ---------------------------
    # USER NAVIGATION MODE
    # ---------------------------
    if mode == "1":

        start_path = Path.home()

        selected_item = navigate_and_select(start_path)

        if not selected_item:
            print("Operation cancelled.")
            return

    # ---------------------------
    # DRIVE WIPE MODE
    # ---------------------------
    elif mode == "2":

        drives = DeviceDiscovery.list_drives()

        print("\nAvailable Drives:\n")

        for i, drive in enumerate(drives):
            print(f"{i+1}. {drive}")

        choice = input("\nSelect drive number to wipe: ").strip()

        if not choice.isdigit() or int(choice) < 1 or int(choice) > len(drives):
            print("Invalid selection.")
            return

        selected_item = drives[int(choice) - 1]

    else:
        print("Invalid mode.")
        return

    # ---------------------------
    # SAFETY CHECKS
    # ---------------------------

    # Prevent wiping the tool itself
    tool_root = Path(__file__).resolve().parents[1]
    if tool_root in selected_item.resolve().parents or selected_item == tool_root:
        print("⚠ Cannot wipe ZeroTrace tool directory.")
        return

    print(f"\n⚠ WARNING: This will permanently delete:\n{selected_item}")
    confirm = input("Type YES to continue: ")

    if confirm != "YES":
        print("Operation cancelled.")
        return

    # ---------------------------
    # PERFORM WIPE
    # ---------------------------

    if selected_item.is_file():
        files = [selected_item]
    else:
        files = FileScanner.recursive_files(selected_item)

    print(f"\nFound {len(files)} files.")

    for file in files:
        try:
            wiping_engine.secure_wipe_file(file)
            logger.log_info(f"Wiped: {file}")
        except Exception as e:
            logger.log_error(f"Failed: {file} -> {e}")

    print("\n✅ Secure wipe completed.")


if __name__ == "__main__":
    main()