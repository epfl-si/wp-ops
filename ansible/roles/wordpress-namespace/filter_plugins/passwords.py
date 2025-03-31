"""Deterministic replacements for Ansible's password_hash pipeline filter."""

from passlib.hash import bcrypt
from passlib.utils.binary import bcrypt64
from base64 import b64encode
from passlib.hash import md5_crypt
import re

class FilterModule(object):
    def filters(self):
        return {
            'password_hash_bcrypt': self.password_hash_bcrypt,
            'password_hash_compat': self.password_hash_compat
        }

    @staticmethod
    def to_length(seed, length):
        assert len(seed) > 0
        while len(seed) < length:
            seed = seed + seed
        return seed[:length]

    @classmethod
    def bogobase64(cls, seed, length_bytes):
        b64 = b64encode(cls.to_length(seed, length_bytes).encode('utf-8'))
        return re.sub('=*$', '', b64.decode('utf-8'))

    def password_hash_bcrypt(self, password, salt_text):
        unused_changed, salt = bcrypt64.check_repair_unused(self.bogobase64(salt_text, 16))
        return bcrypt.using(salt=salt).hash(password)

    def password_hash_compat(self, password, salt_text):
        return md5_crypt.using(salt=self.bogobase64(salt_text, 8)[8]).hash(password)
