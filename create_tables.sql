CREATE TABLE IF NOT EXISTS chat(
	chat_id	BIGINT PRIMARY KEY,
	chat_mode VARCHAR(100) NOT NULL,
	awaits_for VARCHAR(200),
	timezone INTEGER
);

CREATE TABLE IF NOT EXISTS reminder(
	id BIGSERIAL PRIMARY KEY,
	chat_id	BIGINT NOT NULL REFERENCES chat,
	reminder_date TIMESTAMP NOT NULL,
	reminder_text VARCHAR(200),

	UNIQUE(reminder_date, chat_id)
);

CREATE TABLE IF NOT EXISTS temp_datetime(
	id BIGSERIAL PRIMARY KEY,
	chat_id	BIGINT REFERENCES chat UNIQUE NOT NULL,
	reminder_date VARCHAR(20),
	reminder_time VARCHAR(20)
);