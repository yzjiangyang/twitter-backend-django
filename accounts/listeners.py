def user_change(sender, instance, **kwargs):
    from accounts.services import UserService
    UserService.invalidate_user_cache(instance.id)

def user_profile_change(sender, instance, **kwargs):
    from accounts.services import UserService
    UserService.invalidate_profile_cache(instance.user_id)