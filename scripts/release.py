import subprocess

def get_latest_tag() -> str:
    tag = input("Enter the latest tag: ")
    return tag

def release() -> None:
    # Checkout to main branch
    subprocess.run(["git", "checkout", "main"])
    # Pull the latest changes
    subprocess.run(["git", "pull", "origin", "main"])
    # Create a new tag
    subprocess.run(["git", "tag", "-a", get_latest_tag(), "-m", "Release " + get_latest_tag()])
    # Push the tag
    subprocess.run(["git", "push", "--tags"])

if __name__ == "__main__":
    release()
