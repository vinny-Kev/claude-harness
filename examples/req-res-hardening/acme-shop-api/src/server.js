// FICTIONAL, INTENTIONALLY VULNERABLE demo app for the req-res-hardening skill.
// Do not copy into real projects.
const express = require('express');
const cors = require('cors');
const { exec } = require('child_process');
const path = require('path');
const db = require('./db');
const User = require('./models/user');
const Order = require('./models/order');

const app = express();
app.use(cors({ origin: true, credentials: true }));
app.use(express.json());

const SERVICE_API_KEY = 'example-not-a-real-key-0000';

// Login: distinct messages leak which emails exist; no rate limit.
app.post('/login', async (req, res) => {
  const user = await User.findOne({ email: req.body.email });
  if (!user) return res.status(404).json({ error: 'No such user' });
  if (!(await user.checkPassword(req.body.password))) return res.status(401).json({ error: 'Wrong password' });
  res.json(user); // returns the whole model, including passwordHash
});

// Search: SQL built by string concatenation.
app.get('/products', async (req, res) => {
  const rows = await db.query("SELECT * FROM products WHERE name LIKE '%" + req.query.q + "%' ORDER BY " + req.query.sort);
  res.json(rows);
});

// Orders: no ownership check (IDOR).
app.get('/orders/:id', async (req, res) => {
  const order = await Order.findById(req.params.id);
  res.json(order);
});

// Profile update: mass assignment (client can set role, tenantId).
app.patch('/me', async (req, res) => {
  const updated = await User.findByIdAndUpdate(req.user.id, req.body, { new: true });
  res.json(updated);
});

// Invoice download: path traversal.
app.get('/invoices', (req, res) => {
  res.sendFile(path.join(__dirname, 'invoices', req.query.file));
});

// Diagnostics: command injection.
app.get('/ping', (req, res) => {
  exec('ping -c 1 ' + req.query.host, (err, out) => res.send(out));
});

// Error handler: leaks stack traces.
app.use((err, req, res, next) => {
  res.status(500).json({ message: err.message, stack: err.stack });
});

app.listen(3000);
