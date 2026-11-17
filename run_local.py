"""One-command local service. Setup and model download are documented in RUNNING.md."""

import argparse
import os
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=5000)
    parser.add_argument('--log-dir', type=Path, help='Isolated audit and request logs; defaults to logs/.')
    args = parser.parse_args()
    os.environ['AI201_DEBUG'] = '0'
    os.environ['HOST'] = '127.0.0.1'
    os.environ['PORT'] = str(args.port)
    os.environ.setdefault('AI201_MODEL_OFFLINE', '1')
    if args.log_dir:
        os.environ['AI201_LOG_DIR'] = str(args.log_dir.resolve())
    from app import app
    app.config.update(DEBUG=False, TESTING=False, PROPAGATE_EXCEPTIONS=False)
    print(f"Code {app.config['CODE_REVISION']} | session {app.config['SERVICE_RUN_ID']}", flush=True)
    app.run(host='127.0.0.1', port=args.port, debug=False, use_reloader=False, threaded=False)


if __name__ == '__main__':
    main()
