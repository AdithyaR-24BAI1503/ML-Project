from app.nlp import parse_command

def test_add():
    x = parse_command("add client Rahul, 9876543210, rahul@gmail.com")
    assert x.name == "ADD_CLIENT"
    assert x.name_arg == "Rahul"

def test_list():
    assert parse_command("list clients").name == "LIST_CLIENTS"

def test_update():
    x = parse_command("update client Rahul phone 9999999999")
    assert x.name == "UPDATE_CLIENT"
    assert x.field == "phone"

def test_delete():
    assert parse_command("delete client Rahul").name == "DELETE_CLIENT"
