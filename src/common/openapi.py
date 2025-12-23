from typing import Any

from fastapi.openapi.utils import get_openapi

from src.common.config import settings


def _update_schema_ref(schema: dict[str, Any]) -> None:
    """Update schema reference to include components."""
    if '$ref' in schema:
        ref = schema['$ref']
        if not ref.startswith('#/components/'):
            schema['$ref'] = f'#/components/schemas/{ref.split("/")[-1]}'

    if 'items' in schema and '$ref' in schema['items']:
        ref = schema['items']['$ref']
        if not ref.startswith('#/components/'):
            schema['items']['$ref'] = (
                f'#/components/schemas/{ref.split("/")[-1]}'
            )


def _process_content_schema(content: dict[str, Any]) -> None:
    """Process content schema and update references."""
    if 'application/json' in content:
        schema = content['application/json'].get('schema', {})
        _update_schema_ref(schema)


def _process_response(response: dict[str, Any]) -> None:
    """Process response and update content schemas."""
    if 'content' in response:
        _process_content_schema(response['content'])


def _process_method(method: dict[str, Any]) -> None:
    """Process method and update responses."""
    if 'responses' in method:
        for response in method['responses'].values():
            _process_response(response)


def _generate_clean_operation_id(
    path: str, http_method: str, operation: dict[str, Any]
) -> str:
    """Generate clean operation ID for better SDK method names.

    Converts paths like:
    - /api/v1/auth/sign-in/email -> authSignInEmail
    - /api/v1/users/{user_id} -> usersGetById (for GET), usersUpdateById (for PUT)
    - /api/v1/organizations -> organizationsList (for GET), organizationsCreate (for POST)
    """
    # Remove API prefix
    clean_path = path.replace(settings.API_V1_STR, '').strip('/')

    # Split path into segments
    segments = clean_path.split('/')

    # Remove path parameters (e.g., {user_id})
    clean_segments = []
    has_path_param = False
    for segment in segments:
        if segment.startswith('{') and segment.endswith('}'):
            has_path_param = True
        else:
            # Convert kebab-case to camelCase
            parts = segment.replace('-', '_').split('_')
            if clean_segments:
                # CamelCase for subsequent segments
                segment = parts[0] + ''.join(p.capitalize() for p in parts[1:])
            else:
                # Keep first segment lowercase
                segment = parts[0] + ''.join(p.capitalize() for p in parts[1:])
            clean_segments.append(segment)

    # Build base name
    base_name = ''.join(
        s.capitalize() if i > 0 else s for i, s in enumerate(clean_segments)
    )

    # Add action based on HTTP method and path parameters
    method_prefixes = {
        'get': 'get' if has_path_param else 'list',
        'post': 'create',
        'put': 'update',
        'patch': 'update',
        'delete': 'delete',
    }

    prefix = method_prefixes.get(http_method.lower(), http_method.lower())

    # Special case: if it looks like an action endpoint (sign-in, sign-out, etc.)
    # just use the path as the operation name
    action_patterns = [
        'signIn',
        'signUp',
        'signOut',
        'forgotPassword',
        'resetPassword',
        'verify',
        'refresh',
        'resend',
        'callback',
    ]
    for pattern in action_patterns:
        if pattern.lower() in base_name.lower():
            return base_name[0].lower() + base_name[1:]

    # For standard CRUD operations
    if has_path_param:
        return f'{base_name}{prefix.capitalize()}ById'
    elif http_method.lower() == 'get':
        return f'{base_name}List'
    else:
        return f'{base_name}{prefix.capitalize()}'


def _process_paths(paths: dict[str, Any]) -> dict[str, Any]:
    """Process paths and return updated paths dict."""
    processed_paths = {}

    for path, path_obj in paths.items():
        # Add API prefix if not present
        if path.startswith(settings.API_V1_STR):
            processed_paths[path] = path_obj
        else:
            processed_paths[f'{settings.API_V1_STR}{path}'] = path_obj

        # Process each method in path
        for http_method, method in path_obj.items():
            if isinstance(method, dict):
                _process_method(method)
                # Generate clean operation ID if not already set or if it's auto-generated
                current_op_id = method.get('operationId', '')
                # FastAPI generates operationId like "function_name_path_method"
                # Replace with cleaner version
                if current_op_id and '_' in current_op_id:
                    method['operationId'] = _generate_clean_operation_id(
                        path, http_method, method
                    )

    return processed_paths  # type: ignore


def _initialize_components(schema: dict[str, Any]) -> None:
    """Initialize components in OpenAPI schema."""
    if 'components' not in schema:
        schema['components'] = {}

    schema['components']['securitySchemes'] = {
        'JWT': {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT',
            'description': 'Enter JWT token',
        }
    }

    if 'schemas' not in schema['components']:
        schema['components']['schemas'] = {}


def custom_openapi(app: Any) -> dict[str, Any]:
    """Generate custom OpenAPI schema for the application."""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=settings.PROJECT_NAME,
        version='1.0.0',
        description=settings.PROJECT_DESCRIPTION,
        routes=app.routes,
    )

    # Initialize components and security schemes
    _initialize_components(openapi_schema)

    # Add global security requirement
    openapi_schema['security'] = [{'JWT': []}]

    # Process and update paths
    openapi_schema['paths'] = _process_paths(openapi_schema.get('paths', {}))

    app.openapi_schema = openapi_schema
    return app.openapi_schema
