const fs = require('fs');
const { encode } = require('gpt-3-encoder');

const prompt = fs.readFileSync('./prompt.txt', 'utf-8');
const tokens = encode(prompt);
console.log(`토큰 수: ${tokens.length}`);
