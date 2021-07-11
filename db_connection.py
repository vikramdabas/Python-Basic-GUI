import psycopg2
import yaml
try:
    with open("data/config.yaml") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
except:
    print("Config File Not Found.")

db_name = config["db"]["db_name"]
db_port = config["db"]["port"]
user = config["db"]["user"]
host_name = config["db"]["host_name"]
passw = "Test"


def db_conn(command, cmd_type):
    record = None
    connection = None
    cursor = None
    try:
        connection = psycopg2.connect(host=host_name, port=db_port, database=db_name, user=user, password=passw)
        cursor = connection.cursor()
        cursor.execute(command)
        if cmd_type == "fetch":
            record = cursor.fetchall()
        elif cmd_type == "insert":
            connection.commit()
            record = cursor.rowcount
        else:
            pass
    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL, ", error)
        if cmd_type == "insert":
            connection.rollback()
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()
    return record


comm = "SELECT * FROM TABLE_NAME;"
result = db_conn(comm, "FETCH")
print(result)

comm_2 = "INSERT INTO TABLE_NAME ('NAME') VALUES ('ABCD');"
result = db_conn(comm_2, "INSERT")
print(result)
