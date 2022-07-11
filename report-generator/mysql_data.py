from mysql.connector import connect
import pandas as pd


def get_connection():
    connection = connect(user="qe-all", password="primordialFish", database="test-results", host="localhost", port=3306)
    if connection is None:
        print("Error while trying to connect")
        return
    return connection


def get_stuff(connection):
    cursor = connection.cursor()
    max_price = 22
    cursor.execute("SELECT * FROM customers where price > %s", (max_price,))
    result = cursor.fetchall()
    for x in result:
        print(x)
    cursor.close()


def get_sdk_data():
    conn = get_connection()
    sdk_data = get_sdk_size(conn)
    conn.close()


def get_sdk_size():
    connection = get_connection()
    query = """select tr.id as id,
        started,
        attr2 as version,
        label1 as measurement,
        value
from test_run as tr inner join measurement as m on tr.id = m.test_run_id
where name = 'size'
and type = 'sdk'
and attr1= 'python'"""
    cursor = connection.cursor()
    cursor.execute(query)
    ret_val = pd.DataFrame(cursor.fetchall())
    ret_val.columns = [d[0] for d in cursor.description]
    cursor.close()
    connection.close()

    return ret_val


def get_sdk_size_old(connection):
    query = """
        select tr.id as id,
        started,
        attr2 as version,
        max((case
                when (label1 = 'full')
                    then value
                else 0 end))  AS full,
       max((case
                when (label1 = 'min')
                    then value
                else 0 end))  AS min
from test_run as tr inner join measurement as m on tr.id = m.test_run_id
where name = 'size'
and type = 'sdk'
and attr1= 'python'
group by id, started,  version
"""
    cursor = connection.cursor()
    cursor.execute(query)
    ret_val = pd.DataFrame(cursor.fetchall())
    ret_val.columns = [d[0] for d in cursor.description]
    cursor.close()

    return ret_val
