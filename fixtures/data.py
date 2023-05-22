

read_only = ['read']
crud = ['create', 'read', 'update', 'delete']
ru = ['read', 'update']
create = ['create', 'read', 'update']
attach = ['attach', 'detach']
hard_delete = ['hard-delete']


# DO NOT CHANGE ANYTHING HERE OR SOME TESTS WOULD FAIL
GROUP_FIXTURES_DEV = {
    'AdminGroup': {
        'description': 'Not sure what you are yet',
        'role': ru,
        'perms': attach
    },
    'AccountGroup': {
        'description': 'Account management',
        'account': ru,
    },
    'UploadGroup': {
        'description': 'Settings management',
        'avatar': ru
    },
    'EmptyGroup': {
        'description': 'Nothing here',
    },
}

GROUP_FIXTURES_PROD = {}


baseroles = {'AccountGroup', 'UploadGroup'}
ROLE_FIXTURES = {
    'admin': {*baseroles, 'AdminGroup'},
    'starter': baseroles,
}