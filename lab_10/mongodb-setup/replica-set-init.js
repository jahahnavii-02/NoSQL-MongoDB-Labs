// Lab 8.1 - Replica Set Initialization

rs.initiate({
    _id: "rs0",
    members: [
        { _id: 0, host: "mongo-primary:27017", priority: 2 },
        { _id: 1, host: "mongo-secondary1:27017", priority: 1 },
        { _id: 2, host: "mongo-secondary2:27017", priority: 1 }
    ]
})

// Verify replica-set status
rs.status()

// Print member states
rs.status().members.forEach(
    m => print(
        m.name + " | " +
        m.stateStr + " | health: " +
        m.health
    )
)

// View configuration
rs.conf()