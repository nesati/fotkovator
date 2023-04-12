import asyncio

import clip
import numpy as np
import torch

from utils.interface import SearchModule, KNNCapability


class CLIPSearch(SearchModule):
    def __init__(self, bus, database, backend, loop, config):
        super().__init__(bus, database, backend, loop)

        # load clip model
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model, self.preprocess = clip.load(config.get('model', "ViT-B/32"), device=self.device)
        self.logit_scale = self.model.logit_scale.exp()

        assert isinstance(self.database, KNNCapability), 'CLIP search requires kNN capable database'

        self.db_ready = asyncio.Event()

        self.bus.add_listener('new_image', lambda img: self.add_image(*img))

    async def add_image(self, uid, db_ready, img, uri, dt, metadata):
        await self.db_ready.wait()

        # run clip
        image = self.preprocess(img).unsqueeze(0).to(self.device)
        embedding = await self.loop.run_in_executor(None, self._CLIP_embed_image, image)
        embedding = embedding[0].cpu().numpy()

        await self.database.knn_add(self, 'embedings', {'embed': embedding, 'uid': uid})

    def _CLIP_embed_image(self, image):
        with torch.no_grad():
            return self.model.encode_image(image)

    def _CLIP_embed_text(self, text):
        embedding = clip.tokenize(text).to(self.device)
        with torch.no_grad():
            return self.model.encode_text(embedding)

    async def search(self, query, **kwargs):
        await self.db_ready.wait()

        # preprocess query
        if isinstance(query, list):
            query = ' '.join(query)

        if 'page' in kwargs:
            kwargs = {
                'limit': kwargs['limit'],
                'offset': kwargs['page'] * kwargs['limit']
            }

        embedding = await self.loop.run_in_executor(None, self._CLIP_embed_text, query)
        embedding = embedding[0].cpu().numpy()

        out = await self.database.knn_query(self, 'embedings', 'embed', embedding, distance='cosine', **kwargs)

        return list(map(dict, out)), 100000

    async def run_forever(self):
        await self.database.ensure_knn_index(self, 'embedings', (
            {'name': 'embed', 'type': 'vector', 'optimize': 'cosine', 'not null': True, 'n_dim': 512},
            {'name': 'uid', 'type': 'int', 'unique': True, 'not null': True}
        ))
        self.db_ready.set()
