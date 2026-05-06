import sys
import signal
from time import (sleep, perf_counter)
from runtime import App
from runtime.async_runner import run_modules_async

# Initialize the application
app = App()

def shutdown_handler(exit_code=0):
    """ Graceful shutdown of all connections and resources. """
    sys.exit(exit_code)

def signal_handler(sig, frame):
    print('\nAborting...')
    shutdown_handler()

def init_modules(app: App) -> None:
    """ Initialize the modules """
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

def run_modules(app: App) -> dict:
    """ Run the modules """
    if app.num_enabled_modules == 0:
        app.logger.warning("No modules enabled. Nothing to do.")
        shutdown_handler(exit_code=0)

    results = {}
    # Mark the start time for elapsed time counter
    run_start = perf_counter()
    app.logger.debug(f"Running {app.num_enabled_modules} active module(s)")
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

    # Generate the elapsed time
    elapsed = perf_counter() - run_start
    app.logger.info(f"All modules completed in {elapsed:.3f}s.")
    return results

def process_results(results: dict) -> None:
    ## Show the module results
    for name, output in results.items():
        app.logger.info(f"Result: '{name}' -> {output}")

def main():
    signal.signal(signal.SIGINT, signal_handler)
    # from pprint import pprint
    # pprint(app.args)
    # sys.exit(0)

    # Show the application version and exit
    if app.args.show_version:
        print(f"{app}")
        sys.exit(0)
    # Show the modules and exit
    if app.args.show_modules:
        app.show_modules()
        sys.exit(0)
    # Show a module and exit
    if app.args.show_module_info:
        app.show_module_info(app.args.show_module_info)
        sys.exit(0)

    init_modules(app=app)

    app.logger.info(f"Starting {app}")
    if app.args.async_enabled:
        app.logger.info(f"Running modules asynchronously with {app.args.async_workers} workers and {app.args.async_worker_timeout}s timeout")

    # Log the argument values and types for debugging
    # TODO: Remove this when implementing this template
    for arg, value in app.args.__dict__.items():
        app.logger.info(f"Argument: '{arg}' -> '{value}' ({type(value)})")

    if app.args.one_shot:
        results = run_modules(app=app)
        process_results(results=results)
    else:
        while True:
            results = run_modules(app=app)
            process_results(results=results)
            app.logger.debug(f"Sleeping. Running again in {app.args.run_interval} minute(s).")
            sleep(app.args.run_interval * 60)

    shutdown_handler()

if __name__ == '__main__':
    main()