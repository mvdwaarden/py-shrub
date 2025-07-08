// server.js
const express = require('express');
const path = require('path');

const app = express();
const PORT = 3000;

// Serve static files like index.html
app.use(express.static(path.join(__dirname)));

// Start the server
app.listen(PORT, () => {
  console.log(`Server is running at http://localhost:${PORT}`);
});
