import logging
import os
from datetime import datetime

# 1. Create logs directory if it doesn't exist
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# 2. Create a unique filename based on the startup time
log_filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".log"
log_path = os.path.join(LOG_DIR, log_filename)

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        handlers=[
            logging.FileHandler(log_path),  # Write to file
            
        ]
    )



# import logging
# import os
# from datetime import datetime

# # 1. Create logs directory if it doesn't exist
# LOG_DIR = "logs"
# if not os.path.exists(LOG_DIR):
#     os.makedirs(LOG_DIR)

# # 2. Create a unique filename based on the startup time
# log_filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".log"
# log_path = os.path.join(LOG_DIR, log_filename)

# def setup_logging():
#     LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-35s | %(message)s"
    
#     logging.basicConfig(
#         level=logging.INFO,
#         format=LOG_FORMAT,
#         datefmt="%Y-%m-%d %H:%M:%S",
#         handlers=[
#             logging.FileHandler(log_path),  # Write to file
#         ]
#     )

#     # 3. SILENCE THE NOISE
#     logging.getLogger("httpx").setLevel(logging.WARNING)
#     logging.getLogger("httpcore").setLevel(logging.WARNING)
#     logging.getLogger("yfinance").setLevel(logging.ERROR)
#     logging.getLogger("urllib3").setLevel(logging.WARNING)

#     logging.info(f"Logging initialized. Writing to: {log_path}")