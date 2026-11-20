CREATE KEYSPACE IF NOT EXISTS lab16
WITH replication = {'class':'SimpleStrategy','replication_factor':1};

CREATE TABLE IF NOT EXISTS lab16.student_courses (
    student_id text,
    course_id text,
    student_name text,
    course_name text,
    PRIMARY KEY (student_id, course_id)
);

CREATE TABLE IF NOT EXISTS lab16.course_students (
    course_id text,
    student_id text,
    student_name text,
    course_name text,
    PRIMARY KEY (course_id, student_id)
);

CREATE TABLE IF NOT EXISTS lab16.user_events (
    user_id text,
    event_time timestamp,
    event_type text,
    transaction_id text,
    amount double,
    counterparty_id text,
    PRIMARY KEY (user_id, event_time)
) WITH CLUSTERING ORDER BY (event_time DESC);
