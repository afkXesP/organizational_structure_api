from django.db import models
from rest_framework.exceptions import ValidationError


class Department(models.Model):
    """Модель подразделения организации"""
    name = models.CharField(max_length=200, blank=False)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name='children')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Гарантирует уникальность имени внутри родителя
        unique_together = ('name', 'parent')

    def clean(self):
        """Валидация на уровне модели"""
        #  Нельзя сделать подразделение родителем самого себя
        if self.parent_id and self.parent_id == self.id:
            raise ValidationError('Нельзя сделать подразделение родителем самого себя')

    def save(self, *args, **kwargs):
        """Переопределение метода сохранения"""
        self.name = self.name.strip()
        self.full_clean()
        super().save(*args, **kwargs)


class Employee(models.Model):
    """Модель сотрудника"""
    department = models.ForeignKey('Department', on_delete=models.CASCADE, related_name='employees')
    full_name = models.CharField(max_length=200, blank=False)
    position = models.CharField(max_length=200, blank=False)
    hired_at = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
