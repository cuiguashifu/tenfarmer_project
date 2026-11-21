import os
from werkzeug.utils import secure_filename
from flask import Flask, request, jsonify, json
from flask_cors import CORS
import pymysql

app = Flask(__name__)
CORS(app) # 允许前端跨域请求

def get_db():
    return pymysql.connect(
        host='127.0.0.1', 
        user='root', 
        password='123456', 
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

# 8. 用户注册接口
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"code": 400, "msg": "用户名或密码不能为空"})
        
    db = get_db()
    cursor = db.cursor()
    try:
        # 检查用户名是否已存在
        cursor.execute("SELECT * FROM tb_user WHERE username = %s", (username,))
        if cursor.fetchone():
            return jsonify({"code": 400, "msg": "该用户名已被注册"})
            
        # 插入新用户
        cursor.execute("INSERT INTO tb_user (username, password) VALUES (%s, %s)", (username, password))
        db.commit()
        return jsonify({"code": 200, "msg": "注册成功，快去登录吧！"})
    except Exception as e:
        db.rollback()
        return jsonify({"code": 500, "msg": "注册失败", "error": str(e)})
    finally:
        db.close()

# 9. 用户登录接口（简易版）
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM tb_user WHERE username = %s AND password = %s", (username, password))
    user = cursor.fetchone()
    db.close()
    
    if user:
        return jsonify({"code": 200, "msg": "登录成功", "username": user['username']})
    else:
        return jsonify({"code": 400, "msg": "用户名或密码错误"})

# 10. 获取单个成员详情接口
@app.route('/api/member/<int:member_id>', methods=['GET'])
def get_member_detail(member_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM tb_member WHERE member_id = %s", (member_id,))
    res = cursor.fetchone()
    db.close()
    return jsonify(res)

# 11. 发布成长记录接口
@app.route('/api/add_post', methods=['POST'])
def add_post():
    data = request.json
    nickname = data.get('nickname')
    content = data.get('content')
    
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("INSERT INTO tb_message (nickname, content) VALUES (%s, %s)", (nickname, content))
        db.commit()
        return jsonify({"code": 200, "msg": "发布成功"})
    except Exception as e:
        db.rollback()
        return jsonify({"code": 500, "msg": "发布失败", "error": str(e)})
    finally:
        db.close()

# 12. 获取所有成长记录接口
@app.route('/api/get_posts', methods=['GET'])
def get_posts():
    db = get_db()
    cursor = db.cursor()
    # 按时间倒序排列（最新的在最上面）
    cursor.execute("SELECT * FROM tb_message ORDER BY create_time DESC")
    res = cursor.fetchall()
    db.close()
    return jsonify(res)

# 13. 上传照片接口
@app.route('/api/upload_photo', methods=['POST'])
def upload_photo():
    # 获取上传的文件和自定义名称
    file = request.files.get('photo')
    title = request.form.get('title')
    uploader = request.form.get('uploader', '匿名用户')

    if not file or not title:
        return jsonify({"code": 400, "msg": "图片和名称不能为空"})

    # 防止文件名冲突，用时间戳重命名
    import time
    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'jpg'
    filename = f"photo_{int(time.time())}.{ext}"
    
    # 确保目录存在并保存文件
    upload_dir = os.path.join(os.getcwd(), 'static', 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    file.save(os.path.join(upload_dir, filename))

    # 存入数据库
    db = get_db()
    cursor = db.cursor()
    try:
        # image_path 存相对路径，前端可以通过 http://127.0.0.1:5000/static/uploads/... 访问
        img_path = f"/static/uploads/{filename}"
        cursor.execute("INSERT INTO tb_photo (title, image_path, category) VALUES (%s, %s, %s)", 
                       (title, img_path, f"由{uploader}上传"))
        db.commit()
        return jsonify({"code": 200, "msg": "上传成功！"})
    except Exception as e:
        db.rollback()
        return jsonify({"code": 500, "msg": "数据库写入失败", "error": str(e)})
    finally:
        db.close()

# 14. 获取所有照片接口
@app.route('/api/get_photos', methods=['GET'])
def get_photos_from_db():
    db = get_db()
    cursor = db.cursor()
    # 按上传时间倒序
    cursor.execute("SELECT * FROM tb_photo ORDER BY upload_time DESC")
    res = cursor.fetchall()
    db.close()
    return jsonify(res)

# 1. 获取所有活动接口
@app.route('/api/get_activities', methods=['GET'])
def get_activities():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM tb_activity ORDER BY start_date ASC")
    rows = cursor.fetchall()
    db.close()
    
    # 处理日期格式，防止前端解析报错 (datatime.date 转 string)
    result = []
    for row in rows:
        row['start_date'] = row['start_date'].strftime('%Y-%m-%d') if row['start_date'] else None
        row['end_date'] = row['end_date'].strftime('%Y-%m-%d') if row['end_date'] else None
        result.append(row)
        
    return jsonify(result)

# 2. 发布新活动接口
@app.route('/api/add_activity', methods=['POST'])
def add_activity():
    data = request.get_json()
    title = data.get('title')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    content = data.get('content')
    color = data.get('color')
    username = data.get('username')

    if not title or not start_date:
        return jsonify({"code": 400, "msg": "参数不完整"})

    try:
        db = get_db()
        cursor = db.cursor()
        sql = """INSERT INTO tb_activity (title, start_date, end_date, content, color, username) 
                 VALUES (%s, %s, %s, %s, %s, %s)"""
        cursor.execute(sql, (title, start_date, end_date if end_date else None, content, color, username))
        db.commit()
        db.close()
        return jsonify({"code": 200, "msg": "活动添加成功"})
    except Exception as e:
        print("数据库报错:", e)
        return jsonify({"code": 500, "msg": str(e)})

# 3. 删除活动接口
@app.route('/api/delete_activity', methods=['POST'])
def delete_activity():
    data = request.get_json()
    activity_id = data.get('id')

    if not activity_id:
        return jsonify({"code": 400, "msg": "缺少活动 ID"})

    try:
        db = get_db()
        cursor = db.cursor()
        # 执行删除
        sql = "DELETE FROM tb_activity WHERE id = %s"
        cursor.execute(sql, (activity_id,))
        db.commit()
        
        # 检查是否真的删除了数据
        if cursor.rowcount > 0:
            result = {"code": 200, "msg": "删除成功"}
        else:
            result = {"code": 404, "msg": "找不到该活动，可能已被删除"}
            
        db.close()
        return jsonify(result)
    except Exception as e:
        print("数据库报错:", e)
        return jsonify({"code": 500, "msg": str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5000)