-- 将已有 kb_entries（单表 IVFFlat）迁移为 kb_anchors + 改造 kb_entries。
-- 在维护窗口执行；执行前备份数据库。

BEGIN;

CREATE TABLE IF NOT EXISTS kb_anchors (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    quant_key   VARCHAR(64)  NOT NULL UNIQUE,
    anchor_vec  vector(512)  NOT NULL,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_kb_anchors_vec ON kb_anchors
    USING ivfflat (anchor_vec vector_cosine_ops) WITH (lists = 50);

DROP INDEX IF EXISTS idx_kb_embedding;

ALTER TABLE kb_entries ADD COLUMN IF NOT EXISTS anchor_id BIGINT REFERENCES kb_anchors(id) ON DELETE RESTRICT;
ALTER TABLE kb_entries ADD COLUMN IF NOT EXISTS doc_id VARCHAR(128) NOT NULL DEFAULT 'legacy';
ALTER TABLE kb_entries ADD COLUMN IF NOT EXISTS page_index INTEGER NOT NULL DEFAULT 1;

CREATE INDEX IF NOT EXISTS idx_kb_anchor_id ON kb_entries (anchor_id);
CREATE INDEX IF NOT EXISTS idx_kb_doc_id ON kb_entries (doc_id);
CREATE INDEX IF NOT EXISTS idx_kb_doc_page ON kb_entries (doc_id, page_index);

-- 存量 embedding：每条暂挂独立锚点占位（上线后可通过后台批量重算量化锚点）
-- 此处仅保证结构可用；完整回填需运行应用内 ingest 或离线脚本。
UPDATE kb_entries SET doc_id = COALESCE(NULLIF(TRIM(doc_id), ''), 'legacy') WHERE doc_id IS NULL;

COMMIT;
