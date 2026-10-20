"""Stand-in for google.colab.drive: mount() just creates the folder."""
import os


def mount(path, force_remount=False):
    os.makedirs(os.path.join(path, "MyDrive"), exist_ok=True)
    # After chapter 13 the learner's Drive already holds soseki_gpt.pt (saved in that chapter).
    chapter = os.environ.get("VERIFY_CHAPTER", "99")
    saved = os.path.join(path, "MyDrive", "tsukuru-llm", "soseki_gpt.pt")
    cached = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", ".cache", "models", "soseki_gpt.pt")
    if chapter[:2].isdigit() and int(chapter[:2]) > 13 and not os.path.exists(saved) and os.path.exists(cached):
        import shutil
        os.makedirs(os.path.dirname(saved), exist_ok=True)
        shutil.copy(cached, saved)
    print(f"Mounted at {path}")


def flush_and_unmount():
    pass
