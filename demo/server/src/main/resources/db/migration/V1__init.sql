-- 初始结构：对局、题目、幂等动作、成绩、最佳
CREATE TYPE game_mode AS ENUM ('A', 'B');
CREATE TYPE game_level AS ENUM ('L1', 'L2');
CREATE TYPE game_status AS ENUM ('RUNNING', 'FINISHED', 'ABANDONED');

CREATE TABLE games (
    id                uuid PRIMARY KEY,
    guest_id          text        NOT NULL,
    request_id        text        NOT NULL,
    mode              game_mode   NOT NULL,
    level             game_level  NOT NULL,
    status            game_status NOT NULL DEFAULT 'RUNNING',
    started_at        timestamptz NOT NULL,
    deadline_at       timestamptz,
    correct_count     integer     NOT NULL DEFAULT 0 CHECK (correct_count >= 0),
    wrong_count       integer     NOT NULL DEFAULT 0 CHECK (wrong_count >= 0),
    skipped_count     integer     NOT NULL DEFAULT 0 CHECK (skipped_count >= 0),
    penalty_ms        bigint      NOT NULL DEFAULT 0 CHECK (penalty_ms >= 0),
    last_scoring_ms   bigint               CHECK (last_scoring_ms IS NULL OR last_scoring_ms >= 0),
    deck              jsonb       NOT NULL,
    deck_position     integer     NOT NULL DEFAULT 0 CHECK (deck_position >= 0),
    revision          bigint      NOT NULL DEFAULT 0,
    finished_at       timestamptz,
    CONSTRAINT uq_games_guest_request UNIQUE (guest_id, request_id),
    CONSTRAINT ck_games_deck_position CHECK (jsonb_array_length(deck) = 0 OR deck_position <= jsonb_array_length(deck)),
    CONSTRAINT ck_games_finished CHECK ((status = 'RUNNING' AND finished_at IS NULL) OR (status <> 'RUNNING' AND finished_at IS NOT NULL))
);

CREATE TABLE game_puzzles (
    id            uuid PRIMARY KEY,
    game_id       uuid        NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    sequence_no   integer     NOT NULL,
    puzzle_key    text        NOT NULL,
    numbers_json  jsonb       NOT NULL,
    status        text        NOT NULL DEFAULT 'OPEN',
    created_at    timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_puzzle_game_seq UNIQUE (game_id, sequence_no)
);

CREATE TABLE game_actions (
    id                  bigserial PRIMARY KEY,
    game_id             uuid        NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    action_id           text        NOT NULL,
    action_type         text        NOT NULL,
    request_fingerprint text        NOT NULL,
    response_jsonb      jsonb       NOT NULL,
    created_at          timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_action_game_action UNIQUE (game_id, action_id)
);

CREATE TABLE game_results (
    result_id       uuid PRIMARY KEY,
    game_id         uuid        NOT NULL UNIQUE REFERENCES games(id) ON DELETE CASCADE,
    guest_id        text        NOT NULL,
    mode            game_mode   NOT NULL,
    level           game_level  NOT NULL,
    correct_count   integer     NOT NULL CHECK (correct_count >= 0),
    wrong_count     integer     NOT NULL CHECK (wrong_count >= 0),
    skipped_count   integer     NOT NULL CHECK (skipped_count >= 0),
    actual_ms       bigint      NOT NULL CHECK (actual_ms >= 0),
    penalty_ms      bigint      NOT NULL CHECK (penalty_ms >= 0),
    scoring_ms      bigint      NOT NULL CHECK (scoring_ms >= 0),
    started_at      timestamptz NOT NULL,
    finished_at     timestamptz NOT NULL
);

CREATE TABLE personal_bests (
    guest_id     text        NOT NULL,
    mode         game_mode   NOT NULL,
    level        game_level  NOT NULL,
    result_id    uuid        NOT NULL UNIQUE REFERENCES game_results(result_id) ON DELETE CASCADE,
    achieved_at  timestamptz NOT NULL,
    best_correct integer     NOT NULL CHECK (best_correct >= 0),
    best_scoring_ms bigint   NOT NULL CHECK (best_scoring_ms >= 0),
    CONSTRAINT uq_best_guest_mode_level UNIQUE (guest_id, mode, level)
);

CREATE INDEX idx_games_guest ON games (guest_id, started_at DESC);
CREATE INDEX idx_results_guest ON game_results (guest_id, finished_at DESC);
