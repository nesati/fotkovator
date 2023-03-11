import asyncio
import json
import math
from io import BytesIO

from quart import Quart, render_template, request, send_file, Response

app = Quart(__name__)

PAGE = 24


@app.route("/")
async def index():
    if 'p' in request.args:
        page = int(request.args['p'])
    else:
        page = 0

    images, n_imgs = await app.config['database'].list_images(page=page, limit=PAGE)

    # for i in range(len(images)):  # testing: random images are marked as big
    #    if random.random() <= 0.05:
    #        images[i]['big'] = True

    n_pages = math.ceil(n_imgs / PAGE)

    return await render_template("index.html", querry='', images=images, page=page, n_pages=n_pages)


@app.route("/search")
async def search():
    if 'p' in request.args:
        page = int(request.args['p'])
    else:
        page = 0

    tagnames = list(filter(bool, map(lambda s: s.strip(), request.args['tag'].split(','))))

    if len(tagnames) > 0:
        images, n_imgs = await app.config['database'].search(tagnames, page=page, limit=PAGE)
    else:
        images, n_imgs = await app.config['database'].list_images(page=page, limit=PAGE)

    n_pages = math.ceil(n_imgs / PAGE)
    return await render_template("index.html", querry=request.args['tag'], images=images, page=page, n_pages=n_pages)


@app.route("/detail/")
async def detail():
    uid = int(request.args['uid'])
    info = await app.config['database'].get_info(uid)
    tags = await app.config['database'].get_tags(uid)
    return await render_template('photo.html', info=info, tags=tags)


@app.route("/img/")
async def image():
    uri = (await app.config['database'].get_image(int(request.args['uid'])))[0]

    if 'small' in request.args:
        image = await app.config['backend'].get_thumbnail(uri)
    else:
        image = await app.config['backend'].get_image(uri)

    return await send_file(BytesIO(image), mimetype='image/jpeg')


# API calls
@app.route("/tags/")
async def tags():
    tags = await app.config['database'].list_tags()
    return Response(json.dumps(tags), mimetype='application/json')


@app.route("/rescan", methods=['POST'])
async def rescan():
    await app.config['bus'].emit('rescan', ('manual', asyncio.Event()))
    return ''

if __name__ == "__main__":
    app.run()
