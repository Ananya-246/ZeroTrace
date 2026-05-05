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


import os
from pathlib import Path

from core.device_discovery import DeviceDiscovery
from utils.logging import Logger
from wipe_flow import (
    count_wipe_files,
    run_destructive_wipe,
    run_overwrite_only,
    safety_check_blocks_wipe,
)


# ---------------------------
# ROOT SELECTION (C:, /, /Volumes, etc.)
# ---------------------------
def select_root():
    roots = DeviceDiscovery.list_drives()

    if not roots:
        print("❌ No drives / locations found.")
        return None

    print("\nAvailable Locations:\n")
    for i, r in enumerate(roots):
        print(f"{i+1}. {r}")

    choice = input("\nSelect location: ").strip()

    if not choice.isdigit():
        return None

    idx = int(choice) - 1
    if idx < 0 or idx >= len(roots):
        return None

    return Path(roots[idx])


# ---------------------------
# NAVIGATION
# ---------------------------
def navigate_and_select(start_path: Path):
    current_path = start_path

    while True:
        print(f"\nDrive/Root: {current_path.anchor or current_path}")
        print(f"Current Location: {current_path}\n")

        try:
            items = list(current_path.iterdir())
        except PermissionError:
            print("⚠ Access Denied.")
            return None

        items.sort(key=lambda x: (x.is_file(), x.name.lower()))

        for i, item in enumerate(items):
            if item.is_dir():
                print(f"{i+1}. [DIR]  {item.name}")
            else:
                print(f"{i+1}. [FILE] {item.name}")

        print("\n0. Go Back")
        print("W. Wipe This Folder")
        print("S. Switch Drive/Root")
        print("Q. Cancel")

        choice = input("\nSelect option: ").strip()

        if choice == "0":
            if current_path.parent == current_path:
                return None
            current_path = current_path.parent
            continue

        if choice.upper() == "Q":
            return None

        if choice.upper() == "S":
            new_root = select_root()
            if new_root:
                current_path = new_root
            continue

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

    print("\nZeroTrace Secure Data Sanitization Tool")
    print("---------------------------------------")

    print("\nSelect Mode:")
    print("1. Wipe User Data (Navigate & Delete)")
    print("2. Wipe Entire Drive")
    print("3. Overwrite Only (Keep File, Wipe Content)")

    mode = input("Enter choice: ").strip()

    # ---------------------------
    # MODE 3: OVERWRITE ONLY
    # ---------------------------
    if mode == "3":
        print("\n📄 Overwrite Only Mode")

        start_path = select_root()
        if not start_path:
            print("Cancelled.")
            return

        selected_item = navigate_and_select(start_path)

        if not selected_item:
            print("Cancelled.")
            return

        if not selected_item.is_file():
            print("⚠ Please select a file.")
            return

        print(f"\nSelected: {selected_item}")
        print(f"Size    : {os.path.getsize(selected_item)} bytes")

        print("\nSelect Overwrite Method:")
        print("1. NIST Clear")
        print("2. NIST Purge")

        method = input("Enter choice: ").strip()
        if method not in ("1", "2"):
            print("Invalid choice.")
            return

        confirm = input("\nType YES to continue: ")
        if confirm != "YES":
            print("Cancelled.")
            return

        try:
            run_overwrite_only(selected_item, method, logger)
            print("✅ Overwrite complete.")
        except Exception as e:
            print(f"❌ Error: {e}")
            logger.log_error(str(e))

        return

    # ---------------------------
    # MODE 1: NAVIGATION WIPE
    # ---------------------------
    elif mode == "1":
        start_path = select_root()
        if not start_path:
            print("Cancelled.")
            return

        selected_item = navigate_and_select(start_path)

        if not selected_item:
            print("Cancelled.")
            return

    # ---------------------------
    # MODE 2: FULL DRIVE WIPE
    # ---------------------------
    elif mode == "2":
        selected_item = select_root()

        if not selected_item:
            print("Cancelled.")
            return

    else:
        print("Invalid mode.")
        return

    # ---------------------------
    # SAFETY CHECKS
    # ---------------------------
    block = safety_check_blocks_wipe(selected_item)
    if block:
        print(f"⚠ {block}")
        return

    # ---------------------------
    # CONFIRM
    # ---------------------------
    print(f"\n⚠ WARNING: This will permanently delete:\n{selected_item}")
    confirm = input("Type YES to continue: ")

    if confirm != "YES":
        print("Cancelled.")
        return

    # ---------------------------
    # FILE COUNT (same as CLI: after first YES, before method choice)
    # ---------------------------
    file_count = count_wipe_files(selected_item)
    print(f"\nFound {file_count} file(s)")

    # ---------------------------
    # WIPE METHOD
    # ---------------------------
    print("\nSelect Wipe Method:")
    print("1. NIST Clear")
    print("2. NIST Purge")

    wipe_method = input("Enter choice: ").strip()
    if wipe_method not in ("1", "2"):
        print("Invalid method.")
        return

    wipe_method = "clear" if wipe_method == "1" else "purge"

    confirm2 = input("\nProceed? Type YES to confirm: ")
    if confirm2 != "YES":
        print("Cancelled.")
        return

    # ---------------------------
    # WIPE PROCESS + CERTIFICATE (shared with API via ``wipe_flow``)
    # ---------------------------
    result = run_destructive_wipe(selected_item, wipe_method, logger)

    # ---------------------------
    # SUMMARY
    # ---------------------------
    print("\n========== SUMMARY ==========")
    print(f"Total   : {result.total}")
    print(f"Passed  : {result.passed}")
    print(f"Failed  : {result.failed}")
    print("✅ Secure wipe completed.")

    if result.certificate:
        print(
            "\n📜 Tamper-proof certificate generated:\n"
            f"   {result.certificate['certificate_json']}\n"
            f"   {result.certificate['signature_sig']}\n"
            f"   {result.certificate['certificate_pdf']}"
        )
    if result.certificate_error:
        print(f"\n⚠ Certificate generation failed: {result.certificate_error}")
        logger.log_error(f"Certificate generation: {result.certificate_error}")


if __name__ == "__main__":
    main()