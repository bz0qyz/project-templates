import logging
from time import perf_counter
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed

def run_module(name: str, mod_main, *args, **kwargs) -> tuple:
    """Call main() on a loaded module and return (name, result)."""
    start = perf_counter()
    result = mod_main.main(*args, **kwargs)
    elapsed = perf_counter() - start
    return name, result, elapsed

def run_modules_async(
    loaded_mains: dict,
    *args,
    timeout: float = 60.0,
    max_workers: int = 4,
    **kwargs
) -> dict:
    results = {}
    logger = logging.getLogger("async_runner")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(run_module, name, mod_main, *args, **kwargs): name
            for name, mod_main in loaded_mains.items()
            if getattr(mod_main, "enabled", True)
        }
        try:
            for future in as_completed(futures, timeout=timeout):
                name = futures[future]          # always resolved from the futures dict
                try:
                    _, result, elapsed = future.result() # discard the returned name, use dict lookup
                    results[name] = result
                    logger.debug(f"Module: '{name}' completed in {elapsed:.3f}s")
                except TimeoutError:
                    logger.error(f"Module: '{name}' timed out after {timeout}s")
                except Exception as e:
                    logger.error(f"Execution from module '{name}': {e}")
        except TimeoutError:
            logger.error(f"Workers timed out after {timeout}s. Try setting a higher worker timeout with --async-workers")

    return results