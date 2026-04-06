# from core.device_discovery import DeviceDiscovery
# from core.file_scanner import FileScanner
# from core.wiping_engine import WipingEngine
# from utils.logging import Logger
# from pathlib import Path


# def navigate_and_select(start_path: Path):
#     current_path = start_path

#     while True:
#         print(f"\nCurrent Location: {current_path}\n")

#         try:
#             items = list(current_path.iterdir())
#         except PermissionError:
#             print("Access Denied.")
#             return None

#         # Sort: folders first, then files
#         items.sort(key=lambda x: (x.is_file(), x.name.lower()))

#         for i, item in enumerate(items):
#             if item.is_dir():
#                 print(f"{i+1}. [DIR]  {item.name}")
#             else:
#                 print(f"{i+1}. [FILE] {item.name}")

#         print("\n0. Go Back")
#         print("W. Wipe This Folder")
#         print("Q. Cancel")

#         choice = input("\nSelect option: ").strip()

#         if choice == "0":
#             if current_path.parent == current_path:
#                 return None
#             current_path = current_path.parent
#             continue

#         if choice.upper() == "Q":
#             return None

#         if choice.upper() == "W":
#             return current_path

#         if choice.isdigit():
#             index = int(choice) - 1
#             if 0 <= index < len(items):
#                 selected = items[index]
#                 if selected.is_dir():
#                     current_path = selected
#                 else:
#                     return selected
#         else:
#             print("Invalid selection.")


# def main():

#     logger = Logger()
#     wiping_engine = WipingEngine()

#     print("\nZeroTrace Secure Data Sanitization Tool")
#     print("---------------------------------------")

#     print("\nSelect Mode:")
#     print("1. Wipe User Data (Navigate)")
#     print("2. Wipe Entire Drive")

#     mode = input("Enter choice: ").strip()

#     # ---------------------------
#     # USER NAVIGATION MODE
#     # ---------------------------
#     if mode == "1":

#         start_path = Path.home()

#         selected_item = navigate_and_select(start_path)

#         if not selected_item:
#             print("Operation cancelled.")
#             return

#     # ---------------------------
#     # DRIVE WIPE MODE
#     # ---------------------------
#     elif mode == "2":

#         drives = DeviceDiscovery.list_drives()

#         print("\nAvailable Drives:\n")

#         for i, drive in enumerate(drives):
#             print(f"{i+1}. {drive}")

#         choice = input("\nSelect drive number to wipe: ").strip()

#         if not choice.isdigit() or int(choice) < 1 or int(choice) > len(drives):
#             print("Invalid selection.")
#             return

#         selected_item = drives[int(choice) - 1]

#     else:
#         print("Invalid mode.")
#         return

#     # ---------------------------
#     # SAFETY CHECKS
#     # ---------------------------

#     # Prevent wiping the tool itself
#     tool_root = Path(__file__).resolve().parents[1]
#     if tool_root in selected_item.resolve().parents or selected_item == tool_root:
#         print("⚠ Cannot wipe ZeroTrace tool directory.")
#         return

#     print(f"\n⚠ WARNING: This will permanently delete:\n{selected_item}")
#     confirm = input("Type YES to continue: ")

#     if confirm != "YES":
#         print("Operation cancelled.")
#         return

#     # ---------------------------
#     # PERFORM WIPE
#     # ---------------------------

#     if selected_item.is_file():
#         files = [selected_item]
#     else:
#         files = FileScanner.recursive_files(selected_item)

#     print(f"\nFound {len(files)} files.")

#     for file in files:
#         try:
#             wiping_engine.secure_wipe_file(file)
#             logger.log_info(f"Wiped: {file}")
#         except Exception as e:
#             logger.log_error(f"Failed: {file} -> {e}")

#     print("\n✅ Secure wipe completed.")


# if __name__ == "__main__":
#     main()


from core.device_discovery import DeviceDiscovery
from core.file_scanner import FileScanner
from core.wiping_engine import WipingEngine
from utils.logging import Logger
from pathlib import Path
from core.nist_algorithms import NISTAlgorithms
import os


# ---------------------------
# NAVIGATOR
# ---------------------------
def navigate_and_select(start_path: Path):
    current_path = start_path

    while True:
        print(f"\nCurrent Location: {current_path}\n")

        try:
            items = list(current_path.iterdir())
        except PermissionError:
            print("Access Denied.")
            return None

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


# ---------------------------
# MAIN
# ---------------------------
def main():

    logger = Logger()
    wiping_engine = WipingEngine()

    print("\nZeroTrace Secure Data Sanitization Tool")
    print("---------------------------------------")

    print("\nSelect Mode:")
    print("1. Wipe User Data (Navigate & Delete)")
    print("2. Wipe Entire Drive")
    print("3. Overwrite Only (Keep File, Wipe Content)")

    mode = input("Enter choice: ").strip()

    # ---------------------------
    # OVERWRITE ONLY MODE
    # ---------------------------
    if mode == "3":

        print("\n📄 Overwrite Only Mode — file will NOT be deleted.")
        start_path = Path.home()
        selected_item = navigate_and_select(start_path)

        if not selected_item:
            print("Operation cancelled.")
            return

        if not selected_item.is_file():
            print("⚠ Please select a single file, not a folder.")
            return

        print(f"\nYou selected : {selected_item}")
        print(f"Size         : {os.path.getsize(selected_item)} bytes")

        # Choose NIST algorithm
        print("\nSelect Overwrite Method:")
        print("1. NIST Clear  — single zero pass (fast)")
        print("2. NIST Purge  — 3 passes: zeros, random, zeros (thorough)")
        method = input("Enter choice: ").strip()

        if method not in ("1", "2"):
            print("Invalid method. Operation cancelled.")
            return

        print(f"\n⚠ WARNING: Content of this file will be overwritten.")
        print(f"The file itself will remain on disk.")
        confirm = input("Type YES to continue: ").strip()

        if confirm != "YES":
            print("Operation cancelled.")
            return

        # Show BEFORE hex dump
        # hex_dump(str(selected_item), f"BEFORE OVERWRITE: {selected_item.name}")

        # Run selected NIST algorithm
        try:
            if method == "1":
                print("  ⏳ Running NIST Clear — single zero pass...")
                NISTAlgorithms.clear(str(selected_item), verify=True)
                print("  ✔ NIST Clear complete.")

            elif method == "2":
                print("  ⏳ Running NIST Purge — pass 1/3: zeros...")
                NISTAlgorithms._write_and_sync(
                    open(str(selected_item), "r+b", buffering=0),
                    b"\x00" * os.path.getsize(selected_item),
                    os.path.getsize(selected_item)
                )
                print("  ⏳ Running NIST Purge — pass 2/3: random...")
                print("  ⏳ Running NIST Purge — pass 3/3: zeros...")
                NISTAlgorithms.purge(str(selected_item), verify=True)
                print("  ✔ NIST Purge complete.")

            # Show AFTER hex dump
            # hex_dump(str(selected_item), f"AFTER OVERWRITE: {selected_item.name}")

            print(f"  ✅ VERIFIED: {selected_item.name} — all bytes are zero.")
            print(f"  📄 File still exists at: {selected_item}")
            logger.log_info(f"Overwrite only [{('NIST Clear' if method == '1' else 'NIST Purge')}]: {selected_item}")

        except IOError as e:
            print(f"  ❌ Verification failed: {e}")
            logger.log_error(f"Overwrite failed: {selected_item} -> {e}")

        return

    # ---------------------------
    # USER NAVIGATION MODE
    # ---------------------------
    if mode == "1":

        start_path = Path.home()
        selected_item = navigate_and_select(start_path)

        if not selected_item:
            print("Operation cancelled.")
            return

        print(f"\nYou selected : {selected_item}")
        if selected_item.is_file():
            print(f"Type         : Single File")
            print(f"Size         : {os.path.getsize(selected_item)} bytes")
        else:
            files_preview = FileScanner.recursive_files(selected_item)
            print(f"Type         : Folder")
            print(f"Contains     : {len(files_preview)} files")

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
    # PERFORM WIPE + DELETE
    # ---------------------------
    if selected_item.is_file():
        files = [selected_item]
    else:
        files = FileScanner.recursive_files(selected_item)

    print(f"\nFound {len(files)} file(s) to wipe:")
    for f in files:
        print(f"  - {f}")

        # ✅ ADD THIS — ask Clear or Purge before wiping
    print("\nSelect Wipe Method:")
    print("1. NIST Clear  — single zero pass (fast)")
    print("2. NIST Purge  — 3 passes: zeros, random, zeros (thorough)")
    wipe_method = input("Enter choice: ").strip()

    if wipe_method not in ("1", "2"):
        print("Invalid method. Operation cancelled.")
        return

    wipe_method = "clear" if wipe_method == "1" else "purge"

    confirm2 = input("\nProceed? Type YES to confirm: ")
    if confirm2 != "YES":
        print("Operation cancelled.")
        return

    passed = 0
    failed = 0
    
    for file in files:
        try:
            # hex_dump(str(file), f"BEFORE WIPE: {file.name}")
            wiping_engine.secure_wipe_file(file, method=wipe_method)
            # hex_dump(str(file), f"AFTER WIPE: {file.name}")
            passed += 1
            logger.log_info(f"Wiped: {file}")

        except Exception as e:
            print(f"  ✗ Error wiping {file}: {e}")
            logger.log_error(f"Failed: {file} -> {e}")
            failed += 1

    print(f"\n{'='*40}")
    print(f"  Wipe Summary")
    print(f"{'='*40}")
    print(f"  Total files : {len(files)}")
    print(f"  ✅ Passed   : {passed}")
    print(f"  ❌ Failed   : {failed}")
    print(f"{'='*40}")
    print("\n✅ Secure wipe completed.")


if __name__ == "__main__":
    main()
