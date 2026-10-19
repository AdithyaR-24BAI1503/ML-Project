from app.nlp import parse_command

def test_add_client():
    x = parse_command("add client Rahul, 9876543210, rahul@gmail.com")
    assert x.name == "ADD_CLIENT"
    assert x.name_arg == "Rahul"
    assert x.phone == "9876543210"
    assert x.email == "rahul@gmail.com"

def test_list_clients():
    assert parse_command("list clients").name == "LIST_CLIENTS"
    assert parse_command("show client list").name == "LIST_CLIENTS"

def test_update_client():
    x = parse_command("update client Rahul phone 9999999999")
    assert x.name == "UPDATE_CLIENT"
    assert x.field == "phone"
    assert x.value == "9999999999"

def test_delete_client():
    assert parse_command("delete client Rahul").name == "DELETE_CLIENT"
