import asyncio

import modules.modules.frontend.basic_webserver.webserver
from utils.interface import Frontend


class Module(Frontend):
    def __init__(self, bus, database, backend, loop, config):
        super().__init__(bus, database, backend, loop)
        self.shutdown = asyncio.Event()
        self.port = config.get('port', 5000)
        self.host = config.get('host', '127.0.0.1')

        self.bus.add_listener('stop', self.stop)

    def run_forever(self):
        webserver.app.config['bus'] = self.bus
        webserver.app.config['database'] = self.database
        webserver.app.config['backend'] = self.backend
        return webserver.app.run_task(port=self.port, host=self.host, shutdown_trigger=self.shutdown.wait)

    async def stop(self, signal):
        self.shutdown.set()
