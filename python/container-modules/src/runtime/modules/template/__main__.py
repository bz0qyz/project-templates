import logging
from . import module

def main(app):
    module.set_logger(app.logger)
    module.logger.info(f"Running Module: '{module.name}'")

if __name__ == "__main__":
    main()