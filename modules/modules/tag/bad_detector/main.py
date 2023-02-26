import asyncio
import os.path

import torch
import torch.nn as nn
from torchvision import models, transforms

from utils.interface import TagModule

transform = transforms.Compose([
    transforms.Resize(224),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])


class BadTagger(TagModule):
    def __init__(self, bus, database, backend, loop, config):
        super().__init__(bus, database, backend, loop)

        # check gpu
        print("GPU available" if torch.cuda.is_available() else "no GPU")
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        print("Pytorch version: ", torch.__version__)

        self.model_path = config.get('model_path', os.path.dirname(__file__)+'/model.pth')
        self.model = None
        self.model_loaded = asyncio.Event()

    async def tag(self, img):
        if not await self._is_good(img[1]):
            await self.bus.emit('tag', (img[0], 'bad', {'color': (1, .27, .27)}))

    async def _is_good(self, img):
        """
        Evaluates an image using the model
        """

        inputs = transform(img).unsqueeze(0).to(self.device)

        await self.model_loaded.wait()

        with torch.no_grad():
            outputs = await self.loop.run_in_executor(None, self.model, inputs)
        _, preds = torch.max(outputs, 1)

        return bool(preds[0])

    def _load_model(self):
        self.model = models.resnet18()
        num_ftrs = self.model.fc.in_features
        self.model.fc = nn.Linear(num_ftrs, 2)
        self.model.load_state_dict(torch.load(self.model_path))
        self.model.eval()
        self.model.to(self.device)

    async def run_forever(self):
        await self.loop.run_in_executor(None, self._load_model)

        self.model_loaded.set()
