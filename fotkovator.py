import asyncio
import signal

import yaml

from utils.eventbus import EventBus


def load_module(category, name):
    return __import__(f'modules.{category}.{name}', fromlist='init')


async def shutdown(bus, signal, tasks):
    print('shutting down...')
    await bus.emit('stop', signal)
    for task in tasks:
        task.cancel()


if __name__ == '__main__':
    with open('fotkovator.yaml', 'r') as file:
        config = yaml.safe_load(file)

    print(config)

    bus = EventBus()
    loop = asyncio.new_event_loop()

    database = load_module('database', config['database']['module']).Database(bus, loop, config['database'])

    backend = load_module('backend', config['backend']['module']).Backend(bus, database, loop, config['backend'])

    modules = []
    for module in config['modules']:
        modules.append(load_module('modules', module['module']).Module(bus, database, backend, loop, module).run_forever())

    tasks = [database.run_forever(), backend.run_forever()]
    tasks = tuple(map(loop.create_task, filter(lambda corutine: corutine is not None, modules + tasks)))

    signals = (signal.SIGTERM, signal.SIGINT)
    for s in signals:
        loop.add_signal_handler(s, lambda s=s: loop.create_task(shutdown(bus, s, tasks)))

    try:
        loop.run_until_complete(asyncio.gather(*tasks))
    except asyncio.CancelledError:
        print('stopped')
    else:
        raise RuntimeError('The backend stopped unexpectedly')
