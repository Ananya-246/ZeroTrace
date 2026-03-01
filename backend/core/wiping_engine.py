import os

class WipingEngine:

    def secure_wipe_file(self, path, passes=3):
        try:
            length = os.path.getsize(path)

            with open(path, "r+b") as f:
                for _ in range(passes):
                    f.seek(0)
                    f.write(os.urandom(length))
                    f.flush()

                # Final zero pass
                f.seek(0)
                f.write(b"\x00" * length)
                f.flush()
                os.fsync(f.fileno())

            os.remove(path)

        except Exception as e:
            raise e