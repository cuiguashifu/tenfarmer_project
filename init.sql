CREATE DATABASE IF NOT EXISTS qintian_db;
USE qintian_db;

-- 1. 成员信息表
CREATE TABLE tb_member (
    member_id INT PRIMARY KEY AUTO_INCREMENT COMMENT '成员编号',
    name VARCHAR(50) NOT NULL COMMENT '姓名',
    role VARCHAR(50) COMMENT '角色/特长',
    avatar VARCHAR(255) COMMENT '头像路径',
    intro TEXT COMMENT '个人简介'
) COMMENT='成员信息表';

-- 2. 帮扶地信息表
CREATE TABLE tb_location (
    location_id INT PRIMARY KEY AUTO_INCREMENT COMMENT '帮扶地编号',
    location_name VARCHAR(100) NOT NULL COMMENT '地区名称',
    category VARCHAR(50) COMMENT '产品类别（水果/粮油/手作等，用于饼图）',
    description TEXT COMMENT '详细描述',
    before_image VARCHAR(255) COMMENT '帮扶前图片路径',
    after_image VARCHAR(255) COMMENT '帮扶后图片路径'
) COMMENT='帮扶地信息表';

-- 3. 助农事件表
CREATE TABLE tb_event (
    event_id INT PRIMARY KEY AUTO_INCREMENT COMMENT '事件编号',
    title VARCHAR(100) NOT NULL COMMENT '事件标题',
    event_date DATE NOT NULL COMMENT '发生日期（用于柱状图）',
    content TEXT COMMENT '事件详情',
    cover_image VARCHAR(255) COMMENT '封面图路径',
    location_id INT COMMENT '关联帮扶地编号',
    FOREIGN KEY (location_id) REFERENCES tb_location(location_id) ON DELETE SET NULL
) COMMENT='助农事件表';

-- 4. 帮扶地打卡表
CREATE TABLE tb_checkin (
    location_id INT PRIMARY KEY COMMENT '帮扶地编号（主键兼外键）',
    checkin_count INT DEFAULT 0 COMMENT '打卡次数',
    FOREIGN KEY (location_id) REFERENCES tb_location(location_id) ON DELETE CASCADE
) COMMENT='帮扶地打卡表';

-- 5. 相册信息表
CREATE TABLE tb_photo (
    photo_id INT PRIMARY KEY AUTO_INCREMENT COMMENT '相册编号',
    title VARCHAR(100) COMMENT '相册标题',
    image_path VARCHAR(255) NOT NULL COMMENT '图片路径',
    category VARCHAR(50) COMMENT '分类（名场面/助农现场/丰收实拍）',
    upload_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '上传时间'
) COMMENT='相册信息表';

-- 6. 留言信息表
CREATE TABLE tb_message (
    message_id INT PRIMARY KEY AUTO_INCREMENT COMMENT '留言编号',
    nickname VARCHAR(50) NOT NULL COMMENT '访客昵称',
    content VARCHAR(500) NOT NULL COMMENT '留言内容',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '留言时间'
) COMMENT='留言信息表';

-- 7. 公益周边信息表
CREATE TABLE tb_merchandise (
    merch_id INT PRIMARY KEY AUTO_INCREMENT COMMENT '周边编号',
    name VARCHAR(100) NOT NULL COMMENT '商品名称',
    description VARCHAR(255) COMMENT '描述',
    image_path VARCHAR(255) COMMENT '图片路径',
    official_link VARCHAR(255) COMMENT '官方渠道链接'
) COMMENT='公益周边信息表';

-- ================= 插入测试数据 =================
INSERT INTO tb_member (name, role, intro) VALUES ('蒋敦豪', '董事长', '十个勤天主理人');
INSERT INTO tb_member (name, role, intro) VALUES ('鹭卓', '种植组', '玫瑰王子');
INSERT INTO tb_location (location_name, category, description) VALUES ('后陡门', '蔬菜', '主要种植基地');
INSERT INTO tb_location (location_name, category, description) VALUES ('青海囊谦', '特产', '高原特色农产品');
INSERT INTO tb_checkin (location_id, checkin_count) VALUES (1, 50), (2, 30);

-- ================= 视图 =================
CREATE VIEW v_event_details AS
SELECT e.event_id, e.title AS event_title, e.event_date, l.location_name, l.category AS location_category, e.content, e.cover_image
FROM tb_event e LEFT JOIN tb_location l ON e.location_id = l.location_id;

CREATE VIEW v_checkin_rank AS
SELECT l.location_name, l.category, c.checkin_count
FROM tb_location l JOIN tb_checkin c ON l.location_id = c.location_id
ORDER BY c.checkin_count DESC;

-- ================= 存储过程 =================
DELIMITER //
CREATE PROCEDURE sp_add_checkin(IN p_location_id INT)
BEGIN
    UPDATE tb_checkin SET checkin_count = checkin_count + 1 WHERE location_id = p_location_id;
    IF ROW_COUNT() = 0 THEN
        INSERT INTO tb_checkin(location_id, checkin_count) VALUES (p_location_id, 1);
    END IF;
END //
DELIMITER ;

-- ================= 触发器 =================
DELIMITER //
CREATE TRIGGER trg_after_insert_message
AFTER INSERT ON tb_message
FOR EACH ROW
BEGIN
    UPDATE tb_checkin SET checkin_count = checkin_count + 1 WHERE location_id = 1;
END //
DELIMITER ;