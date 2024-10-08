CREATE TABLE IF NOT EXISTS todo
(
    id SERIAL,
    guild_id BIGINT,
    message TEXT,
    priority_level INT,
    message_id BIGINT,
    message_link TEXT
);

CREATE TABLE IF NOT EXISTS settings
(
    guild_id BIGINT PRIMARY KEY,
    output_channel_id BIGINT,
    allowed_role_ids BIGINT[]
);