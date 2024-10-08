import os
import numpy as np
from PIL import Image

import torch
from torchvision.ops import box_convert
from torchvision import transforms, tv_tensors
from torchvision.datasets import VisionDataset

from pycocotools.coco import COCO






class CocoDataset(VisionDataset):
    def __init__(self, path, annFile, transform = None, target_transform = None, transforms = None):
        super().__init__(path, transforms, transform, target_transform)

        self.annfile = annFile
        self.root = path
        self.coco = COCO(annFile)
        self.ids = list(self.coco.imgs.keys())
        self.transform = transform
        self.target_transform = target_transform

    def __getitem__(self, index):
        coco = self.coco
        img_id = self.ids[index]
        ann_ids = coco.getAnnIds(imgIds=img_id)
        target = coco.loadAnns(ann_ids)


        #* Load the image
        path = coco.loadImgs(img_id)[0]['file_name']
        img = Image.open(os.path.join(self.root, path)).convert('RGB')
        img = transforms.ToTensor()(img)

        #* Load and convert to tensor the annotations
        boxes = []
        toIgnore = []
        nums = len(target)
        for i in range(nums):
            box = torch.tensor(target[i]['bbox'])
            bbox = box_convert(box, 'xywh', 'xyxy')
            #! Sanity check for positive width and height
            if bbox[2] <= bbox[0] or bbox[3] <= bbox[1]:
                toIgnore.append(i)
                continue
            boxes.append(bbox.tolist())

        areas = [target[i]['area'] for i in range(nums) if i not in toIgnore]
        masks = np.array([coco.annToMask(target[i]) for i in range(nums) if i not in toIgnore])
        labels = [target[i]['category_id'] for i in range(nums) if i not in toIgnore]

        img_id = torch.tensor([img_id])
        labels = torch.tensor(labels, dtype=torch.int64)
        is_crowd = torch.zeros((nums - len(toIgnore),), dtype=torch.int64)
        areas = torch.as_tensor(areas, dtype=torch.float32)
        boxes = tv_tensors.BoundingBoxes(boxes, format='XYXY', canvas_size=img.shape[-2:])
        masks = tv_tensors.Mask(masks)

        target = {
            "image_id": img_id,
            "labels": labels,
            "area": areas,
            "iscrowd": is_crowd,
            "boxes": boxes,
            "masks": masks
        }

        if self.transforms is not None:
            img, target = self.transforms(img, target)

        return img, target

    def get_num_classes(self):
        return len(self.coco.getCatIds())

    def __len__(self):
        return len(self.ids)
