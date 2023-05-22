import datetime
import json
import os

from decimal import Decimal


CACHE_FILE = ".cache.json"


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return json.JSONEncoder.default(self, obj)


def cache(ttl: int = 0):
    def inner(func):
        def wrapper(*args, **kwargs):
            print(f"{args}  |  {kwargs}")
            is_cached = False
            now = int(datetime.datetime.utcnow().timestamp())

            if not os.path.isfile(CACHE_FILE):
                with open(CACHE_FILE, 'w') as fp:
                    fp.write(json.dumps({}))

            with open(CACHE_FILE, 'r') as fp:
                cached = json.load(fp)

            if len(args) > 1:
                func_name = f"{func.__name__}_{args[1].upper()}"
            else:
                func_name = func.__name__

            if func_name in cached.keys():
                if ttl:
                    if ttl + cached[func_name]['timestamp'] > now:
                        is_cached = True
                else:
                    is_cached = True

            if not is_cached:
                cached[func_name] = {'value': func(*args, **kwargs), 'timestamp': now}

                try:
                    with open(CACHE_FILE, 'w') as fp:
                        fp.write(json.dumps(cached, cls=DecimalEncoder))
                except Exception as e:
                    print(f"Error when saving to cache: {e}")
                    pass

            return cached[func_name]['value']

        return wrapper
    return inner