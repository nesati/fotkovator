import asyncio

import yaml
from utils.eventbus import EventBus


def load_module(category, name):
    return __import__(f'modules.{category}.{name}', fromlist='init')


if __name__ == '__main__':
    with open('fotkovator.yaml', 'r') as file:
        config = yaml.safe_load(file)

    print(config)

    bus = EventBus()

    database = load_module('database', config['database']['module']).Database(bus, config['database'])

    backend = load_module('backend', config['backend']['module']).Backend(bus, database, config['backend'])

    modules = []
    for module in config['modules']:
        modules.append(load_module('modules', module['module']).Module(bus, database, backend, module).run_forever())
    loop = asyncio.new_event_loop()

    modules += [database.run_forever(), backend.run_forever()]
    modules = list(map(loop.create_task, filter(lambda corutine: corutine is not None, modules)))

    loop.run_until_complete(asyncio.wait(modules))
