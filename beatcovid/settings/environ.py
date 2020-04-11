
import os

import environ

env = environ.Env(DEBUG=(bool, False), USE_S3=(bool, False))

def load_environment(ENV_PATH):
    if os.path.isfile(ENV_PATH):
        print(f"Loading env from {ENV_PATH}")
        env.read_env(ENV_PATH)
