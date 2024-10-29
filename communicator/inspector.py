import collections
import logging
import time
from functools import partial

logger = logging.getLogger(__name__)


class Inspector:
    methods = ('stats', 'active_queues', 'registered', 'scheduled', 'active', 'reserved', 'revoked', 'conf')

    def __init__(self, io_loop, capp, timeout):
        self.io_loop = io_loop
        self.capp = capp
        self.timeout = timeout
        self.workers = collections.defaultdict(dict)

    def inspect(self, workername=None):
        feutures = []
        for method in self.methods:
            feutures.append(self.io_loop.run_in_executor(None, partial(self._inspect, method, workername)))
        return feutures

    def _on_update(self, workername, method, response):
        info = self.workers[workername]
        info[method] = response
        info['timestamp'] = time.time()

    def _inspect(self, method, workername):
        destination = [workername] if workername else None
        inspect = self.capp.control.inspect(timeout=self.timeout, destination=destination)
        logger.debug('Sending %s inspect command', method)
        start = time.time()
        result = (
            getattr(inspect, method)()
            if method != 'active'
            else getattr(inspect, method)(safe=True)
        )
        logger.debug("Inspect command %s took %.2fs to complete", method, time.time() - start)
        if result is None or 'error' in result:
            logger.warning("Inspect method %s failed", method)
            return
        for worker, response in result.items():
            if response is not None:
                future = self.io_loop.run_in_executor(
                    None,  # Use the default executor
                    partial(self._on_update, worker, method, response)  # Run state.event(event) in the executor
                )

                def handle_exception(fut):
                    try:
                        fut.result()  # This will raise an exception if the task failed
                    except Exception as exc:
                        logger.error(f"Error processing event: {exc}")

                # Add a callback to handle any exceptions in the future
                future.add_done_callback(handle_exception)
