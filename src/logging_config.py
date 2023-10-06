import logging

logging.basicConfig(
    handlers=[logging.FileHandler("filename.log"), logging.StreamHandler()],
    format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
    level=logging.INFO,
)
