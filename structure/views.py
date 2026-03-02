from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import Employee, Department
from .serializers import DepartmentSerializer, DepartmentDetailSerializer, EmployeeSerializer


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer

    def retrieve(self, request, *args, **kwargs):
        """Получение одного подразделения, с возможностью настройки глубины дерева"""
        department_id = kwargs.get('pk')

        # Настройка глубины вложенности (0 до 5)
        depth = int(request.GET.get('depth', 1))
        depth = max(0, min(depth, 5))

        include_employees = request.query_params.get('include_employees', 'true').lower() == 'true'

        # Оптимизация запроса через prefetch_related, чтобы избежать N+1 проблему
        department = get_object_or_404(Department.objects.prefetch_related('children', 'employees'),
                                       pk=department_id)

        serializer = DepartmentDetailSerializer(department, context={
            'depth': depth, 'include_employees': include_employees},)

        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='employees')
    def create_employee(self, request, pk=None):
        """Добавление сотрудника напрямую в конкретное подразделение"""
        department = get_object_or_404(Department, pk=pk)
        serializer = EmployeeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(department=department)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        """Частичное обновление подразделения"""
        instance = self.get_object()
        serializer = DepartmentSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """Удаление подразделения с двумя режимами: каскадным или переносом данных"""
        department = self.get_object()
        mode = request.query_params.get('mode', 'cascade')

        match mode:
            case 'cascade':
                # Каскадное удаление
                department.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)

            case 'reassign':
                # Перенос сотрудников и дочерних подразделений перед удалением
                reassign_id = request.query_params.get('reassign_to_department_id')
                if not reassign_id:
                    return Response({'detail': 'reassign_to_department_id обязателен'},
                                    status=status.HTTP_400_BAD_REQUEST)

                new_department = get_object_or_404(Department, pk=reassign_id)
                if new_department.id == department.id:
                    return Response({'detail': 'Нельзя переназначить в то же подразделение'},
                                    status=status.HTTP_400_BAD_REQUEST)

                # Либо всё переносится, либо ничего
                with transaction.atomic():
                    Employee.objects.filter(department=department).update(department=new_department)
                    Department.objects.filter(parent=department).update(parent=new_department)
                    department.delete()

                return Response(status=status.HTTP_204_NO_CONTENT)

            case _:
                return Response({'detail': 'mode должен быть cascade или reassign'},
                                status=status.HTTP_400_BAD_REQUEST)