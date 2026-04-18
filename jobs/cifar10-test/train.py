import os
import time
import argparse
import torch
import torch.nn as nn
import torchvision
import torchvision.transforms as T
from torch.utils.tensorboard import SummaryWriter

parser = argparse.ArgumentParser()
parser.add_argument("--data-dir", default="/data/cifar10")
parser.add_argument("--log-dir", default="/logs/cifar10-test")
parser.add_argument("--ckpt-dir", default="/checkpoints/cifar10-test")
parser.add_argument("--epochs", type=int, default=10)
parser.add_argument("--batch-size", type=int, default=512)
parser.add_argument("--lr", type=float, default=0.1)
args = parser.parse_args()

os.makedirs(args.log_dir, exist_ok=True)
os.makedirs(args.ckpt_dir, exist_ok=True)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"device: {device}")
if device.type == "cuda":
    print(f"GPU: {torch.cuda.get_device_name(0)}")

train_tf = T.Compose([
    T.RandomCrop(32, padding=4),
    T.RandomHorizontalFlip(),
    T.ToTensor(),
    T.Normalize((0.4914, 0.4822, 0.4465), (0.2470, 0.2435, 0.2616)),
])
val_tf = T.Compose([
    T.ToTensor(),
    T.Normalize((0.4914, 0.4822, 0.4465), (0.2470, 0.2435, 0.2616)),
])

train_ds = torchvision.datasets.CIFAR10(args.data_dir, train=True,  download=True, transform=train_tf)
val_ds   = torchvision.datasets.CIFAR10(args.data_dir, train=False, download=True, transform=val_tf)

train_loader = torch.utils.data.DataLoader(train_ds, batch_size=args.batch_size, shuffle=True,  num_workers=4, pin_memory=True)
val_loader   = torch.utils.data.DataLoader(val_ds,   batch_size=args.batch_size, shuffle=False, num_workers=4, pin_memory=True)

model = torchvision.models.resnet18(num_classes=10)
model.conv1 = nn.Conv2d(3, 64, kernel_size=3, stride=1, padding=1, bias=False)
model.maxpool = nn.Identity()
model = model.to(device)

optimizer = torch.optim.SGD(model.parameters(), lr=args.lr, momentum=0.9, weight_decay=5e-4)
scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)
criterion = nn.CrossEntropyLoss()

writer = SummaryWriter(log_dir=args.log_dir)
print(f"TensorBoard logs → {args.log_dir}")

for epoch in range(1, args.epochs + 1):
    model.train()
    train_loss, train_correct, train_total = 0.0, 0, 0
    t0 = time.time()
    for x, y in train_loader:
        x, y = x.to(device), y.to(device)
        optimizer.zero_grad()
        out = model(x)
        loss = criterion(out, y)
        loss.backward()
        optimizer.step()
        train_loss += loss.item() * y.size(0)
        train_correct += out.argmax(1).eq(y).sum().item()
        train_total += y.size(0)
    scheduler.step()

    model.eval()
    val_loss, val_correct, val_total = 0.0, 0, 0
    with torch.no_grad():
        for x, y in val_loader:
            x, y = x.to(device), y.to(device)
            out = model(x)
            val_loss += criterion(out, y).item() * y.size(0)
            val_correct += out.argmax(1).eq(y).sum().item()
            val_total += y.size(0)

    tl = train_loss / train_total
    ta = train_correct / train_total
    vl = val_loss / val_total
    va = val_correct / val_total
    elapsed = time.time() - t0

    writer.add_scalar("loss/train", tl, epoch)
    writer.add_scalar("loss/val",   vl, epoch)
    writer.add_scalar("acc/train",  ta, epoch)
    writer.add_scalar("acc/val",    va, epoch)
    writer.add_scalar("lr", scheduler.get_last_lr()[0], epoch)
    writer.flush()

    print(f"epoch {epoch:02d}/{args.epochs}  "
          f"train loss={tl:.4f} acc={ta:.3f}  "
          f"val loss={vl:.4f} acc={va:.3f}  "
          f"({elapsed:.1f}s)")

torch.save(model.state_dict(), os.path.join(args.ckpt_dir, "resnet18_final.pt"))
writer.close()
print("done.")
