FROM pytorch/pytorch:2.6.0-cuda12.4-cudnn9-runtime

RUN pip install --no-cache-dir tensorboard torchvision

WORKDIR /app
COPY train.py .

ENTRYPOINT ["python", "train.py"]
