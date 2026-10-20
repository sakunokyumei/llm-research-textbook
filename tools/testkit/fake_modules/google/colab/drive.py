"""Stand-in for google.colab.drive: mount() just creates the folder."""
import os


def mount(path, force_remount=False):
    os.makedirs(os.path.join(path, "MyDrive"), exist_ok=True)
    print(f"Mounted at {path}")


def flush_and_unmount():
    pass
