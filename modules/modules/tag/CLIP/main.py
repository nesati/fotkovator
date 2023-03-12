import asyncio
from collections import OrderedDict

import clip
import torch

from utils.interface import TagModule


class CLIPTagger(TagModule):
    """
    Uses openAI's CLIP to add tags for any configured visual concept.
    """

    def __init__(self, bus, database, backend, loop, config):
        super().__init__(bus, database, backend, loop)

        # load clip model
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model, self.preprocess = clip.load(config.get('model', "ViT-B/32"), device=self.device)
        self.logit_scale = self.model.logit_scale.exp()

        # pre-encode text
        self.classifiers = []
        for classifier in config['classifiers']:
            prefix = config.get('prefix', '')
            classifier['concepts'] = OrderedDict(classifier['concepts'])  # order the keys and values for splitting
            classifier['labels'] = list(classifier['concepts'].values())
            classifier['concepts'] = list(map(lambda s: prefix + s, classifier['concepts'].keys()))
            classifier['encodings'] = clip.tokenize(classifier['concepts']).to(self.device)
            with torch.no_grad():
                classifier['encodings'] = self.model.encode_text(classifier['encodings'])
                classifier['encodings'] /= classifier['encodings'].norm(dim=1, keepdim=True)
            del classifier['concepts']
            self.classifiers.append(classifier)

    async def tag(self, uid, db_ready, img, uri, crated, metadata):
        with torch.no_grad():
            # run clip
            image = self.preprocess(img).unsqueeze(0).to(self.device)
            image_features = await self.loop.run_in_executor(None, self.model.encode_image, image)
            image_features /= image_features.norm(dim=1, keepdim=True)

            # run classifiers
            tags = set()
            for classifier in self.classifiers:
                # cosine similarity
                logits_per_image = self.logit_scale * image_features @ classifier['encodings'].t()

                # calculate probabilities
                probs = logits_per_image.softmax(dim=-1).cpu()[0]
                idx = torch.argmax(probs)

                if probs[idx] > classifier.get('threshold', 0):
                    if isinstance(classifier['labels'][idx], str):
                        tags.add(classifier['labels'][idx])
                    else:
                        tags |= set(classifier['labels'][idx])

        # wait for database
        await db_ready.wait()

        # send tag events
        await asyncio.gather(*map(lambda tag: self.bus.emit('tag', (uid, tag, {})), tags))
