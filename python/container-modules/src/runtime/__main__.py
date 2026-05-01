import sys
import signal
from . import App

# Initialize the application
app = App()


def shutdown_handler(exit_code=0, kc_api=None):
    """ Graceful shutdown of all connections and modules """
    for name, module in app.modules.items():
        if module and module.enabled and hasattr(module, 'shutdown'):
            module.shutdown()
    sys.exit(exit_code)

def signal_handler(sig, frame):
    print('\nAborting...')
    shutdown_handler()

def main():
    signal.signal(signal.SIGINT, signal_handler)

    # Show the application version
    if app.args.show_version:
        print(f"{app}")
        exit(0)

    # Initialize the modules
    for name, module in app.modules.items():
        if not module.enabled or not hasattr(module, 'init'):
            continue
        try:
            initialized = module.init()
            if not initialized:
                app.logger.warning(f"Module '{name}' failed to initialize and will be disabled.")
                module.enabled = False
        except Exception as e:
            app.logger.error(f"Failed to load module '{name}': {e}")
            module.enabled = False

    if app.args.show_modules:
        app.show_modules()
        exit(0)

    app.logger.info(f"Starting {app}")

    from pprint import pprint
    pprint(app.args)

    for name, module in app.modules.items():
        if not module.enabled or not hasattr(module, 'run'):
            continue
        module.run()


    app.logger.info(f"All modules completed. Shutting down.")
    shutdown_handler()
