import logging
import sys
from concurrent.futures import ThreadPoolExecutor

from communicator.job.start import celery
import tornado.web
from tornado import ioloop
from tornado.httpserver import HTTPServer
import tornado.platform.asyncio
from communicator.events import Events
from communicator.inspector import Inspector
from communicator.variables import variables

logger = logging.getLogger(__name__)


if sys.version_info[0] == 3 and sys.version_info[1] >= 8 and sys.platform.startswith('win'):
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


class Flower(tornado.web.Application):
    pool_executor_cls = ThreadPoolExecutor
    max_workers = None

    def __init__(self, options=None, capp=None, events=None, io_loop=None, **kwargs):
        super().__init__(**kwargs)
        tornado.platform.asyncio.AsyncIOMainLoop().install()
        self.io_loop = io_loop or tornado.ioloop.IOLoop.instance()
        self.ssl_options = kwargs.get('ssl_options', None)
        # self.capp = capp or celery.Celery(
        #     'tasks',
        #     broker=variables.celery_broker
        # )
        self.capp = celery
        self.capp.loader.import_default_modules()

        self.executor = self.pool_executor_cls(max_workers=self.max_workers)
        self.io_loop.set_default_executor(self.executor)

        self.inspector = Inspector(self.io_loop, self.capp, variables.inspect_timeout / 1000.0)

        self.events = events or Events(
            self.capp,
            db=variables.flower_db,
            persistent=variables.flower_persistent,
            state_save_interval=variables.flower_state_save_interval,
            enable_events=variables.flower_enable_events,
            io_loop=self.io_loop,
            max_workers_in_memory=variables.flower_max_workers,
            max_tasks_in_memory=variables.flower_max_tasks,
            limit_task_interval=variables.flower_state_cleaner_interval,
            limit_task_count=variables.flower_state_cleaner_max_size
        )
        self.started = False

    def start(self):
        self.events.start()

        if not variables.flower_unix_socket:
            self.listen(
                variables.flower_port,
                address=variables.flower_address,
                ssl_options=self.ssl_options,
                xheaders=False
            )
        else:
            from tornado.netutil import bind_unix_socket
            server = HTTPServer(self)
            socket = bind_unix_socket(variables.flower_unix_socket, mode=0o777)
            server.add_socket(socket)

        self.started = True
        self.update_workers()
        # self.io_loop.start()

    def stop(self):
        if self.started:
            self.events.stop()
            logging.debug("Stopping executors...")
            self.executor.shutdown(wait=False)
            logging.debug("Stopping event loop...")
            # self.io_loop.stop()
            self.started = False

    @property
    def transport(self):
        return getattr(self.capp.connection().transport, 'driver_type', None)

    @property
    def workers(self):
        return self.inspector.workers

    def update_workers(self, worker_name=None):
        return self.inspector.inspect(worker_name)
