"""Actionable startup checks for the repository-local SimpleCADAPI runtime."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import threading
from pathlib import Path
from typing import Any

from agent.project_contract import (
    CAD_BACKEND_NAME,
    REQUIRED_PUBLIC_IMPORTS,
    SIMPLECADAPI_SOURCE_ROOT,
    SIMPLECADAPI_VERSION,
    ensure_vendored_import_path,
    import_vendored_simplecadapi,
    vendored_source_is_available,
)

_RUNTIME_CACHE: dict[str, dict[str, Any]] = {}
_RUNTIME_CACHE_LOCK = threading.Lock()


def _check(ok: bool, *, detail: str, **extra: Any) -> dict[str, Any]:
    return {"ok": bool(ok), "detail": detail, **extra}


def _run_sandbox_probe(script: str, *, timeout_seconds: int = 30) -> tuple[bool, str]:
    """Run a short probe through the same Bubblewrap boundary as CAD builds."""
    from agent.sandbox import command as sandbox_command

    with tempfile.TemporaryDirectory(prefix="simplecadapi-diagnostic-") as directory:
        workspace = Path(directory)
        (workspace / "probe.py").write_text(script, encoding="utf-8")
        command, seccomp_fd = sandbox_command(
            workspace,
            ["probe.py"],
            writable=True,
            timeout_seconds=timeout_seconds,
        )
        try:
            completed = subprocess.run(
                command,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=timeout_seconds + 5,
                pass_fds=(seccomp_fd,),
                check=False,
            )
        finally:
            os.close(seccomp_fd)
        if completed.returncode == 0:
            return True, (completed.stdout or "").strip() or "Sandbox probe completed."
        detail = (completed.stderr or completed.stdout or "").strip()
        if len(detail) > 1200:
            detail = detail[-1200:]
        return False, detail or f"Sandbox probe exited with code {completed.returncode}."


def _runtime_diagnostics() -> dict[str, Any]:
    """Run package/sandbox checks once per vendored source and SDK version."""
    cache_key = f"{SIMPLECADAPI_SOURCE_ROOT.resolve()}::{SIMPLECADAPI_VERSION}"
    with _RUNTIME_CACHE_LOCK:
        cached = _RUNTIME_CACHE.get(cache_key)
    if cached is not None:
        return json.loads(json.dumps(cached))

    failures: list[str] = []
    source = _check(
        vendored_source_is_available(),
        detail=(
            f"Using repository-local source at {SIMPLECADAPI_SOURCE_ROOT}."
            if vendored_source_is_available()
            else f"Vendored SimpleCADAPI source is missing at {SIMPLECADAPI_SOURCE_ROOT}."
        ),
        path=str(SIMPLECADAPI_SOURCE_ROOT),
    )
    if not source["ok"]:
        failures.append(source["detail"] + " Restore the SimpleCADAPI directory before starting the app.")

    module: Any | None = None
    origin = ""
    try:
        ensure_vendored_import_path()
        module = import_vendored_simplecadapi()
        origin = str(Path(module.__file__).resolve())
        version = str(getattr(module, "__version__", "") or SIMPLECADAPI_VERSION)
        version_ok = version == SIMPLECADAPI_VERSION
        version_check = _check(
            version_ok,
            detail=(
                f"Runtime {CAD_BACKEND_NAME} version {version} matches the declared vendored version."
                if version_ok
                else f"Runtime {CAD_BACKEND_NAME} version {version!r} does not match declared {SIMPLECADAPI_VERSION!r}."
            ),
            expected=SIMPLECADAPI_VERSION,
            actual=version,
            origin=origin,
        )
        if not version_ok:
            failures.append(version_check["detail"] + " Reinstall the repository-local package.")
    except Exception as error:  # noqa: BLE001 - diagnostics must report import failures.
        version_check = _check(
            False,
            detail=f"Could not import repository-local {CAD_BACKEND_NAME}: {error}",
            expected=SIMPLECADAPI_VERSION,
            actual=None,
            origin=origin or None,
        )
        failures.append(
            version_check["detail"]
            + " Run ./install.sh so the vendored package and its dependencies are installed."
        )

    import_results: dict[str, Any] = {}
    imports_ok = module is not None
    if module is not None:
        for module_name, attribute in REQUIRED_PUBLIC_IMPORTS:
            key = f"{module_name}.{attribute}"
            available = hasattr(module, attribute)
            import_results[key] = {
                "ok": available,
                "detail": (
                    f"Public import {key} is available."
                    if available
                    else f"Public import {key} is missing."
                ),
            }
            imports_ok = imports_ok and bool(import_results[key]["ok"])
    else:
        for module_name, attribute in REQUIRED_PUBLIC_IMPORTS:
            import_results[f"{module_name}.{attribute}"] = {
                "ok": False,
                "detail": "Skipped because SimpleCADAPI could not be imported.",
            }
    imports_check = _check(
        imports_ok,
        detail=(
            "All required public SimpleCADAPI imports are available."
            if imports_ok
            else "One or more required public SimpleCADAPI imports are unavailable."
        ),
        required=import_results,
    )
    if not imports_ok:
        missing = [name for name, result in import_results.items() if not result["ok"]]
        failures.append(
            imports_check["detail"]
            + " Missing: "
            + ", ".join(missing)
            + ". Check the vendored package installation."
        )

    rendering_ok = False
    rendering_detail = "Rendering check skipped because SimpleCADAPI could not be imported."
    if module is not None and imports_ok:
        try:
            import vtk  # type: ignore[import-untyped]  # noqa: F401

            rendering_ok = True
            rendering_detail = "SimpleCADAPI screenshot rendering and VTK are available."
        except ImportError as error:
            rendering_detail = f"SimpleCADAPI rendering support is unavailable: {error}"
    rendering_check = _check(rendering_ok, detail=rendering_detail)
    if not rendering_ok:
        failures.append(
            rendering_detail
            + " Install the rendering dependency (VTK) in the application environment."
        )

    sandbox_ok = False
    sandbox_detail = "Sandbox check was not run."
    try:
        sandbox_ok, sandbox_detail = _run_sandbox_probe(
            "print('simplecadapi sandbox ready')\n"
        )
    except Exception as error:  # noqa: BLE001 - diagnostics must remain actionable.
        sandbox_detail = f"Sandbox access failed: {error}"
    sandbox_check = _check(sandbox_ok, detail=sandbox_detail)
    if not sandbox_ok:
        failures.append(
            sandbox_detail
            + " Install bubblewrap and libseccomp, then verify the local sandbox can start."
        )

    smoke_ok = False
    smoke_detail = "CAD smoke test was not run."
    if module is not None and imports_ok and sandbox_ok:
        smoke_script = """
from simplecadapi import capture_result, make_box_rsolid, make_part_rpart, model
from simplecadapi import render_screenshot_rpath

@model(graph_id="startup-smoke")
def build_smoke_part():
    body = make_box_rsolid(width=1.0, height=2.0, depth=3.0)
    part = make_part_rpart(part_id="startup_smoke", body=body)
    capture_result(value=part)
    return part

result = build_smoke_part()
if result.value.body.get_volume() <= 0:
    raise RuntimeError("SimpleCADAPI smoke Part has non-positive volume")
render_screenshot_rpath(
    shapes=result.value.body,
    output_path="smoke.png",
    image_size=(64, 64),
    show_axes=False,
    show_legend=False,
    show_callouts=False,
)
if not __import__("pathlib").Path("smoke.png").is_file():
    raise RuntimeError("SimpleCADAPI smoke renderer did not produce smoke.png")
print("SimpleCADAPI CAD smoke test passed")
"""
        try:
            smoke_ok, smoke_detail = _run_sandbox_probe(smoke_script)
        except Exception as error:  # noqa: BLE001
            smoke_detail = f"CAD smoke test failed to start: {error}"
    elif module is not None and imports_ok:
        smoke_detail = "CAD smoke test was skipped because the sandbox is unavailable."
    smoke_check = _check(smoke_ok, detail=smoke_detail)
    if not smoke_ok:
        failures.append(
            smoke_detail
            + " Verify the vendored SimpleCADAPI dependencies and sandbox runtime."
        )

    result = {
        "source": source,
        "version": version_check,
        "imports": imports_check,
        "rendering": rendering_check,
        "sandbox": sandbox_check,
        "smoke_test": smoke_check,
        "failures": failures,
        "ok": not failures,
    }
    with _RUNTIME_CACHE_LOCK:
        _RUNTIME_CACHE[cache_key] = json.loads(json.dumps(result))
    return result


def run_startup_diagnostics(settings: Any, *, force: bool = False) -> dict[str, Any]:
    """Return startup checks with workspace/LLM checks and actionable failures."""
    if force:
        with _RUNTIME_CACHE_LOCK:
            _RUNTIME_CACHE.clear()
    runtime = _runtime_diagnostics()
    failures = list(runtime["failures"])
    from agent.settings import resolve_api_key

    api_key, _ = resolve_api_key(settings)
    workspace_ok = False
    workspace_detail = "Workspace has not been checked."
    try:
        settings.workspace_root.mkdir(parents=True, exist_ok=True)
        probe = settings.workspace_root / ".simplecadapi-preflight-probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        workspace_ok = True
        workspace_detail = f"Workspace is writable: {settings.workspace_root}."
    except OSError as error:
        workspace_detail = f"Workspace is not writable at {settings.workspace_root}: {error}"
    if not workspace_ok:
        failures.append(workspace_detail + " Choose a writable workspace_root.")

    setup_messages: list[str] = []
    if not api_key:
        setup_messages.append(
            f"No API key is configured in {settings.api_key_env}; set it before starting a Run."
        )
    if not str(settings.model).strip():
        setup_messages.append("No LLM model is configured; set llm.model before starting a Run.")

    result = {
        # ``ok`` describes the supported CAD runtime.  The API key and model
        # are separately surfaced because the setup page intentionally starts
        # before either is configured.
        "ok": not failures,
        "ready_for_run": not failures and bool(api_key) and bool(str(settings.model).strip()),
        "failures": failures,
        "setup_messages": setup_messages,
        "workspace": _check(workspace_ok, detail=workspace_detail),
        "api_key": bool(api_key),
        "model_configured": bool(str(settings.model).strip()),
        "simplecadapi": runtime,
        "sandbox": runtime["sandbox"],
        "rendering": runtime["rendering"],
        "cad_smoke_test": runtime["smoke_test"],
        # Keep the original flat preflight names for existing callers while
        # making the new contract the authoritative nested result.
        "bwrap_installed": bool(runtime["sandbox"]["ok"]),
        "seccomp": bool(runtime["sandbox"]["ok"]),
        "python_packages": bool(runtime["imports"]["ok"]),
        "workspace_writable": workspace_ok,
    }
    return result


def clear_diagnostics_cache() -> None:
    with _RUNTIME_CACHE_LOCK:
        _RUNTIME_CACHE.clear()
