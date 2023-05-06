

read_only = ['read']
crud = ['create', 'read', 'update', 'delete']
ru = ['read', 'update']
create = ['create', 'read', 'update']
attach = ['attach', 'detach']
hard_delete = ['hard-delete']



GROUP_DICT = {
    'AdminGroup': {},
    'AccountGroup': {
        'account': ru,
    },
}