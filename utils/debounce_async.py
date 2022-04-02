import asyncio
from .debounce import debounce

def debounce_async(secs):
    def decorator(func):

        @debounce(secs)
        def intermediate_function(*args, **kwargs):
            # TODO: put in a queque, prevent execution an wait the
            # previous func to finish. This may be an option
            asyncio.run(func(*args, **kwargs))

        # TODO: make the wrapper async as well
        async def wrapper(*args, **kwargs):
            intermediate_function(*args, **kwargs)

        return wrapper
    return decorator
