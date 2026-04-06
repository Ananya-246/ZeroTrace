from utils import (
    setup_logger,
    validate_device_path,
    validate_algorithm,
    format_size,
    current_timestamp,
)

# Test logger
logger = setup_logger()
logger.info("Logger is working!")

# Test size formatter
print(format_size(1024))
print(format_size(1048576))

# Test timestamp
print(current_timestamp())

# Test validation
try:
    validate_algorithm("zero")
    print("Algorithm validation passed")

    validate_device_path("non_existing_path")
except Exception as e:
    print("Validation error caught:", e)
