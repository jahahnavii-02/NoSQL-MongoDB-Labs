// Lab 8.1 - Try It Yourself
// Add an arbiter only if it is not already configured.

const members = rs.conf().members;
const arbiterExists = members.some(m => m.arbiterOnly === true);

if (arbiterExists) {
    print("An arbiter is already configured; no change made.");
} else {
    rs.addArb("mongo-arbiter:27017");
}

rs.status().members.forEach(m =>
    print(m.name + " | " + m.stateStr + " | health: " + m.health)
);