import modal

app = modal.App("gpu-check")

image = modal.Image.debian_slim().pip_install("torch")

@app.function(
    image=image,
    gpu="A100-80GB",
    timeout=300,
)
def check_gpu():
    import torch

    print("CUDA available:", torch.cuda.is_available())

    if torch.cuda.is_available():
        props = torch.cuda.get_device_properties(0)
        print("GPU:", torch.cuda.get_device_name(0))
        print("VRAM GB:", round(props.total_memory / (1024**3), 2))


@app.local_entrypoint()
def main():
    check_gpu.remote()