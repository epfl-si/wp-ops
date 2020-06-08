class FilterModule(object):
    '''
    custom jinja2 filters for working with integers
    '''

    def filters(self):
        return {
            'int': self.int
        }

    def int(self, input, radix = None):
        if isinstance(input, int):
            return input
        elif radix is not None:
            return int(input, radix)
        elif input.startswith("0"):
            return int(input, 8)
        elif input.startswith("0x"):
            return int(input[2:], 16)
        else:
            raise Error("Unable to guess radix of " + input)
