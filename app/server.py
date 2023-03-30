#!/usr/bin/python3

import uvicorn
from os import getenv
from gunicorn.app.base import BaseApplication
from typing import Union, Any, Callable, Dict
from main import application
from config import *

class StandaloneApplication(BaseApplication):
    def __init__(self, application: Callable, options: Dict[str, Any] = None):
        self.options = options or {}
        self.application = application
        super().__init__()

    def load_config(self):
        config = {
            key: value
            for key, value in self.options.items()
            if key in self.cfg.settings and value is not None
        }
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


if __name__ == "__main__":
    if not ENV == "dev":
        options = {
            "bind": "%s:%s" % ("0.0.0.0", "7777"),
            "workers": WORKER,
            "worker_class": "uvicorn.workers.UvicornWorker",
            "timeout": TIMEOUT,
            "graceful_timeout": GRACEFUL_TIMEOUT,
            "keepalive": KEEP_ALIVE
        }
        StandaloneApplication(application, options).run()
    else:
        uvicorn.run("main:app", port=7777, reload=True)
