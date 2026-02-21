import os

def nist_clear_wipe(file_path, passes=1):
    file_size = os.path.getsize(file_path)

    with open(file_path, "r+b") as f:
        for _ in range(passes):
            f.seek(0)
            f.write(os.urandom(file_size))
            f.flush()
            os.fsync(f.fileno())

    os.remove(file_path)
    print(f"{file_path} securely wiped using NIST Clear method.")

if __name__ == "__main__":
    file_path = "F:/demo.bin"
    nist_clear_wipe(file_path, passes=1)
