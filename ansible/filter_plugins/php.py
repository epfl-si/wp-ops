import phpserialize

class FilterModule(object):
    '''
    Serialize PHP things (e.g. for WordPress secrets)
    '''

    def filters(self):
        return {
            'php_serialize': self.php_serialize
        }

    def php_serialize(self, struct):
        return phpserialize.dumps(struct).decode('utf-8')
