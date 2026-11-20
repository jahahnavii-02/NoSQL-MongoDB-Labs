CREATE CONSTRAINT student_id IF NOT EXISTS
FOR (s:Student) REQUIRE s.id IS UNIQUE;
CREATE CONSTRAINT course_id IF NOT EXISTS
FOR (c:Course) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT user_id IF NOT EXISTS
FOR (u:User) REQUIRE u.id IS UNIQUE;
CREATE CONSTRAINT transaction_id IF NOT EXISTS
FOR (t:Transaction) REQUIRE t.id IS UNIQUE;

MERGE (alice:Student {id:'S001', name:'Alice'});
MERGE (bob:Student {id:'S002', name:'Bob'});
MERGE (carol:Student {id:'S003', name:'Carol'});
MERGE (ml:Course {id:'C001', name:'Machine Learning'});
MERGE (db:Course {id:'C002', name:'Database Systems'});
MERGE (alice)-[:ENROLLED_IN]->(ml);
MERGE (alice)-[:ENROLLED_IN]->(db);
MERGE (bob)-[:ENROLLED_IN]->(ml);
MERGE (carol)-[:ENROLLED_IN]->(db);
