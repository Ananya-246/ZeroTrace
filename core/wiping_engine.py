# import os

# class WipingEngine:

#     def secure_wipe_file(self, path, passes=3):
#         try:
#             length = os.path.getsize(path)

#             with open(path, "r+b") as f:
#                 for _ in range(passes):
#                     f.seek(0)
#                     f.write(os.urandom(length))
#                     f.flush()

#                 # Final zero pass
#                 f.seek(0)
#                 f.write(b"\x00" * length)
#                 f.flush()

#             os.remove(path)

#         except Exception as e:
#             raise e

import os
from core.nist_algorithms import NISTAlgorithms


class WipingEngine:

    # ---------------------------
    # SECURE WIPE + DELETE
    # ---------------------------
    def secure_wipe_file(self, path, method: str = "purge"):
        """
        Wipes file content using NIST Clear or NIST Purge
        then deletes the file from disk.

        method: "clear" → NIST Clear (single zero pass)
        method: "purge" → NIST Purge (3-pass: zeros, random, zeros)
        """
        try:
            if method == "clear":
                print(f"    ⏳ NIST Clear — pass 1/1: zeros...")
                NISTAlgorithms.clear(str(path), verify=True)
                print(f"    ✔ NIST Clear complete.")

            else:
                print(f"    ⏳ NIST Purge — pass 1/3: zeros...")
                print(f"    ⏳ NIST Purge — pass 2/3: random...")
                print(f"    ⏳ NIST Purge — pass 3/3: zeros...")
                NISTAlgorithms.purge(str(path), verify=True)
                print(f"    ✔ NIST Purge complete.")

            # Delete file after wipe
            os.remove(path)
            print(f"    🗑 File deleted: {path}")

        except Exception as e:
            raise e