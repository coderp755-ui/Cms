from django.db import models
from django.utils.timezone import now

from django.conf import settings


class BaseModel(models.Model):
    '''
    Base model to set custom db_table naming convention
    db_table = "<app_label>_<model_name>(lowercase)"
    '''
    class Meta:
        abstract = True

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not cls._meta.abstract:
            app_label = cls._meta.app_label  # Get the app label (alias)
            cls._meta.db_table = f"{app_label}_{cls.__name__.lower()}"


class SoftDeleteQuerySet(models.QuerySet):
    '''
    Custom QuerySet to handle soft delete operations
    .delete() - soft delete
    .hard_delete() - permanent delete
    '''
    def delete(self):
        return super().update(is_deleted=True, deleted_at=now())

    def hard_delete(self):
        return super().delete()

    def alive(self):
        return self.filter(is_deleted=False)

    def dead(self):
        return self.filter(is_deleted=True)


class SoftDeleteManager(models.Manager):
    '''
    Custom manager to use SoftDeleteQuerySet
    '''
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model).filter(is_deleted=False)

    def hard_delete(self):
        return self.get_queryset().hard_delete()


class BaseTimeStampModelMixin(BaseModel):
    """
    Base model for all pharmacy models
    created_at: The date and time the record was created.
    updated_at: The date and time the record was last updated.
    """
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when the record was created")
    updated_at = models.DateTimeField(auto_now=True, help_text="Timestamp when the record was last updated")

    class Meta:
        abstract = True


class BaseAuditModelMixin(BaseModel):
    """
    Base model for audit fields
    created_by: The user that created the record.
    updated_by: The user that updated the record.
    """
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL,
        on_delete=models.DO_NOTHING, null=True, blank=True,
        related_name='%(class)s_created_by',
        help_text="Foreign key referencing the user who created the record."
    )
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL,
        on_delete=models.DO_NOTHING, null=True, blank=True,
        related_name='%(class)s_updated_by',
        help_text="Foreign key referencing the user who updated the record."
    )

    class Meta:
        abstract = True


class SoftDeleteModelMixin(BaseModel):
    """
    Inherit this mixin to add soft delete fields: deleted_at, is_deleted
    auto assign deleted_at if is_deleted is True while saving the object
    and reset deleted_at if is_deleted is False or the object is restored
    """
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    restored_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        help_text="Foreign key referencing the user who deleted the record.",
        related_name="%(class)s_deleted_by"
    )
    restored_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        help_text="Foreign key referencing the user who restored the record.",
        related_name="%(class)s_restored_by"
    )
    objects = SoftDeleteManager()
    all_objects = SoftDeleteQuerySet.as_manager()  # To access all objects including deleted ones
    class Meta:
        abstract = True

    def delete(self, user=None):
        self.is_deleted = True
        self.deleted_at = now()
        if hasattr(self, "deleted_by") and user:
            self.deleted_by = user
        self.save()

    def hard_delete(self):
        super().delete()
    
    def restore(self, user=None):
        self.is_deleted = False
        self.restored_at = now()
        if hasattr(self, "restored_by") and user:
            self.restored_by = user
        self.save()