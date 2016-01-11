import hashlib
import os
import time


def time_cached(pause):
    def cached(fn):
        def wrapped_fn(*args, **kwargs):
            if not os.path.exists('.cache'):
                os.mkdir('.cache')
            arg = args[1]
            file_path = os.path.join('.cache',
                                     hashlib.md5(str(arg)).hexdigest() + '.dat')
            time_stamp, res_text = read_timestamp_and_text(file_path)
            current_time = time.time()
            if current_time - time_stamp >= pause:
                res_text = fn(*args, **kwargs)
                write_timestamp_and_text(file_path, current_time, res_text)
            return res_text
        return wrapped_fn
    return cached


def read_timestamp_and_text(file_name):
    """Reads elements from the cache file."""
    try:
        with open(file_name, 'r') as cache_file:
            timestamp = float(cache_file.readline())
            cached_text = cache_file.read()
    except IOError:
        timestamp = 0
        cached_text = ''
    return timestamp, cached_text


def write_timestamp_and_text(file_name, timestamp, text):
    """Writing elements to the cache file"""
    cache_file = open(file_name, 'w')
    cache_file.write(str(timestamp) + '\n')
    cache_file.write(str(text) + '\n')
    cache_file.close()
