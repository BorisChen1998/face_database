import mysql.connector
from sklearn.cluster import KMeans
import numpy as np

K = 10

db = mysql.connector.connect(
  host="localhost",
  user="cxs",
  passwd="cxs1998mysqllib"
)
cursor = db.cursor()
cursor.execute("use lib")

def main():
    ids = []
    X = []
    cursor.execute("lock tables class write")
    cursor.execute("delete from class")
    db.commit()

    cursor.execute("lock tables user_char write")
    cursor.execute("select id, feature from user_char")
    result = cursor.fetchall()
    for x in result:
        ids.append(x[0])
        X.append(list(eval(x[1])))
    X_arr = np.array(X)
    kmeans = KMeans(n_clusters=K, random_state=0).fit(X_arr)

    ls = [[] for i in range(K)]

    for i in range(X_arr.shape[0]):
        ls[kmeans.labels_[i]].append(ids[i])

    for i in range(K):
        f_list = kmeans.cluster_centers_[i]
        f_list = ','.join(str(i) for i in f_list)
        id_list = ls[i]
        
        cursor.execute("lock tables class write")
        sql = "insert into class values(%d, '%s')" % (i, f_list)
        cursor.execute(sql)
        db.commit()
        cursor.execute("lock tables user_char write")
        sql = "update user_char set class_id = %d where id = %d"
        for l in id_list:
            cursor.execute(sql % (i, l))
            db.commit()

    cursor.execute("unlock tables")
    db.commit()

if __name__ == '__main__':
    main()
