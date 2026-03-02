from rest_framework import serializers

from .models import Department, Employee


class EmployeeSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с данными сотрудников"""
    class Meta:
        model = Employee
        fields = ['id', 'department', 'full_name', 'position', 'hired_at', 'created_at']
        read_only_fields = ['id', 'created_at', 'department']

    def validate_full_name(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError('ФИО не может быть пустым')

        if len(value) > 200:
            raise serializers.ValidationError('Максимальная длина - 200 символов')

        return value

    def validate_position(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Должность не может быть пустой')
        if len(value) > 200:
            raise serializers.ValidationError('Максимальная длина - 200 символов')
        return value


class DepartmentSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с подразделениями"""
    class Meta:
        model = Department
        fields = ['id', 'name',  'parent', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_name(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Название не может быть пустым')

        if len(value) > 200:
            raise serializers.ValidationError('Максимальная длина - 200 символов')

        return value

    def validate(self, data):
        """Валидация для связей внутри дерева"""
        name = data.get('name', getattr(self.instance, 'name', None))
        parent = data.get('parent', getattr(self.instance, 'parent', None))

        # Проверка уникальности
        queryset = Department.objects.filter(name=name, parent=parent)
        if self.instance:
            queryset = queryset.exclude(id=self.instance.id)
        if queryset.exists():
            raise serializers.ValidationError({'name': 'В этом подразделение уже есть отдел с таким названием'})

        # Защита от циклической зависимости
        if self.instance and parent:
            if parent.id == self.instance.id:
                raise serializers.ValidationError('Нельзя сделать подразделением родителем самого себя')

            # Обход вверх по дереву, для проверки, не является ли новый руководитель потомком текущего
            curr = parent
            while curr is not None:
                if curr.id == self.instance.id:
                    raise serializers.ValidationError('Нельзя переместить подразделение внутрь собственного поддерева')
                curr = curr.parent

        return data


class DepartmentDetailSerializer(serializers.ModelSerializer):
    """Сериализатор для более детального отображения дерева с вложенностью"""
    employees = serializers.SerializerMethodField()
    children = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = ['id', 'name', 'parent', 'created_at', 'employees', 'children']

    def get_employees(self, obj):
        """Получение списка сотрудников подразделения"""
        include_employees = self.context.get('include_employees', True)
        if not include_employees:
            return []
        employees = obj.employees.all().order_by('full_name')
        return EmployeeSerializer(employees, many=True).data

    def get_children(self, obj):
        """Рекурсивный вызов сериализатора для получения вложенных подразделений"""
        depth = self.context.get('depth', 1)
        if depth <= 0:
            return []

        children = obj.children.all()
        serializer = DepartmentDetailSerializer(children, many=True, context={**self.context, 'depth': depth - 1})
        return serializer.data
