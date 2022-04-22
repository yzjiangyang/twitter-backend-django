from functools import wraps
from rest_framework.response import Response


def required_param(method='GET', params=None):
    if params == None:
        params = []

    def decorator(view_func):
        # pass parameters from view_func to _wrapped_view through wraps
        @wraps(view_func)
        def _wrapped_view(instance, request, *args, **kwargs):
            if method == 'GET':
                data = request.query_params
            else:
                data = request.data

            missing_params = [param for param in params if param not in data]
            if missing_params:
                params_str = ', '.join(missing_params)
                return Response({
                    'success': False,
                    'message': 'missing {} in request.'.format(params_str)
                }, status=400)
            return view_func(instance, request, *args, **kwargs)
        return _wrapped_view
    return decorator