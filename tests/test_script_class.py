import clap

# NOTE: `min` and `max` are built-in functions in Python, but in the following
# function, they are overwritten by the parameter names. If needed, you can
# reimport these functions under different names from the `builtins` module::
#
# from builtins import min as __min__
# from builtins import max as __max__


@clap.Command
def fizzbuzz(min: int = 1, max: int = 100, /) -> None:
    mapping = {
        3: "Fizz",
        5: "Buzz",
    }
    buffer = ""

    start, stop = sorted((min, max))
    index_width = len(str(stop))

    for i in range(start, stop + 1):  # +1 to make the stop argument inclusive
        for n, word in mapping.items():
            if i > 0 and i % n == 0:
                buffer += word

        print("{0:0>{1}d}: {2}".format(i, index_width, buffer))
        buffer *= 0  # clear the buffer


if __name__ == "__main__":
    fizzbuzz()
