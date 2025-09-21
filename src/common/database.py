from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Import all models here to ensure they are registered with Base
# before any operations that need them are performed.
# The noqa comments are to prevent linters from complaining about unused imports,
# as their primary purpose here is to ensure the model classes are registered.
from src.activity_log import models as activity_log_models  # noqa
from src.auth import models as auth_models  # noqa
from src.projects import models as project_models  # noqa
from src.organizations import models as organization_models  # noqa
