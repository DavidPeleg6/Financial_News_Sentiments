-- CREATE TABLE Sentiments (
--     stock VARCHAR(10),
--     time_published DATETIME,
--     sentiment Decimal(5, 4),
--     relevance_score Decimal(5, 4),
--     sentiment_label VARCHAR(20),
--     source VARCHAR(30),
--     article_url VARCHAR(200),
--     PRIMARY KEY (stock, time_published)
-- );

-- stock	relevance_score	sentiment	sentiment_label	article_url	source	time_published
-- DESCRIBE sentiment;

-- ALTER TABLE sentiment ADD COLUMN relevance_score Decimal(6, 5);
-- ALTER TABLE sentiment ADD COLUMN source_name VARCHAR(30);

-- ALTER TABLE sentiment DROP COLUMN relevance_score;

-- ALTER TABLE sentiment ADD COLUMN sentiment_label VARCHAR(20);


-- DROP TABLE IF EXISTS Sentiments;


SELECT * FROM Sentiments;
