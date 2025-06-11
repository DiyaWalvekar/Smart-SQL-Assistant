# 1st DATABASE
CREATE DATABASE IF NOT EXISTS users;

USE users;

CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  password VARCHAR(255) NOT NULL
);

#inside the users DATABASE

CREATE TABLE query_history ( 
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    query_text TEXT NOT NULL,
    query_result TEXT,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
 
# 2nd DATABASE 
CREATE DATABASE IF NOT EXISTS voice_sql;
USE voice_sql;