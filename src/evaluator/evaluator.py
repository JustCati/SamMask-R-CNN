from pycocotools.coco import COCO
from pycocotools.cocoeval import COCOeval



class Evaluator():
    def __init__(self, 
                 gt: COCO,
                 pred_box_json: str,
                 pred_mask_json: str):
        self.cocoGT = gt
        self.pred_box_json = pred_box_json
        self.pred_mask_json = pred_mask_json


    #* Single wrapper function for memory reason
    #* (Python deletes the objects only if they are in differents functions)
    def _single_compute(self, type: str = "bbox"):
        if type == "bbox":
            try: 
                self.coco_box = self.cocoGT.loadRes(self.pred_box_json)
            except:
                return [0.0] * 12
            cocoeval = COCOeval(self.cocoGT, self.coco_box, "bbox")
        elif type == "segm":
            try:
                self.coco_mask = self.cocoGT.loadRes(self.pred_mask_json)
            except:
                return [0.0] * 12
            cocoeval = COCOeval(self.cocoGT, self.coco_mask, "segm")

        cocoeval.evaluate()
        cocoeval.accumulate()
        cocoeval.summarize()
        return cocoeval.stats


    def compute_map(self):
        box_map = self._single_compute("bbox")
        mask_map = self._single_compute("segm")
        return box_map, mask_map
