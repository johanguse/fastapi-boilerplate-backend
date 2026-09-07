def test_types_exports_exist():
    # Importing common.types should expose these names via __all__
    from src.common import types

    # When not TYPE_CHECKING, these are aliases to Any. Just ensure attributes exist.
    for name in [
        'ActivityLog',
        'User',
        'Project',
        'Organization',
        'OrganizationMember',
        'OrganizationInvitation',
    ]:
        assert hasattr(types, name), f'{name} should exist on common.types'
