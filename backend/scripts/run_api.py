from pathlib import Path
import os
import sys
import traceback

import uvicorn


LOG_FILE = Path(__file__).resolve().parents[1] / "api-startup.log"
BACKEND_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    try:
        os.chdir(BACKEND_ROOT)
        sys.path.insert(0, str(BACKEND_ROOT))
        LOG_FILE.write_text("Starting API on http://127.0.0.1:8000\n", encoding="utf-8")
        uvicorn.run("app.main:app", host="127.0.0.1", port=8000, log_level="info")
        LOG_FILE.write_text("API process exited normally\n", encoding="utf-8")
    except BaseException:
        LOG_FILE.write_text(traceback.format_exc(), encoding="utf-8")
        raise


if __name__ == "__main__":
    main()
