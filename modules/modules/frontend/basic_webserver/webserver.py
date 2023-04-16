import asyncio
import json
import math
from io import BytesIO

from quart import Quart, render_template, request, send_file, Response, redirect

from modules.modules.frontend.basic_webserver.metadata import clean_metadata

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

    images, n_imgs = await app.config['search'].search(tagnames, page=page, limit=PAGE)

    n_pages = math.ceil(n_imgs / PAGE)
    return await render_template("index.html", querry=request.args['tag'], images=images, page=page, n_pages=n_pages)


@app.route("/detail/")
async def detail():
    uid = int(request.args['uid'])
    info = await app.config['database'].get_info(uid)
    if info is None:
        return await not_found()
    tags = await app.config['database'].get_tags(uid)

    info['metadata'] = clean_metadata(info['metadata'])

    return await render_template('photo.html', info=info, tags=tags)


@app.route("/img/")
async def image():
    uri = (await app.config['database'].get_image(int(request.args['uid'])))['uri']

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


@app.route("/edit", methods=['POST'])
async def edit():
    uid = int((await request.form)['uid'])
    tagname = (await request.form)['tagname']
    action = (await request.form)['action']

    if action == 'delete':
        await app.config['bus'].emit('remove_tag', (uid, tagname))
    elif action == 'rename':
        new_name = (await request.form)['new-tagname'].strip()
        if new_name:
            try:
                await app.config['bus'].emit('rename_tag', (tagname, new_name))
            except AssertionError:
                return await render_template('error.html', code=400, message='Špatný požadavek',
                                             body="Nelze přejmenovat štítek na již existující název štítku."), 400
    elif action == 'add':
        new_name = (await request.form)['add-tagname'].strip()
        if new_name:
            await app.config['bus'].emit('tag', (uid, new_name, {}))

    return redirect(f"/detail/?uid={uid}")


@app.route("/rescan", methods=['POST'])
async def rescan():
    if not app.config['database'].scan_in_progress:
        await app.config['bus'].emit('rescan', ('manual', asyncio.Event()))
        return 'Scan done'
    else:
        return 'Scan in progress already', 503


# error handlers
@app.errorhandler(404)
async def not_found(*_):
    return await render_template('error.html', code=404, message='Nenalezeno'), 404


@app.errorhandler(500)
async def internal_error(*_):
    return await render_template('error.html', code=500, message='Interní chyba'), 500


if __name__ == "__main__":
    app.run()
