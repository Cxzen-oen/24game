-- 账号体系与排行榜资格
--
-- 设计要点：
-- 1) 游客（guest_id）继续可玩，但只有 account_id 不为空的成绩进入排行榜；
-- 2) 账号与游客二选一拥有对局/成绩，登录后可把本机游客数据并入账号；
-- 3) 排行榜不单独建表，直接由 personal_bests 派生，避免两份最佳成绩不一致。

CREATE TABLE accounts (
    id             uuid PRIMARY KEY,
    username       text        NOT NULL,
    nickname       text        NOT NULL,
    password_hash  text        NOT NULL,
    status         text        NOT NULL DEFAULT 'ACTIVE',
    token_version  integer     NOT NULL DEFAULT 0,
    created_at     timestamptz NOT NULL DEFAULT now(),
    updated_at     timestamptz NOT NULL DEFAULT now(),
    last_login_at  timestamptz,
    CONSTRAINT ck_accounts_status CHECK (status IN ('ACTIVE', 'BANNED')),
    CONSTRAINT ck_accounts_username CHECK (username ~ '^[a-z][a-z0-9_]{3,19}$'),
    CONSTRAINT ck_accounts_nickname CHECK (char_length(nickname) BETWEEN 2 AND 12),
    CONSTRAINT ck_accounts_token_version CHECK (token_version >= 0)
);

CREATE UNIQUE INDEX uq_accounts_username ON accounts (username);

COMMENT ON TABLE accounts IS '账号；username 存小写，展示用 nickname';
COMMENT ON COLUMN accounts.token_version IS '令牌版本，改密/封禁时 +1 可使已签发 JWT 立即失效';

-- 刷新令牌只存 SHA-256，不落明文；旋转后旧记录保留用于检测重放
CREATE TABLE refresh_tokens (
    id          uuid PRIMARY KEY,
    account_id  uuid        NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    token_hash  char(64)    NOT NULL,
    issued_at   timestamptz NOT NULL,
    expires_at  timestamptz NOT NULL,
    revoked_at  timestamptz,
    replaced_by uuid,
    user_agent  text,
    ip          text,
    CONSTRAINT uq_refresh_token_hash UNIQUE (token_hash)
);

CREATE INDEX idx_refresh_account ON refresh_tokens (account_id, issued_at DESC);

-- 对局归属：account_id 优先；游客局在登录后接入账号
ALTER TABLE games ADD COLUMN account_id uuid REFERENCES accounts(id) ON DELETE CASCADE;
ALTER TABLE games ALTER COLUMN guest_id DROP NOT NULL;
ALTER TABLE games ADD CONSTRAINT ck_games_owner CHECK (account_id IS NOT NULL OR guest_id IS NOT NULL);
CREATE INDEX idx_games_account ON games (account_id, started_at DESC);
-- 账号局的 requestId 幂等；(guest_id, request_id) 对 NULL 不去重，需要单独约束
CREATE UNIQUE INDEX uq_games_account_request ON games (account_id, request_id) WHERE account_id IS NOT NULL;

ALTER TABLE game_results ADD COLUMN account_id uuid REFERENCES accounts(id) ON DELETE CASCADE;
ALTER TABLE game_results ALTER COLUMN guest_id DROP NOT NULL;
ALTER TABLE game_results ADD CONSTRAINT ck_results_owner CHECK (account_id IS NOT NULL OR guest_id IS NOT NULL);
CREATE INDEX idx_results_account ON game_results (account_id, finished_at DESC);

ALTER TABLE personal_bests ADD COLUMN account_id uuid REFERENCES accounts(id) ON DELETE CASCADE;
ALTER TABLE personal_bests ALTER COLUMN guest_id DROP NOT NULL;
ALTER TABLE personal_bests ADD CONSTRAINT ck_best_owner
    CHECK ((account_id IS NULL) <> (guest_id IS NULL));

-- 每个账号每个「模式 × 难度」只有一条最佳
CREATE UNIQUE INDEX uq_best_account_mode_level
    ON personal_bests (account_id, mode, level)
    WHERE account_id IS NOT NULL;

-- 排行榜读取路径：A 榜按答对数降序、计榜用时升序；B 榜按计榜用时升序
CREATE INDEX idx_best_board_a
    ON personal_bests (mode, level, best_correct DESC, best_scoring_ms ASC, achieved_at ASC)
    WHERE account_id IS NOT NULL;

CREATE INDEX idx_best_board_b
    ON personal_bests (mode, level, best_scoring_ms ASC, achieved_at ASC)
    WHERE account_id IS NOT NULL;