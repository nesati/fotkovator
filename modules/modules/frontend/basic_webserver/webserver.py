import json
from io import BytesIO

from PIL import ImageOps
from quart import Quart, render_template, request, send_file, Response

app = Quart(__name__)


@app.route("/")
async def index():
    if 'p' in request.args:
        page = int(request.args['p'])
    else:
        page = 0

    images = await app.config['database'].list_images(page=page, limit=24)

    # for i in range(len(images)):  # testing: random images are marked as big
    #    if random.random() <= 0.05:
    #        images[i]['big'] = True

    last = len(images) < 24

    return await render_template("index.html", images=images, page=page, last=last)


@app.route("/detail/")
async def detail():
    uid = request.args['uid']
    metadata = await app.config['database'].get_metadata(uid)
    tags = await app.config['database'].get_tags(uid)
    return await render_template('photo.html', uid=uid, metadata=metadata, tags=tags)


@app.route("/img/")
async def image():
    image = (await app.config['backend'].get_image(request.args['uid']))[0]
    if 'small' in request.args:
        image = ImageOps.contain(image, (256, 256))
    img_io = BytesIO()
    image.save(img_io, 'JPEG', quality=70)
    img_io.seek(0)
    return await send_file(img_io, mimetype='image/jpeg')


@app.route("/tags/")
async def tags():
    tags = await app.config['database'].list_tags()
    return Response(json.dumps(tags), mimetype='application/json')


if __name__ == "__main__":
    app.run()