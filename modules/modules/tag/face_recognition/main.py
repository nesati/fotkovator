import concurrent.futures
import os.path
import pickle
from collections import OrderedDict

import aiofiles
import face_recognition
import numpy as np
from sklearn.cluster import AgglomerativeClustering

from utils.interface import TagModule

# create a process pool executor
executor = concurrent.futures.ProcessPoolExecutor()


class FaceTagger(TagModule):
    def __init__(self, bus, database, backend, loop, config):
        super().__init__(bus, database, backend, loop)

        self.face_db = config.get('db_path', 'face.pickle')

        if os.path.exists(self.face_db):
            with open(self.face_db, 'rb') as f:
                self.embeddings, self.uids, self.person_ids, self.aliases, self.locked = pickle.load(f)
        else:
            self.reset_db()

        self.bus.add_listener('scan_done', lambda *args: self.group())
        self.bus.add_listener('rename_tag', lambda args: self.associate(*args))
        self.bus.add_listener('img_removed', lambda uid: self.img_removed(uid))
        self.bus.add_listener('rescan', lambda args: self.rescan(*args))

    def reset_db(self):
        self.embeddings = None
        self.uids = []
        self.person_ids = []
        self.aliases = OrderedDict()
        self.locked = set()

    async def tag(self, uid, db_ready, img, uri, created, metadata):
        # the face_recognition.face_encodings must be run in a process executor as it is not thread safe
        for encoding in await self.loop.run_in_executor(executor, face_recognition.face_encodings, np.array(img)):
            if self.embeddings is None:
                self.embeddings = np.array([encoding], dtype=np.float16)
            else:
                self.embeddings = np.append(self.embeddings, encoding[np.newaxis], axis=0)
            self.uids.append(uid)

        await db_ready.wait()  # block scan_done event until database ready

    async def associate(self, old_name, new_name):
        """
        Handles rename_tag event. Associates face embedding with tag name.
        :param old_name: old tag name
        :param new_name: new tag name
        """
        # identify person id
        if old_name.startswith('Osoba'):
            person_id = int(old_name.replace('Osoba ', ''))
        else:
            try:
                person_id = self.aliases[old_name]['id']
            except KeyError:  # the tag affected is not a face tag
                return

        # identify embeddings and calculate mean
        embedding = np.mean(self.embeddings[:len(self.person_ids), :][self.person_ids == person_id], axis=0)

        # save alias
        self.aliases[new_name] = {
            'id': person_id,
            'embedding': embedding,
        }

        await self.save_db()

    async def img_removed(self, uid):
        """
        Handles img_removed event. Removes embedding from database.
        :param uid: the removed images uid
        """
        try:
            idx = self.uids.index(uid)
        except ValueError:
            pass
        else:
            self.embeddings = np.delete(self.embeddings, idx)
            self.uids.remove(uid)

        try:
            self.locked.remove(uid)
        except KeyError:
            pass

        await self.save_db()

    async def rescan(self, scan_type, db_ready):
        if scan_type in self.database.SCAN_RESET:
            self.reset_db()
            await self.save_db()

    async def save_db(self):
        async with aiofiles.open(self.face_db, 'wb') as f:
            await f.write(pickle.dumps((self.embeddings, self.uids, self.person_ids, self.aliases, self.locked)))

    async def group(self):
        """
        Coverts embeddings to person tag.
        """

        if len(self.uids) == 0:
            return

        if len(set(self.uids) - self.locked) == 0:  # no new images
            return

        distance = 1.2  # taken from face_recognition.compare_faces * 2

        if len(self.aliases) > 0:
            self.embeddings = np.append(self.embeddings,
                                        np.array(list(map(lambda alias: alias['embedding'], self.aliases.values()))),
                                        axis=0)

        # run clustering on faces + associated embeddings
        self.person_ids = AgglomerativeClustering(
            n_clusters=None,
            metric='euclidean',
            distance_threshold=distance
        ).fit_predict(self.embeddings)

        # rename clusters based on associated people
        # move associated group ids to original id
        max_index = np.max(self.person_ids)
        mapping = [-1] * (max_index + 1)
        not_used = set(range(max_index + 1))
        for idx, alias in enumerate(self.aliases.values()):
            idx2 = self.person_ids[len(self.uids) + idx]
            mapping[idx2] = alias['id']
            if alias['id'] in not_used:
                not_used.remove(alias['id'])
        not_associated = list(not_used)
        for idx in range(len(mapping)):
            if mapping[idx] == -1:
                mapping[idx] = not_used.pop()

        # apply transformation
        self.person_ids = np.select([self.person_ids == i for i in range(max_index + 1)], mapping, self.person_ids)

        # remove helper values
        if len(self.aliases) > 1:
            self.person_ids = self.person_ids[:-len(self.aliases)]
            self.embeddings = self.embeddings[:-len(self.aliases)]

        # remove all ephemeral person tags
        for i in not_associated:
            await self.bus.emit('delete_tag', (f'Osoba {i}',))

        # save tags
        for uid, label in zip(self.uids, self.person_ids):
            if uid not in self.locked or label in not_associated:
                await self.bus.emit('tag', (uid, f'Osoba {label}', {}))

        # lock tagged images
        self.locked |= set(self.uids)

        # save db
        await self.save_db()
