import os
import time
import argparse
import datetime

from src.dataset.coco import convertToCoco
from src.utils.utils import getDevice, fix_random_seed
from src.dataset.lvis_utils import append_categories, swap_categories_ids, fix_annotations





def main(args):
    path = args.path
    if not os.path.exists(path):
        raise FileNotFoundError(f"Path {path} does not exist")

    img_path = os.path.join(path, "images")
    if not os.path.exists(path):
        raise ValueError(f"Path {path} does not exist")

    modelOutputPath = ""
    if args.train:
        modelOutputPath = os.path.join(os.getcwd(), "ckpts", "sammask_rcnn_" + str(datetime.datetime.fromtimestamp(int(time.time()))))
        if not os.path.exists(modelOutputPath):
            os.makedirs(modelOutputPath)
    elif args.resume:
        modelOutputPath = args.resume
    elif args.perf or args.eval or args.demo:
        if args.perf:
            modelOutputPath = args.perf
        elif args.eval:
            modelOutputPath = args.eval
        elif args.demo:
            modelOutputPath = args.demo

    if not os.path.exists(modelOutputPath) and not args.sample:
        raise ValueError(f"Path {modelOutputPath} does not exist")


    # Check if dataset annotations json file is already preprocessed
    annoPath = os.path.join(path, "annotations")
    metadataPath = os.path.join(annoPath, "ego_objects_metadata.json")
    for split in ["eval", "train"]:
        if not os.path.exists(os.path.join(annoPath, f"ego_objects_{split}_fixed.json")):
            print("Fixing annotations for split: ", split)
            splitPath = os.path.join(annoPath, "ego_objects_" + split + ".json")
            fix_annotations(splitPath, metadataPath, split)

        # Convert to COCO if necessary
        if not os.path.exists(os.path.join(path, "COCO")):
            os.makedirs(os.path.join(path, "COCO"))
        if not os.path.exists(os.path.join(path, "COCO", f"ego_objects_{split}.json")):
            print("Converting to COCO format for split: ", split)
            src_json = os.path.join(annoPath, f"ego_objects_{split}_fixed.json")
            output_json = os.path.join(path, "COCO", f"ego_objects_{split}_nomask.json")
            convertToCoco(src_json, output_json)


    # Check if dataset masks are present
    # TODO: Convert to COCO and then create masks with SAM so that mask are directly saved in right format






if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EgoObject Istance Segmentation with SAMASK-RCNN")
    parser.add_argument("--path", type=str, default=os.path.join(os.getcwd(), "data", "EgoObjects"), help="Path to the data directory")
    parser.add_argument("--sample", action="store_true", default=False, help="Plot a sample image from the dataset with ground truth masks")
    parser.add_argument("--train", action="store_true", default=False, help="Force Training of the model")
    parser.add_argument("--demo", type=str, default="", help="Run a demo of inference on 3 random image from the validation set with the model at the specified path")
    parser.add_argument("--perf", type=str, default="", help="Plot the performance of the model at the specified path")
    parser.add_argument("--eval", type=str, default="", help="Evaluate the model at the specified path")
    parser.add_argument("--save", action="store_true", default=False, help="Save the demo images to the model directory")
    parser.add_argument("--resume", type=str, default="", help="Resume training from the specified model path")
    parser.add_argument("--epochs", type=int, default=10, help="Number of epochs to train the model")
    args = parser.parse_args()

    main(args)