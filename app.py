from flask import Flask, jsonify, request
from flask_cors import CORS
import mysql.connector
from math import sqrt
from sklearn import preprocessing
import numpy as np
import os
import cv2
from PIL import Image

threshold = 0.6 # decide whether matched

def distance(x, y):
    l = len(x)
    xs = 0
    ys = 0
    mul = 0
    for i in range(l):
        xs += x[i] ** 2
        ys += y[i] ** 2
        mul += x[i] * y[i]
    
    res = mul#res = mul/(sqrt(xs) * sqrt(ys))
    return res

db = mysql.connector.connect(
  host="localhost",
  user="cxs",
  passwd="cxs1998mysqllib"
)
cursor = db.cursor()
cursor.execute("use lib")
cursor.execute("create table if not exists class(id INT PRIMARY KEY, feature VARCHAR(30000))ENGINE=MyISAM")
cursor.execute("create table if not exists user_info(id INT PRIMARY KEY, usrId VARCHAR(20), name VARCHAR(255))ENGINE=MyISAM") # feature looks like '1,2,3,4'
cursor.execute("create table if not exists user_char(id INT PRIMARY KEY, feature VARCHAR(30000), user_info_id INT, class_id INT, FOREIGN KEY(class_id) REFERENCES class(id) ON DELETE SET NULL ON UPDATE SET NULL, FOREIGN KEY(user_info_id) REFERENCES user_info(id) ON DELETE SET NULL ON UPDATE SET NULL)ENGINE=MyISAM")
'''
cursor.execute("SELECT feature FROM stu")

myresult = cursor.fetchall()

print(myresult[0][0])
'''
app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

@app.route('/api/feature', methods=['GET'])
def data_pagination():
    db = mysql.connector.connect(
        host="localhost",
        user="cxs",
        passwd="cxs1998mysqllib"
    )
    cursor = db.cursor()
    cursor.execute("use lib")
    feature = request.args.get('feature')
    f_list = list(eval(feature))
    #f_list = preprocessing.normalize(f_list, norm='l2')

    cursor.execute("select id, feature from class")
    myresult = cursor.fetchall()
    d_min = 1e9
    nearest_id = -1
    for x in myresult:
        f_c_list = np.array(list(eval(x[1])))
        d_cur = distance(f_list, f_c_list)
        if d_cur < d_min:
            nearest_id = x[0]
            d_min = d_cur

    cursor.execute("select user_info_id, feature from user_char where class_id = %d" % (nearest_id))
    
    myresult = cursor.fetchall()
    d_min = 0.0
    i_cur = -1
    for i in myresult:
        f_i_list = np.array(list(eval(i[1])))
        d_cur = distance(f_list, f_i_list)
        
        if d_cur > threshold and d_cur > d_min:
            i_cur = i[0]
            d_min = d_cur
    
    if i_cur != -1:
        cursor.execute("select usrId, name from user_info where id = %d" % (i_cur))
        return_result = cursor.fetchone()
        return jsonify({
            'usrId' : return_result[0],
            'name' : return_result[1]
        })

    return jsonify({
        'usrId' : 'None',
        'name' : 'None'
    })

@app.route('/api/feature', methods=['POST'])
def data_insert():
    db = mysql.connector.connect(
        host="localhost",
        user="cxs",
        passwd="cxs1998mysqllib"
    )
    cursor = db.cursor()
    cursor.execute("use lib")
    stuId = request.form.get('usrId')
    stuName = request.form.get('name')
    feature = request.form.get('feature')
    f_list = list(eval(feature))
    #f_list = preprocessing.normalize(f_list, norm='l2')
    cursor.execute("select MAX(id) from user_info")
    
    idx = cursor.fetchone()[0] + 1

    sql = "insert into user_info values(%d, '%s', '%s')"
    
    print(cursor.rowcount, " record inserted.")
    
    cursor.execute("lock tables class write")
    cursor.execute("select id, feature from class")
    myresult = cursor.fetchall()
    d_min = 1e9
    nearest_id = -1
    for x in myresult:
        f_c_list = np.array(list(eval(x[1])))
        d_cur = distance(f_list, f_c_list)
        if d_cur < d_min:
            nearest_id = x[0]
            d_min = d_cur

    val = (idx, stuId, stuName)
    cursor.execute("lock tables user_info write")
    cursor.execute(sql % val)
    db.commit()
    cursor.execute("lock tables user_char write")
    cursor.execute("select MAX(id) from user_char")
    idx2 = cursor.fetchone()[0] + 1
    cursor.execute("insert into user_char values(%d, '%s', %d, %d)" % (idx2, feature, idx, nearest_id))

    cursor.execute("unlock tables")
    db.commit()

    return jsonify({
        'msg' : "ok"
    })

@app.route('/api/image', methods=['POST'])
def image_insert():
    stuId = request.form.get('usrId')
    image = request.form.get('image')
    image = list(eval(image))
    image = np.array(image).astype(np.uint8)
    dir_list = os.listdir('usr_image')
    if not stuId in dir_list:
        os.mkdir('usr_image/%s' % (stuId))
    im_list = os.listdir('usr_image/%s' % (stuId))
    l = len(im_list)
    im = Image.fromarray(image)
    im.save("usr_image/%s/%d.jpg" % (stuId, l))
    #cv2.imwrite("usr_image/%s/%d.jpg" % (stuId, l), cv2.UMat(image))

    return jsonify({
        'msg' : "ok"
    })

@app.route('/api/clear', methods=['POST'])
def delete_all():
    pd = request.form.get('pd')
    if pd != "admin_clear":
        return jsonify({
            'msg' : 'Wrong Password'
        })
    db = mysql.connector.connect(
        host="localhost",
        user="cxs",
        passwd="cxs1998mysqllib"
    )
    cursor = db.cursor()
    cursor.execute("use lib")
    cursor.execute("delete from user_char")
    cursor.execute("delete from user_info")
    db.commit()
    return jsonify({
        'msg' : 'Done'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4756)
