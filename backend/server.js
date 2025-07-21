const express = require('express');
const cors = require('cors');
const predictRouter = require('./routes/predict');
const { askSmartFarmBot } = require('./routes/llm');

const app = express();
app.use(cors());
app.use(express.json());

app.use('/predict', predictRouter);

// 스마트팜 LLM 챗봇
app.post('/ask', async (req, res) => {
  const userMessage = req.body.userMessage || '';
  try {
    const answer = await askSmartFarmBot(userMessage);
    res.json({ reply: answer });
  } catch (err) {
    res.status(500).json({ reply: err.message });
  }
});

const PORT = 3001;
app.listen(PORT, () => {
  console.log(`서버 실행 중: http://localhost:${PORT}`);
});
