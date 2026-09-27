import pymysql
import pandas as pd

def executar_query(query, params=None, fetch=True):
    conexao = pymysql.connect(
        host='34.39.195.71',
        user='admin',
        password='Paulo@##2021',
        database='db_escola',
        charset='utf8mb4'
    )
    if fetch:
        df = pd.read_sql(query, conexao, params=params)
        conexao.close()
        return df
    else:
        cursor = conexao.cursor()
        cursor.execute(query, params or ())
        conexao.commit()
        cursor.close()
        conexao.close()
