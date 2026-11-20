from flask import Flask, request, jsonify
from flask_cors import CORS
import pymysql

app = Flask(__name__)
CORS(app) # 允许前端跨域请求

def get_db():
    return pymysql.connect(
        host='127.0.0.1', 
        user='root', 
        password='123456',  # <--- 改这里！！！
        database='qintian_db', 
        cursorclass=pymysql.cursors.DictCursor
    )

# 1. 获取成员
@app.route('/api/members', methods=['GET'])
def get_members():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM tb_member")
    res = cursor.fetchall()
    db.close()
    return jsonify(res)

# 2. 获取打卡排行榜数据
@app.route('/api/locations', methods=['GET'])
def get_locations():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM v_checkin_rank")
    res = cursor.fetchall()
    db.close()
    return jsonify(res)

# 3. 打卡接口（调用存储过程）
@app.route('/api/checkin/<int:location_id>', methods=['POST'])
def checkin(location_id):
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.callproc('sp_add_checkin', (location_id,))
        db.commit()
        return jsonify({"msg": "打卡成功！"})
    except Exception as e:
        db.rollback()
        return jsonify({"msg": "打卡失败", "error": str(e)})
    finally:
        db.close()

# 4. 留言接口（触发触发器）
@app.route('/api/message', methods=['POST'])
def add_message():
    data = request.json
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("INSERT INTO tb_message(nickname, content) VALUES (%s, %s)", (data['nickname'], data['content']))
        db.commit()
        return jsonify({"msg": "留言成功！(打卡数增加了哦)"})
    except Exception as e:
        db.rollback()
        return jsonify({"msg": "留言失败", "error": str(e)})
    finally:
        db.close()

# 5. 获取助农事件（调用视图）
@app.route('/api/events', methods=['GET'])
def get_events():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM v_event_details")
    res = cursor.fetchall()
    db.close()
    return jsonify(res)

# 6. 获取相册
@app.route('/api/photos', methods=['GET'])
def get_photos():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM tb_photo")
    res = cursor.fetchall()
    db.close()
    return jsonify(res)

# 7. 获取周边
@app.route('/api/merch', methods=['GET'])
def get_merch():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM tb_merchandise")
    res = cursor.fetchall()
    db.close()
    return jsonify(res)

if __name__ == '__main__':
    app.run(debug=True, port=5000)