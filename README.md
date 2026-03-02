# API организационной структуры

---

<a name="russian-version"></a>

## REST API для управления организационной структурой компании

##  Поддерживает
- иерархию подразделений (дерево);
- сотрудников внутри подразделений;
- перемещение подразделений;
- каскадное удаление или перераспределение сотрудников;
- получение поддерева с ограничением глубины

## Технологии
* Python 3.11
* Django, Django REST Framework
* PostgreSQL
* Docker & docker-compose
* pytest

## Функциональность API
### Подразделение
| Метод  | URL                    | Описание                           |
| ------ | ---------------------- | ---------------------------------- |
| POST   | /api/departments/      | Создать подразделение              |
| GET    | /api/departments/{id}/ | Получить подразделение + поддерево |
| PATCH  | /api/departments/{id}/ | Обновить название или родителя     |
| DELETE | /api/departments/{id}/ | Удалить подразделение              |

### Сотрудники
| Метод | URL                              | Описание           |
| ----- | -------------------------------- | ------------------ |
| POST  | /api/departments/{id}/employees/ | Создать сотрудника |

### Ограничения
* Название подразделения уникально в пределах одного родителя
* Нельзя сделать подразделение родителем самого себя
* Нельзя создать цикл в дереве
* При удалении:
  - mode=cascade - удаляются все дочерние подразделения и сотрудники
  - mode=reassign - сотрудники и дочерние подразделения переводятся в другое подразделение`

## Запуск проекта

1. Клонируйте репозиторий
   ```bash
    git clone https://github.com/afkXesP/organizational_structure_api.git
    cd organizational_structure_API
   ```
   
2. Создайте файл окружения
   ```bash
    cp .env.example .env
   ```
   
3. Запустите контейнеры
   ```bash
    docker compose up --build
   ```
   После запуска контейнера API доступен по адресу: ```http://localhost:8000/api/```

### Пример .env
    DEBUG=True
    SECRET_KEY=django-secret-key
    
    POSTGRES_DB=name_db
    POSTGRES_USER=user
    POSTGRES_PASSWORD=password
    
    DB_NAME=name_db
    DB_USER=user
    DB_PASSWORD=password
    DB_HOST=db
    DB_PORT=5432

## Запуск тестов
Тесты выполняются через pytest.
* Внутри контейнера:```docker compose exec web pytest```
* Локально: ```pytest```

## Структура проект
```
    project/
    │
    ├── structure/
    │   ├── models.py
    │   ├── serializers.py
    │   ├── views.py
    │   └── tests/
    │
    ├── docker-compose.yml
    ├── Dockerfile
    ├── requirements.txt
    └── README.md
```

## Примеры запросов
### Создать подразделение
```
POST /api/departments/

{
  "name": "IT",
  "parent": null
}
```
### Создать сотрудника
```
POST /api/departments/1/employees/

{
  "full_name": "Ivan Ivanov",
  "position": "Developer",
  "hired_at": "2026-01-01"
}
```
### Получить подразделение с поддеревом
```
GET /api/departments/1/?depth=2
```
### Удалить с перераспределением
```
DELETE /api/departments/2/?mode=reassign&reassign_to_department_id=1
```
