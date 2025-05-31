from fastapi.openapi.utils import get_openapi

from src.common.config import settings


def _update_schema_ref(schema: dict) -> None:
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


def _process_content_schema(content: dict) -> None:
    """Process content schema and update references."""
    if 'application/json' in content:
        schema = content['application/json'].get('schema', {})
        _update_schema_ref(schema)


def _process_response(response: dict) -> None:
    """Process response and update content schemas."""
    if 'content' in response:
        _process_content_schema(response['content'])


def _process_method(method: dict) -> None:
    """Process method and update responses."""
    if 'responses' in method:
        for response in method['responses'].values():
            _process_response(response)


def _process_paths(paths: dict) -> dict:
    """Process paths and return updated paths dict."""
    processed_paths = {}

    for path, path_obj in paths.items():
        # Add API prefix if not present
        if path.startswith(settings.API_V1_STR):
            processed_paths[path] = path_obj
        else:
            processed_paths[f'{settings.API_V1_STR}{path}'] = path_obj

        # Process each method in path
        for method in path_obj.values():
            _process_method(method)

    return processed_paths


def _initialize_components(schema: dict) -> None:
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


def custom_openapi(app):
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
