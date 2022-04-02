import asyncio
from .debounce import debounce

def debounce_async(secs):
    def decorator(func):

        @debounce(secs)
        def intermediate_function(*args, **kwargs):
            # TODO: put in a queque, prevent execution
            # and wait until the previous func finish. This may be an option
            asyncio.run(func(*args, **kwargs))

        async def wrapper(*args, **kwargs):
            intermediate_function(*args, **kwargs)

        return wrapper
    return decorator
