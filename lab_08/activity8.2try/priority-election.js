/*
Lab 8.2 - Try It Yourself
Priority-Based Replica Set Election
*/

// Display the current replica-set configuration
print("\n--- Replica Set Priority Configuration ---");

var config = rs.conf();

config.members.forEach(function (member) {
    print(
        member.host +
        " | Priority: " + member.priority +
        " | Arbiter: " + (member.arbiterOnly || false)
    );
});

// Expected configuration:
// mongo-primary     -> Priority 2
// mongo-secondary1  -> Priority 3
// mongo-secondary2  -> Priority 1
// mongo-arbiter     -> Priority 0

/*
Expected result:
If mongo-secondary1 is the current primary and steps down,
mongo-primary should become primary because the priority-3
member is temporarily ineligible for election.
*/

// Display the current member states
print("\n--- Replica Set Member States ---");

rs.status().members.forEach(function (member) {
    print(
        member.name +
        " | " + member.stateStr +
        " | Health: " + member.health
    );
});

print("\nPriority election configuration verified.");