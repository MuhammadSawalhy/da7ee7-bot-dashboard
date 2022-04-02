from threading import Timer


def debounce(secs):
    """ Decorator that will postpone a functions
        execution until after wait seconds
        have elapsed since the last time it was invoked. """
    def decorator(fn):
        task = None
        def debounced(*args, **kwargs):
            nonlocal task
            def call_it():
                fn(*args, **kwargs)
            if task:
                task.cancel()
            task = Timer(secs, call_it)
            task.start()

        return debounced
    return decorator