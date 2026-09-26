"""Transfer ownership only after the previous model service has stopped."""


def manage(*, parent, output, deadline, state, pause, invoke, now):
    while True:
        active = state()
        if active in ("inactive", "failed"):
            break
        if active not in ("active", "activating", "deactivating"):
            raise RuntimeError("Previous worker state is unverified")
        if now() >= deadline:
            raise TimeoutError("Handoff deadline while previous worker remains active")
        pause()
    if (parent / "completion.json").exists():
        return parent, 0
    if now() >= deadline:
        raise TimeoutError("Continuation deadline expired")
    if output.exists():
        raise FileExistsError("Continuation already exists; explicit recovery required")
    code = invoke()
    if code == 0 and not (output / "completion.json").exists():
        raise RuntimeError("Worker exited without a complete-run certificate")
    return output, code
