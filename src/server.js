const express = require("express");
const bodyParser = require("body-parser");
const cors = require("cors");

const app = express();
const port = 3001;

app.use(cors());

app.use(bodyParser.json());

let waypoints = [];

app.post("/waypoints", (req, res) => {
    const { waypoints: newWaypoints } = req.body;
    if (Array.isArray(newWaypoints)) {
        waypoints = newWaypoints;
        res.status(200).send({ message: "Waypoints updated successfully" });
    } else {
        res.status(400).send({ message: "Invalid waypoints data" });
    }
});

app.get("/waypoints", (req, res) => {
    res.status(200).json(waypoints);
});

app.listen(port, () => {
    console.log(`Server running at http://localhost:${port}`);
});
