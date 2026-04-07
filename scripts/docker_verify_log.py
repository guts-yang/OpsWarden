#!/usr/bin/env python3
"""Docker Compose 验证：将每步结果追加到 debug-64d860.log（NDJSON）。"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG_PATH = ROOT / "debug-64d860.log"
SESSION = "64d860"
RUN_ID = "verify-" + str(int(time.time() * 1000))


def _looks_like_registry_ipv6_fail(text: str) -> bool:
    if not text:
        return False
    return (
        "registry-1.docker.io" in text
        and ("2a03:2880" in text or "]:443" in text)
        and ("connectex" in text or "failed to do request" in text)
    )


def log_line(
    hypothesis_id: str,
    location: str,
    message: str,
    data: dict,
) -> None:
    line = {
        "sessionId": SESSION,
        "runId": RUN_ID,
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data,
        "timestamp": int(time.time() * 1000),
    }
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(line, ensure_ascii=False) + "\n")


def run_cmd(
    hypothesis_id: str,
    location: str,
    cmd: list[str],
    *,
    cwd: Path | None = None,
    timeout: int | None = 600,
) -> tuple[int, str]:
    try:
        p = subprocess.run(
            cmd,
            cwd=cwd or ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
        )
        out = (p.stdout or "") + (p.stderr or "")
        if len(out) > 8000:
            out = out[:8000] + "\n...[truncated]"
        log_line(
            hypothesis_id,
            location,
            "cmd_done",
            {"cmd": cmd, "exitCode": p.returncode, "outputTail": out},
        )
        return p.returncode, out
    except FileNotFoundError as e:
        log_line(
            hypothesis_id,
            location,
            "cmd_not_found",
            {"cmd": cmd, "error": str(e)},
        )
        return 127, str(e)
    except subprocess.TimeoutExpired:
        log_line(
            hypothesis_id,
            location,
            "cmd_timeout",
            {"cmd": cmd, "timeoutSec": timeout},
        )
        return 124, "timeout"


def main() -> int:
    # H0: record optional hub mirror overrides (no secrets)
    log_line(
        "H0",
        "scripts/docker_verify_log.py:image_overrides",
        "env_snapshot",
        {
            "DOCKERHUB_PYTHON_IMAGE": os.environ.get("DOCKERHUB_PYTHON_IMAGE", ""),
            "DOCKERHUB_NODE_IMAGE": os.environ.get("DOCKERHUB_NODE_IMAGE", ""),
            "DOCKERHUB_NGINX_IMAGE": os.environ.get("DOCKERHUB_NGINX_IMAGE", ""),
            "POSTGRES_IMAGE": os.environ.get("POSTGRES_IMAGE", ""),
        },
    )

    # H1: docker available
    code, _ = run_cmd("H1", "scripts/docker_verify_log.py:docker_version", ["docker", "version"])
    if code != 0:
        return 1

    # H2: compose config
    code, _ = run_cmd(
        "H2",
        "scripts/docker_verify_log.py:compose_config",
        ["docker", "compose", "config", "--quiet"],
    )
    if code != 0:
        return 2

    # H3: build (long)
    code, build_out = run_cmd(
        "H3",
        "scripts/docker_verify_log.py:compose_build",
        ["docker", "compose", "build"],
        timeout=1200,
    )
    if code != 0:
        if _looks_like_registry_ipv6_fail(build_out):
            log_line(
                "H3",
                "scripts/docker_verify_log.py:compose_build_hint",
                "registry_ipv6_fail_hint",
                {
                    "fixHint": "Docker 解析 Docker Hub 为 IPv6 但本机 IPv6 不可达。可选：(1) Docker Desktop → Docker Engine 合并 docker/engine-ipv4-snippet.json（ipv6:false）；(2) 在 .env 中设置 DOCKERHUB_*_IMAGE 与 POSTGRES_IMAGE 镜像站前缀，见 .env.example。",
                    "snippetPath": "docker/engine-ipv4-snippet.json",
                },
            )
        return 3

    # H4: up
    code, _ = run_cmd(
        "H4",
        "scripts/docker_verify_log.py:compose_up",
        ["docker", "compose", "up", "-d"],
        timeout=300,
    )
    run_cmd(
        "H4",
        "scripts/docker_verify_log.py:compose_ps",
        ["docker", "compose", "ps", "-a"],
        timeout=60,
    )

    # H5: HTTP health (use curl if present, else python urllib)
    try:
        import urllib.request

        for url, label in (
            ("http://127.0.0.1:8000/health", "backend_health"),
            ("http://127.0.0.1:8080/", "frontend_root"),
        ):
            try:
                with urllib.request.urlopen(url, timeout=15) as r:
                    status = r.status
                    body = r.read(2000).decode("utf-8", errors="replace")
                log_line(
                    "H5",
                    f"scripts/docker_verify_log.py:{label}",
                    "http_ok",
                    {"url": url, "status": status, "bodyPreview": body[:500]},
                )
            except Exception as e:
                log_line(
                    "H5",
                    f"scripts/docker_verify_log.py:{label}",
                    "http_fail",
                    {"url": url, "error": type(e).__name__, "detail": str(e)[:500]},
                )
    except Exception as e:
        log_line("H5", "scripts/docker_verify_log.py:http_block", "http_exception", {"error": str(e)})

    return 0 if code == 0 else 4


if __name__ == "__main__":
    sys.exit(main())
