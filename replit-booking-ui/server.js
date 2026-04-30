import express from 'express';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const app = express();
const PORT = process.env.PORT || 3000;

const GAS_URL = 'https://script.google.com/macros/s/AKfycbyUzhb2Yo1_dWM3VgaSOVc1OGDlMvGMkQQuqB7QrcwnY-ci4d3yIC-lgCRZvPkeyGOahg/exec';

app.use(express.static(__dirname));
app.use(express.urlencoded({ extended: true }));

// GET proxy — e.g. /api/gas?action=getalldata
app.get('/api/gas', async (req, res) => {
  try {
    const url = new URL(GAS_URL);
    for (const [k, v] of Object.entries(req.query)) url.searchParams.set(k, v);
    const r = await fetch(url.toString(), { redirect: 'follow' });
    const data = await r.json();
    res.json(data);
  } catch (err) {
    res.status(502).json({ status: 'error', message: err.message });
  }
});

// POST proxy — body forwarded as URLSearchParams (same as GAS expects)
app.post('/api/gas', async (req, res) => {
  try {
    const body = new URLSearchParams(req.body);
    const r = await fetch(GAS_URL, { method: 'POST', body, redirect: 'follow' });
    const data = await r.json();
    res.json(data);
  } catch (err) {
    res.status(502).json({ status: 'error', message: err.message });
  }
});

app.listen(PORT, () => console.log(`Listening on port ${PORT}`));
