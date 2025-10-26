# ruff: noqa: E402, F401, I001
from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Import all models here to ensure they are registered with Base
# before any operations that need them are performed.
# as their primary purpose here is to ensure the model classes are registered.
from src.activity_log import models as activity_log_models
from src.auth import models as auth_models
from src.invitations import models as invitation_models
from src.organizations import models as organization_models
from src.projects import models as project_models
from src.subscriptions import models as subscription_models
from src.ai_analytics import models as ai_analytics_models
from src.ai_content import models as ai_content_models
from src.ai_documents import models as ai_documents_models
