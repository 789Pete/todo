from datetime import date, timedelta

import factory
from factory.django import DjangoModelFactory

from apps.tasks.models import Tag, Task


class TagFactory(DjangoModelFactory):
    class Meta:
        model = Tag

    name = factory.Sequence(lambda n: f"Tag{n}")
    color = "#4ECDC4"
    user = factory.SubFactory("apps.accounts.tests.factories.UserFactory")


class TaskFactory(DjangoModelFactory):
    class Meta:
        model = Task

    title = factory.Faker("sentence", nb_words=4)
    description = factory.Faker("paragraph")
    status = "todo"
    priority = "medium"
    due_date = factory.LazyFunction(lambda: date.today() + timedelta(days=7))
    user = factory.SubFactory("apps.accounts.tests.factories.UserFactory")

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for tag in extracted:
                self.tags.add(tag)
