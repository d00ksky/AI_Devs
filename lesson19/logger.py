import logging


logger = logging.getLogger("myapp")
logger.setLevel(logging.DEBUG)
# Add a simple stream handler
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)