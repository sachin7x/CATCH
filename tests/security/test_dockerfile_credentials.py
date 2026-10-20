from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_dockerfile_does_not_copy_private_ssh_key_into_image() -> None:
    dockerfile = (REPOSITORY_ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert "COPY ./thurl /root/.ssh/id_rsa" not in dockerfile
    assert "COPY thurl /root/.ssh/id_rsa" not in dockerfile
    assert "RUN --mount=type=ssh" in dockerfile


def test_local_ssh_key_is_gitignored_and_excluded_from_build_context() -> None:
    gitignore = (REPOSITORY_ROOT / ".gitignore").read_text(encoding="utf-8")
    dockerignore = (REPOSITORY_ROOT / ".dockerignore").read_text(encoding="utf-8")

    assert "\nthurl\n" in f"\n{gitignore}\n"
    assert "\nthurl\n" in f"\n{dockerignore}\n"
