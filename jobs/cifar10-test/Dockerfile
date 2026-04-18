FROM pytorch/pytorch:2.7.0-cuda12.8-cudnn9-runtime

RUN pip install --no-cache-dir tensorboard torchvision

WORKDIR /app
COPY train.py .

ENTRYPOINT ["python", "train.py"]
