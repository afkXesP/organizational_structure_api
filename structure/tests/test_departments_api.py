import pytest
from rest_framework.test import APIClient
from structure.models import Department, Employee


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
def test_create_department(api_client):
    response = api_client.post('/api/departments/', {'name': 'IT', 'parent': None}, format='json')

    assert response.status_code == 201
    assert Department.objects.count() == 1
    assert Department.objects.first().name == 'IT'


@pytest.mark.django_db
def test_department_unique_within_parent(api_client):
    parent = Department.objects.create(name='IT')
    Department.objects.create(name='IT', parent=parent)

    response = api_client.post('/api/departments/', {'name': 'IT', 'parent': parent.id}, format='json')

    assert response.status_code == 400


@pytest.mark.django_db
def test_create_a_cycle_in_a_tree(api_client):
    a = Department.objects.create(name='A')
    b = Department.objects.create(name='B', parent=a)
    c = Department.objects.create(name='C', parent=b)
    response = api_client.patch(f'/api/departments/{a.id}/', {'parent': c.id}, format='json')

    assert response.status_code in (400, 409)


@pytest.mark.django_db
def test_create_employee(api_client):
    department = Department.objects.create(name='IT')

    response = api_client.post(f'/api/departments/{department.id}/employees/',{
                                'full_name': 'Ivan Ivanov',
                                'position': 'Developer',
                                'hired_at': '2026-01-01',
                               }, format='json')

    assert response.status_code == 201
    assert Employee.objects.count() == 1
    assert Employee.objects.first().department == department


@pytest.mark.django_db
def test_create_employee_with_nonexistent_department(api_client):
    response  = api_client.post(f'/api/departments/{999}/employees/', {
                                'full_name': 'Ivan Ivanov',
                                'position': 'Developer',}, format='json')

    assert response.status_code == 404


@pytest.mark.django_db
def test_get_department_with_depth(api_client):
    root = Department.objects.create(name='IT')
    child = Department.objects.create(name='Backend', parent=root)
    Department.objects.create(name='DevOps', parent=child)

    response = api_client.get(f'/api/departments/{root.id}/?depth=1')

    assert response.status_code == 200

    children = response.data['children']
    assert len(children) == 1
    assert children[0]['name'] == 'Backend'
    assert children[0]['children'] == []


@pytest.mark.django_db
def test_delete_department_reassign(api_client):
    root = Department.objects.create(name='IT')
    hr = Department.objects.create(name='HR')
    employee = Employee.objects.create(department=hr, full_name='Ivan Ivanov', position='HR')

    response = api_client.delete(f'/api/departments/{hr.id}/?mode=reassign&reassign_to_department_id={root.id}')

    assert response.status_code == 204

    employee.refresh_from_db()
    assert employee.department == root


@pytest.mark.django_db
def test_delete_department_cascade(api_client):
    department = Department.objects.create(name='IT')
    Employee.objects.create(department=department, full_name='Ivan Ivanov', position='Developer')

    response = api_client.delete(f'/api/departments/{department.id}/?mode=cascade')

    assert response.status_code == 204
    assert Department.objects.count() == 0
    assert Employee.objects.count() == 0
