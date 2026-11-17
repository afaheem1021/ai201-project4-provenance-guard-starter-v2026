"""Test-only process: inject one detector fault; never imported by the normal launcher."""
import argparse
import os


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, required=True)
    parser.add_argument('--log-dir', required=True)
    parser.add_argument('--fault', choices=['unavailable', 'unexpected'], required=True)
    args = parser.parse_args()
    os.environ.update(AI201_DEBUG='0', HOST='127.0.0.1', PORT=str(args.port), AI201_LOG_DIR=args.log_dir)
    import detector
    from app import app

    def fail(text):
        if args.fault == 'unavailable':
            raise detector.DetectorUnavailable('Controlled capstone fault')
        raise RuntimeError('Controlled capstone fault')

    detector.model_signal = fail
    app.config.update(DEBUG=False, TESTING=False, PROPAGATE_EXCEPTIONS=False)
    app.run(host='127.0.0.1', port=args.port, debug=False, use_reloader=False, threaded=False)


if __name__ == '__main__':
    main()
