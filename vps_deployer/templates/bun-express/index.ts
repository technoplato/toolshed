import express from "express";

const app = express();
const port = 3000;

app.get("/", (req, res) => {
  res.json({ Hello: "World", Service: "Bun Express" });
});

app.get("/secure-data", (req, res) => {
  res.json({
    secure: true,
    data: "This data is only visible if you passed the Traefik gate.",
    headers: req.headers,
  });
});

app.listen(port, () => {
  console.log(`Listening on port ${port}...`);
});
