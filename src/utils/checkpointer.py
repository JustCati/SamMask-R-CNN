import os
import torch
import os.path as osp
from glob import glob



class Checkpointer(object):
    def __init__(self, path, phase = 'train'):
        self.perf_box = 0.0
        self.perf_mask = 0.0
        self.curr_epoch = 0
        self.checkpoint = self._load_checkpoint(path)

        if self.checkpoint is not None and phase == 'train':
            self.curr_epoch = self.checkpoint.get('epoch', 0)

            self.best_checkpoint = self._load_checkpoint(glob(osp.join(osp.dirname(path), 'best_epoch_overall-*.pth'))[0])
            self.perf_box = self.best_checkpoint.get('perf_box', 0.0)
            self.perf_mask = self.best_checkpoint.get('perf_mask', 0.0)
        elif self.checkpoint is None and phase != 'train':
            raise RuntimeError('Cannot find checkpoint {}'.format(path))
        self.output_dir = osp.dirname(path) if osp.isfile(path) else path


    def load(self, model, optimizer=None, lr_scheduler=None):
        if self.checkpoint is not None:
            model.load_state_dict(self.checkpoint['model_state_dict'])
            if optimizer is not None:
                optimizer.load_state_dict(self.checkpoint['optimizer_state_dict'])
            if lr_scheduler is not None:
                lr_scheduler.load_state_dict(self.checkpoint['lr_scheduler_state_dict'])
        return model, optimizer, lr_scheduler, self.curr_epoch


    def save(self, epoch, model, optimizer, lr_scheduler, perf_box, perf_mask):
        torch.save({
            'epoch': epoch,
            'model_state_dict': model.module.state_dict() if torch.cuda.device_count() > 1 else model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            "lr_scheduler_state_dict": lr_scheduler.state_dict(),
            "perf_box": perf_box,
            "perf_mask": perf_mask,
        }, osp.join(self.output_dir, 'epoch-{}.pth'.format(epoch)))


        #* Commented out to prevent deletion of previous epoch model, this way we
        #* can manually select the best model for specific bbox or mask performance and not only overall

        # Delete previous epoch model
        # if epoch > 1:
        #     os.remove(osp.join(self.output_dir, 'epoch-{}.pth'.format(epoch-1)))
    
        # Save best model
        if self.perf_box <= perf_box and self.perf_mask <= perf_mask:
            self.perf_box = perf_box
            self.perf_mask = perf_mask

            torch.save({
                'epoch': epoch,
                'model_state_dict': model.module.state_dict() if torch.cuda.device_count() > 1 else model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                "lr_scheduler_state_dict": lr_scheduler.state_dict(),
                "perf_box": perf_box,
                "perf_mask": perf_mask,
            }, osp.join(self.output_dir, f'best_epoch_overall-{epoch}.pth'))

            # Delete previous best model
            if os.listdir(self.output_dir):
                for file in os.listdir(self.output_dir):
                    if file.startswith(f'best_epoch_overall') and file != f'best_epoch_overall-{epoch}.pth' and epoch > 1:
                        os.remove(osp.join(self.output_dir, file))


    def _load_checkpoint(self, checkpoint):
        if checkpoint is not None and osp.isfile(checkpoint):
            return torch.load(checkpoint, map_location=torch.device('cpu'))
        return None


def setup_checkpointer(path, phase):
    return Checkpointer(path, phase)
