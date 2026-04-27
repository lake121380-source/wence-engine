"""一次性数据库迁移脚本：补齐新增字段和新建表"""
import os
import sqlite3

# 固定指向 backend 目录下数据库，避免受执行 cwd 影响打到错误库
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'content_studio.db')
print('using sqlite db:', db_path)
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# ── 1. creator_videos 补字段 ─────────────────────────────
cur.execute('PRAGMA table_info(creator_videos)')
existing_cols = [row[1] for row in cur.fetchall()]
print('creator_videos 现有字段:', existing_cols)

new_cols = [
    ('collect_count',      'INTEGER DEFAULT 0'),
    ('like_play_ratio',    'FLOAT'),
    ('comment_play_ratio', 'FLOAT'),
    ('collect_play_ratio', 'FLOAT'),
    ('script',             'TEXT'),
    ('top_comments',       'TEXT'),
    ('video_url',          'VARCHAR(500)'),
]
for col, col_type in new_cols:
    if col not in existing_cols:
        cur.execute(f'ALTER TABLE creator_videos ADD COLUMN {col} {col_type}')
        print(f'  ✅ Added: creator_videos.{col}')
    else:
        print(f'  ⏭  Already exists: creator_videos.{col}')

# ── 2. creator_intel_cards 表 ────────────────────────────
cur.execute('''
CREATE TABLE IF NOT EXISTS creator_intel_cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    creator_id INTEGER NOT NULL UNIQUE,
    positioning TEXT,
    video_style TEXT,
    common_topics TEXT,
    comment_pain_points TEXT,
    summary TEXT,
    raw_analysis TEXT,
    created_at DATETIME,
    updated_at DATETIME,
    FOREIGN KEY (creator_id) REFERENCES creators(id)
)
''')
print('✅ creator_intel_cards table ready')

# ── 3. operator_viewpoints 表 ────────────────────────────
cur.execute('''
CREATE TABLE IF NOT EXISTS operator_viewpoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    category TEXT,
    content TEXT NOT NULL,
    tags TEXT,
    is_active INTEGER DEFAULT 1,
    indexed INTEGER DEFAULT 0,
    created_at DATETIME,
    updated_at DATETIME
)
''')
print('✅ operator_viewpoints table ready')

# ── 4. video_analyses 表 ─────────────────────────────────
cur.execute('''
CREATE TABLE IF NOT EXISTS video_analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id INTEGER,
    topic_id INTEGER,
    like_play_ratio FLOAT,
    comment_play_ratio FLOAT,
    collect_play_ratio FLOAT,
    like_play_level TEXT,
    comment_play_level TEXT,
    collect_play_level TEXT,
    resonance_analysis TEXT,
    discussion_analysis TEXT,
    value_analysis TEXT,
    why_viral_summary TEXT,
    raw_data TEXT,
    created_at DATETIME,
    updated_at DATETIME,
    FOREIGN KEY (video_id) REFERENCES creator_videos(id),
    FOREIGN KEY (topic_id) REFERENCES topics(id)
)
''')
print('✅ video_analyses table ready')

# ── 5. operator_viewpoints 补 tenant_id ─────────────────────────
cur.execute('PRAGMA table_info(operator_viewpoints)')
existing_cols = [row[1] for row in cur.fetchall()]
if 'tenant_id' not in existing_cols:
    cur.execute('ALTER TABLE operator_viewpoints ADD COLUMN tenant_id INTEGER REFERENCES tenants(id)')
    print('  ✅ Added: operator_viewpoints.tenant_id')
else:
    print('  ⏭  Already exists: operator_viewpoints.tenant_id')

# ── 6. style_templates 补 content_type ──────────────────────────
cur.execute('PRAGMA table_info(style_templates)')
existing_cols = [row[1] for row in cur.fetchall()]
if 'content_type' not in existing_cols:
    cur.execute('ALTER TABLE style_templates ADD COLUMN content_type VARCHAR(50)')
    print('  ✅ Added: style_templates.content_type')
else:
    print('  ⏭  Already exists: style_templates.content_type')

conn.commit()

# ── 7. creator_intel_cards 补字段（tenant_id + 情报卡新字段）────
cur.execute('PRAGMA table_info(creator_intel_cards)')
existing_cols = [row[1] for row in cur.fetchall()]
intel_new_cols = [
    ('tenant_id',    'INTEGER REFERENCES tenants(id)'),
    ('viral_formula','TEXT'),
    ('strengths',    'TEXT'),
    ('weaknesses',   'TEXT'),
]
for col, col_type in intel_new_cols:
    if col not in existing_cols:
        cur.execute(f'ALTER TABLE creator_intel_cards ADD COLUMN {col} {col_type}')
        print(f'  ✅ Added: creator_intel_cards.{col}')
    else:
        print(f'  ⏭  Already exists: creator_intel_cards.{col}')

# ── 8. generations 补结构化调试字段 ──────────────────────
cur.execute('PRAGMA table_info(generations)')
existing_cols = [row[1] for row in cur.fetchall()]
generation_new_cols = [
    ('debug_info', 'TEXT'),
    ('mode_branch', 'VARCHAR(32)'),
    ('temperature_used', 'FLOAT'),
    ('doc_chars_injected', 'INTEGER DEFAULT 0'),
    ('viral_chars_injected', 'INTEGER DEFAULT 0'),
]
for col, col_type in generation_new_cols:
    if col not in existing_cols:
        cur.execute(f'ALTER TABLE generations ADD COLUMN {col} {col_type}')
        print(f'  ✅ Added: generations.{col}')
    else:
        print(f'  ⏭  Already exists: generations.{col}')

conn.commit()
conn.close()
print('\nMigration complete! ✅')
