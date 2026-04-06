from pathlib import Path

class FileScanner:

    @staticmethod
    def recursive_files(path: Path):
        return [f for f in path.rglob("*") if f.is_file()]

    @staticmethod
    def count_files(path: Path):
        return len(FileScanner.recursive_files(path))

    @staticmethod
    def calculate_size(path: Path):
        total = 0
        for f in FileScanner.recursive_files(path):
            try:
                total += f.stat().st_size
            except:
                pass
        return total