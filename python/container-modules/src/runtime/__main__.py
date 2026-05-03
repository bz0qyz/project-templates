import sys
import signal
from time import perf_counter
from . import App
from .async_runner import run_modules_async

# Initialize the application
app = App()


def shutdown_handler(exit_code=0, kc_api=None):
    """ Graceful shutdown of all connections and resources. """
    sys.exit(exit_code)

def signal_handler(sig, frame):
    print('\nAborting...')
    shutdown_handler()

def main():
    signal.signal(signal.SIGINT, signal_handler)
    run_start = perf_counter()

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
    if app.args.async_enabled:
        app.logger.info(f"Running modules asynchronously with {app.args.async_workers} workers and {app.args.async_worker_timeout}s timeout")

    # Log the argument values and types for debugging
    # Remove this when implementing this template
    for arg, value in app.args.__dict__.items():
        app.logger.info(f"Argument: '{arg}' -> '{value}' ({type(value)})")

    # Run the modules
    results = {}
    if app.args.async_enabled:
        # Run the modules asynchronously
        results = run_modules_async(
            loaded_mains=app.modules,
            max_workers=app.args.async_workers,
            timeout=float(app.args.async_worker_timeout)
        )
    else:
        # Run the nodules synchronously
        for name, module in app.modules.items():
            if not module.enabled or not hasattr(module, 'run'):
                continue
            try:
                results[module.name] = module.run()
            except Exception as e:
                app.logger.error(f"Execution from module '{name}': {e}")

    elapsed = perf_counter() - run_start
    ## Show the module results
    for name, output in results.items():
        app.logger.info(f"Result: '{name}' -> {output}")
    app.logger.info(f"All modules completed in {elapsed:.3f}s. Shutting down.")
    shutdown_handler()
