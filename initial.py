import mysql.connector
import numpy as np

db = mysql.connector.connect(
  host="localhost",
  user="cxs",
  passwd="cxs1998mysqllib"
)
cursor = db.cursor()
cursor.execute("use lib")
for i in range(10):
    tmp = np.zeros(512)
    f_list = tmp.tolist()
    f_list = ','.join(str(e) for e in f_list)
    cursor.execute("insert into class values(%d, '%s')" % (i, f_list))