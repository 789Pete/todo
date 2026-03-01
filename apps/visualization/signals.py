from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.tasks.models import Tag, Task


def _invalidate_graph_cache(user_id):
    """Increment the graph cache version for the given user, invalidating all their cached graph responses."""
    version_key = f"graph_cache_version_{user_id}"
    try:
        cache.incr(version_key)
    except ValueError:
        # Key doesn't exist yet — initialise to 1
        cache.set(version_key, 1)


@receiver(post_save, sender=Task)
@receiver(post_delete, sender=Task)
def invalidate_graph_on_task_change(sender, instance, **kwargs):
    _invalidate_graph_cache(instance.user_id)


@receiver(post_save, sender=Tag)
@receiver(post_delete, sender=Tag)
def invalidate_graph_on_tag_change(sender, instance, **kwargs):
    _invalidate_graph_cache(instance.user_id)
