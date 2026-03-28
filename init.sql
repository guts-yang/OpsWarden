-- OpsWarden 数据库初始化脚本

CREATE DATABASE IF NOT EXISTS opswarden
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE opswarden;

-- ==========================================
-- OPS-7: 运维账号表
-- ==========================================
CREATE TABLE IF NOT EXISTS accounts (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    employee_id     VARCHAR(32)  NOT NULL UNIQUE COMMENT '工号',
    username        VARCHAR(64)  NOT NULL UNIQUE COMMENT '登录用户名',
    password_hash   VARCHAR(256) NOT NULL COMMENT '密码哈希',
    name            VARCHAR(64)  NOT NULL COMMENT '姓名',
    department      VARCHAR(128) DEFAULT NULL COMMENT '部门',
    email           VARCHAR(128) DEFAULT NULL COMMENT '邮箱',
    phone           VARCHAR(20)  DEFAULT NULL COMMENT '手机号',
    role            ENUM('admin', 'operator', 'user') NOT NULL DEFAULT 'user' COMMENT '角色',
    status          ENUM('active', 'frozen') NOT NULL DEFAULT 'active' COMMENT '状态',
    last_login_at   DATETIME     DEFAULT NULL COMMENT '最后登录时间',
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    INDEX idx_employee_id (employee_id),
    INDEX idx_name (name),
    INDEX idx_department (department),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='运维账号表';

-- ==========================================
-- OPS-13: 工单表（提前建好，后面直接用）
-- ==========================================
CREATE TABLE IF NOT EXISTS tickets (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    ticket_no       VARCHAR(32)  NOT NULL UNIQUE COMMENT '工单编号',
    title           VARCHAR(256) NOT NULL COMMENT '工单标题',
    description     TEXT         COMMENT '问题详细描述',
    source          ENUM('ai_auto', 'manual', 'feishu') NOT NULL DEFAULT 'ai_auto' COMMENT '来源',
    status          ENUM('pending', 'processing', 'resolved', 'closed') NOT NULL DEFAULT 'pending' COMMENT '状态',
    priority        ENUM('low', 'medium', 'high', 'urgent') NOT NULL DEFAULT 'medium' COMMENT '优先级',
    reporter_id     BIGINT       DEFAULT NULL COMMENT '报障人ID',
    reporter_name   VARCHAR(64)  DEFAULT NULL COMMENT '报障人姓名',
    assignee_id     BIGINT       DEFAULT NULL COMMENT '处理人ID',
    solution        TEXT         DEFAULT NULL COMMENT '解决方案',
    is_written_back TINYINT(1)   NOT NULL DEFAULT 0 COMMENT '是否已回写知识库',
    callback_note   TEXT         DEFAULT NULL COMMENT '回访备注',
    callback_at     DATETIME     DEFAULT NULL COMMENT '回访时间',
    resolved_at     DATETIME     DEFAULT NULL COMMENT '解决时间',
    closed_at       DATETIME     DEFAULT NULL COMMENT '关闭时间',
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_ticket_no (ticket_no),
    INDEX idx_status (status),
    INDEX idx_assignee (assignee_id),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='运维工单表';

CREATE TABLE IF NOT EXISTS ticket_logs (
    id            BIGINT AUTO_INCREMENT PRIMARY KEY,
    ticket_id     BIGINT       NOT NULL COMMENT '关联工单ID',
    action        VARCHAR(64)  NOT NULL COMMENT '操作类型',
    operator_id   BIGINT       DEFAULT NULL COMMENT '操作人ID',
    operator_name VARCHAR(64)  DEFAULT NULL COMMENT '操作人姓名',
    content       TEXT         DEFAULT NULL COMMENT '操作内容',
    created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_ticket_id (ticket_id),
    FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工单操作日志表';

-- 插入默认管理员（密码: admin123 的bcrypt哈希）
INSERT INTO accounts (employee_id, username, password_hash, name, department, role, status)
VALUES ('ADMIN001', 'admin', '$2b$12$LJ3m4ys3GZ8bPqdFJH4wXOYFnLBsRlAhK7Jk6VBv8H9zK5m7K2f6i', '系统管理员', '运维管理部', 'admin', 'active');

GRANT ALL PRIVILEGES ON opswarden.* TO 'ops'@'%';
FLUSH PRIVILEGES;