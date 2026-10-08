from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .engine import DeployEngine
from .server import serve


def engine() -> DeployEngine:
    workspace = Path(os.environ.get("SOL_DEPLOY_WORKSPACE") or os.getcwd()).resolve()
    state_dir = Path(os.environ.get("SOL_DEPLOY_STATE_DIR") or (Path(__file__).resolve().parents[1] / ".runtime"))
    return DeployEngine(workspace_root=workspace, state_dir=state_dir)


def emit(value) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, default=str))


def main() -> None:
    parser = argparse.ArgumentParser(prog="sol-deploy")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("serve")
    p.add_argument("--host", default=None)
    p.add_argument("--port", type=int, default=None)

    p = sub.add_parser("project-create")
    p.add_argument("name")
    p.add_argument("root")

    p = sub.add_parser("service-create")
    p.add_argument("project_id")
    p.add_argument("name")
    p.add_argument("root")
    p.add_argument("--build", default="")
    p.add_argument("--start", required=True)
    p.add_argument("--health", default="/")

    for name in ("build", "deploy", "stop", "redeploy", "logs"):
        p = sub.add_parser(name)
        p.add_argument("service_id")

    args = parser.parse_args()
    if args.command == "serve":
        serve(args.host, args.port)
        return

    e = engine()
    if args.command == "project-create":
        emit(e.create_project(args.name, args.root))
    elif args.command == "service-create":
        emit(e.create_service(
            project_id=args.project_id,
            name=args.name,
            root=args.root,
            build_command=args.build,
            start_command=args.start,
            health_path=args.health,
        ))
    elif args.command == "build":
        emit(e.build(args.service_id))
    elif args.command == "deploy":
        emit(e.deploy(args.service_id))
    elif args.command == "stop":
        emit(e.stop(args.service_id))
    elif args.command == "redeploy":
        emit(e.redeploy(args.service_id))
    elif args.command == "logs":
        print(e.logs(args.service_id))


if __name__ == "__main__":
    main()
