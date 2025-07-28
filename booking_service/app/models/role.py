from enum import Enum


class RoleEnum(int, Enum):
    SUPERADMIN = 0
    ADMIN = 1
    CLIENT = 2
