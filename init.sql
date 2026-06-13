-- OpsWarden 数据库初始化脚本 (PostgreSQL)

CREATE EXTENSION IF NOT EXISTS vector;

-- ==========================================
-- ENUM 类型定义
-- ==========================================
DO $$ BEGIN
    CREATE TYPE account_role   AS ENUM ('admin', 'operator', 'user');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE account_status AS ENUM ('active', 'frozen');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE ticket_source  AS ENUM ('ai_auto', 'manual');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE ticket_status  AS ENUM ('pending', 'processing', 'resolved', 'closed');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE ticket_priority AS ENUM ('low', 'medium', 'high', 'urgent');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE kb_source AS ENUM ('manual', 'ticket_writeback');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- ==========================================
-- 运维账号表
-- ==========================================
CREATE TABLE IF NOT EXISTS accounts (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    employee_id     VARCHAR(32)      NOT NULL UNIQUE,
    username        VARCHAR(64)      NOT NULL UNIQUE,
    password_hash   VARCHAR(256)     NOT NULL,
    name            VARCHAR(64)      NOT NULL,
    department      VARCHAR(128),
    email           VARCHAR(128),
    phone           VARCHAR(20),
    role            account_role     NOT NULL DEFAULT 'user',
    status          account_status   NOT NULL DEFAULT 'active',
    last_login_at   TIMESTAMPTZ,
    created_at      TIMESTAMPTZ      NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ      NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_accounts_employee_id  ON accounts (employee_id);
CREATE INDEX IF NOT EXISTS idx_accounts_name         ON accounts (name);
CREATE INDEX IF NOT EXISTS idx_accounts_department   ON accounts (department);
CREATE INDEX IF NOT EXISTS idx_accounts_status       ON accounts (status);

-- ==========================================
-- 运维工单表
-- ==========================================
CREATE TABLE IF NOT EXISTS tickets (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ticket_no       VARCHAR(32)      NOT NULL UNIQUE,
    title           VARCHAR(256)     NOT NULL,
    description     TEXT,
    source          ticket_source    NOT NULL DEFAULT 'ai_auto',
    status          ticket_status    NOT NULL DEFAULT 'pending',
    priority        ticket_priority  NOT NULL DEFAULT 'medium',
    reporter_id     BIGINT,
    reporter_name   VARCHAR(64),
    assignee_id     BIGINT,
    solution        TEXT,
    is_written_back BOOLEAN          NOT NULL DEFAULT FALSE,
    callback_note   TEXT,
    callback_at     TIMESTAMPTZ,
    resolved_at     TIMESTAMPTZ,
    closed_at       TIMESTAMPTZ,
    created_at      TIMESTAMPTZ      NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ      NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tickets_ticket_no ON tickets (ticket_no);
CREATE INDEX IF NOT EXISTS idx_tickets_status    ON tickets (status);
CREATE INDEX IF NOT EXISTS idx_tickets_assignee  ON tickets (assignee_id);
CREATE INDEX IF NOT EXISTS idx_tickets_created   ON tickets (created_at);

-- ==========================================
-- 工单操作日志表
-- ==========================================
CREATE TABLE IF NOT EXISTS ticket_logs (
    id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ticket_id     BIGINT       NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    action        VARCHAR(64)  NOT NULL,
    operator_id   BIGINT,
    operator_name VARCHAR(64),
    content       TEXT,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ticket_logs_ticket_id ON ticket_logs (ticket_id);

-- ==========================================
-- 知识库：量化锚点（L1，仅此表建向量 ANN 索引）
-- ==========================================
CREATE TABLE IF NOT EXISTS kb_anchors (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    quant_key   VARCHAR(64)  NOT NULL UNIQUE,
    anchor_vec  vector(512)  NOT NULL,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_kb_anchors_vec ON kb_anchors
    USING ivfflat (anchor_vec vector_cosine_ops) WITH (lists = 50);

-- ==========================================
-- 知识库条目（L2：页级索引，embedding 仅用于候选集内精排，无向量索引）
-- ==========================================
CREATE TABLE IF NOT EXISTS kb_entries (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    category    VARCHAR(64)  NOT NULL,
    question    TEXT         NOT NULL,
    solution    TEXT         NOT NULL,
    tags        VARCHAR(256),
    source      kb_source    NOT NULL DEFAULT 'manual',
    match_score FLOAT        NOT NULL DEFAULT 0.8,
    anchor_id   BIGINT       REFERENCES kb_anchors(id) ON DELETE RESTRICT,
    doc_id      VARCHAR(128) NOT NULL DEFAULT 'legacy',
    page_index  INTEGER      NOT NULL DEFAULT 1,
    embedding   vector(512),
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_kb_category ON kb_entries (category);
CREATE INDEX IF NOT EXISTS idx_kb_source   ON kb_entries (source);
CREATE INDEX IF NOT EXISTS idx_kb_anchor_id ON kb_entries (anchor_id);
CREATE INDEX IF NOT EXISTS idx_kb_doc_id ON kb_entries (doc_id);
CREATE INDEX IF NOT EXISTS idx_kb_doc_page ON kb_entries (doc_id, page_index);

-- ==========================================
-- 默认管理员账号（密码: 请通过 bcrypt 生成后替换）
-- ==========================================
INSERT INTO accounts (employee_id, username, password_hash, name, department, role, status)
VALUES ('ADMIN001', 'admin', '$2b$12$YOUR_BCRYPT_HASH_REPLACE_ME', '系统管理员', 'general', 'admin', 'active')
ON CONFLICT (username) DO NOTHING;

-- ==========================================
-- Agent audit tables
-- ==========================================
CREATE TABLE IF NOT EXISTS agent_runs (
    id             BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    thread_id      VARCHAR(160) NOT NULL,
    user_id        BIGINT,
    query          TEXT NOT NULL,
    final_answer   TEXT,
    stop_reason    VARCHAR(64),
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agent_runs_thread_id ON agent_runs (thread_id);
CREATE INDEX IF NOT EXISTS idx_agent_runs_user_id   ON agent_runs (user_id);

CREATE TABLE IF NOT EXISTS agent_tool_calls (
    id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id        BIGINT REFERENCES agent_runs(id) ON DELETE CASCADE,
    tool_name     VARCHAR(64) NOT NULL,
    args_json     JSONB,
    result_json   JSONB,
    latency_ms    INTEGER,
    success       BOOLEAN NOT NULL DEFAULT FALSE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agent_tool_calls_run_id ON agent_tool_calls (run_id);
