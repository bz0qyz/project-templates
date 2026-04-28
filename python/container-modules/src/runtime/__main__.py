import sys
import signal
from . import App
from time import sleep

# Initialize the application
app = App()


def signal_handler(sig, frame):
    print('\nAborting...')
    for name, module in app.modules.items():
        if "module" in module and hasattr(module["module"], 'shutdown'):
            module["module"].shutdown()
    sys.exit(0)

def main():
    signal.signal(signal.SIGINT, signal_handler)

    from pprint import pprint
    pprint(app.args)

    if app.args.version:
        print(f"{app.name} version {app.version}")
        sys.exit(0)

    app.logger.info(f"Starting {app.name} version {app.version}")

    for name, module in app.modules.items():
        if "main" in module:
            disabled = getattr(app.args, f"disable_module_{name}", False)
            if disabled:
                app.logger.info(f"Skipping disabled module: \"{name}\"")
                continue
            module["main"].main(app=app)
        sleep(5)

    app.logger.info(f"All modules completed. Exiting.")
    sys.exit(0)
