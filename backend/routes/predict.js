const express = require('express');
const { exec } = require('child_process');
const path = require('path');
const router = express.Router();

router.post('/', (req, res) => {
  const farmId = req.body.farm_id || 1;
  const crop = req.body.crop || 'tomato'; // crop 값 받기

  // crop 값에 따라 파이썬 스크립트 경로 선택
  let pyScriptName = '';
  if (crop === 'tomato') {
    pyScriptName = 'Tomato_predict.py';
  } else if (crop === 'paprika') {
    pyScriptName = 'Paprika_predict.py';
  } else {
    return res.status(400).json({ status: "error", message: "Invalid crop type" });
  }

  const pyScriptPath = path.resolve(__dirname, '..', 'Ai', pyScriptName);
  const pyCmd = `python "${pyScriptPath}" ${farmId}`;

  exec(pyCmd, (error, stdout, stderr) => {
    if (error) {
      console.error('Python error:', stderr);
      return res.status(500).json({ status: "error", message: "Python execution error", detail: stderr });
    }

    console.log('PYTHON STDOUT:', stdout);
    try {
      const jsonStart = stdout.indexOf('{');
      const jsonEnd = stdout.lastIndexOf('}');
      if (jsonStart === -1 || jsonEnd === -1) throw new Error("No JSON found in Python output");
      const jsonString = stdout.substring(jsonStart, jsonEnd + 1);
      const data = JSON.parse(jsonString);
      return res.json(data);
    } catch (e) {
      console.error('Failed to parse Python response:', stdout);
      return res.status(500).json({ status: "error", message: "Failed to parse Python response", raw: stdout });
    }
  });
});
module.exports = router;
