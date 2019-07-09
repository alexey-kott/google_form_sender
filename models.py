from peewee import SqliteDatabase, Model, IntegerField, TextField, DateTimeField

db = SqliteDatabase('db.sqlite3')


class BaseModel(Model):
    class Meta:
        database = db


class Row(BaseModel):
    index = IntegerField(unique=True)
    creation_dt = TextField()
    salon = TextField()  # Наименование салона
    manager = TextField()
    new_clients = IntegerField()  # Кол-во новых клиентов
    new_calculation = IntegerField()  # Кол-во новых просчетов
    repeated_calculation = IntegerField()  # Кол-во повторных просчетов
    distributed_cutaways = IntegerField()  # Кол-во розданных визиток
    sales = IntegerField()  # Кол-во продаж
    revenue = IntegerField()  # Выручка (№ заказа, сумма, наименование)
    row_hash = TextField()


class TableCheck(BaseModel):
    """Describes table state at certain time moments"""
    check_dt = DateTimeField()
    table_hash = TextField()
