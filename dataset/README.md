# Datasets

Image datasets staged on **5090** for generation / training experiments.

- **Machine:** 5090 (`192.168.10.33`)
- **Mount:** `/mnt/ssd4t` (Crucial T700 4TB NVMe, `nvme2n1p1`)
- **Root path:** `/mnt/ssd4t/datasets/`
- **Ownership:** `zx:zx`

## Overview

| Dataset | Size on disk | Images | Resolution | Source |
|---|---|---|---|---|
| cifar10 | 341 MB | 60,000 | 32×32 | classic torchvision download |
| flowers102 | 676 MB | 8,189 | variable | [Oxford VGG](https://www.robots.ox.ac.uk/~vgg/data/flowers/102/) |
| tiny_imagenet | 717 MB | 110,000 | 64×64 | [Stanford cs231n](http://cs231n.stanford.edu/tiny-imagenet-200.zip) |
| celeba | 3.1 GB | 202,599 | 178×218 aligned | [archive.org mirror](https://archive.org/details/celeba) |
| ffhq128 | 4.1 GB | 70,000 | 128×128 | [HF nuwandaa/ffhq128](https://huggingface.co/datasets/nuwandaa/ffhq128) |
| celeba_hq | 5.2 GB | 30,000 | 256×256 preprocessed | [StarGAN v2 Dropbox](https://github.com/clovaai/stargan-v2) |
| afhq (v2) | 13 GB | 15,000 | 512×512 | [StarGAN v2 Dropbox](https://github.com/clovaai/stargan-v2) |

Totals: ~27 GB. Original archives (zip/tgz) are kept alongside extracted content for easy re-extraction.

## Layout

```
/mnt/ssd4t/datasets/
├── cifar10/
│   ├── cifar-10-batches-py/            # 178 MB — unpacked pickled batches
│   └── cifar-10-python.tar.gz          # 163 MB
├── flowers102/
│   ├── 102flowers.tgz                  # 329 MB
│   ├── jpg/                            # 348 MB — 8,189 images
│   ├── imagelabels.mat                 # class labels (1..102)
│   └── setid.mat                       # train/val/test split ids
├── tiny_imagenet/
│   ├── tiny-imagenet-200.zip           # 237 MB
│   └── tiny-imagenet-200/              # 481 MB
│       ├── train/  val/  test/
│       ├── wnids.txt                   # 200 class ids
│       └── words.txt                   # wnid → human label
├── celeba/                             # images + all 6 annotation files
│   ├── img_align_celeba.zip            # 1.4 GB
│   ├── img_align_celeba/               # 1.7 GB — 202,599 JPGs
│   ├── list_attr_celeba.txt            # 40-attribute labels
│   ├── list_bbox_celeba.txt
│   ├── list_eval_partition.txt         # train/val/test split
│   ├── list_landmarks_align_celeba.txt
│   ├── list_landmarks_celeba.txt
│   └── identity_CelebA.txt
├── ffhq128/
│   ├── thumbnails128x128.zip           # 2.0 GB
│   └── thumbnails128x128/              # 2.1 GB — 70,000 PNGs
├── celeba_hq/                          # StarGAN v2 preprocessed (train/val split)
│   ├── celeba_hq.zip                   # 2.6 GB
│   └── celeba_hq/
│       ├── train/                      # female/ male/
│       └── val/
└── afhq/                               # StarGAN v2 v2 (512×512)
    ├── afhq_v2.zip                     # 6.5 GB
    ├── train/                          # cat/ dog/ wild/
    └── test/
```

## Typical use

- **Small sanity runs:** cifar10, flowers102, tiny_imagenet (fit in RAM, fast epochs)
- **Face generation:** celeba (64/128), ffhq128 (128), celeba_hq (256)
- **Multi-domain generation:** afhq (cat/dog/wild), celeba_hq (female/male via StarGAN v2 split)

## Free space

The 4 TB T700 has ~3.4 TB free after these — plenty of room for `checkpoints/`, `logs/`, `exports/` which live alongside `datasets/` on the same drive.

## Adding more datasets

- Prefer resumable HTTP mirrors: `wget -c --progress=dot:giga <url>`
- Log to `/mnt/ssd4t/tmp/dl_logs/<dataset>.log`
- Unpack in-place; keep the original archive unless space gets tight
