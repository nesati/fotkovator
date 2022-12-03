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

    run_forever = []
    for module in config['frontend']:
        a = load_module('frontend', module['module'])
        run_forever.append(a.init(bus, module))
    for module in config['backend']:
        run_forever.append(load_module('backend', module['module']).init(bus, module))
    for module in config['tag']:
        load_module('tag', module['module']).init(bus, module)

    loop = asyncio.new_event_loop()

    run_forever = list(map(loop.create_task, run_forever))

    loop.run_until_complete(asyncio.wait(run_forever))
