import multiprocessing

import face_recognition
import numpy as np
from sklearn.cluster import AgglomerativeClustering

from utils.interface import TagModule


def face_encodings(img, q):
    q.put(face_recognition.face_encodings(img))


class FaceTagger(TagModule):
    def __init__(self, bus, database, backend, loop, config):
        super().__init__(bus, database, backend, loop)

        self.embeddings = []
        self.bus.add_listener('scan_done', lambda *args: self.group())

    async def tag(self, img):
        # a hacky workaround to fix segfault when face_recognition.face_encodings is run directly in executor
        q = multiprocessing.Queue()
        proc = multiprocessing.Process(target=face_encodings, args=(np.array(img[1]), q))
        proc.start()
        await self.loop.run_in_executor(None, proc.join)  # non-blocking wait for process to finish
        for encoding in q.get():
            self.embeddings.append((img[0], encoding))

    async def group(self):
        """
        Coverts embeddings to person tag.
        """
        if len(self.embeddings) == 0:
            return
        X = np.array(list(map(lambda x: x[1], self.embeddings)))
        clustering = AgglomerativeClustering(
            n_clusters=None,
            metric='euclidean',
            distance_threshold=1.2  # taken from face_recognition.compare_faces * 2
        ).fit(X)

        for uid, label in zip(map(lambda x: x[0], self.embeddings), clustering.labels_):
            await self.bus.emit('tag', (uid, f'Person {label}'))
        self.embeddings = []  # delete unnecessary data and prepare for next scan
