import React, { useState } from 'react';
import AIButton from './Aibutton.js'; 
import ReactMarkdown from 'react-markdown';


function App() {
  const farmId = 1;
  const [input, setInput] = useState('');
  const [reply, setReply] = useState('');

  const handleSend = async () => {
    if (!input.trim()) return;

    const res = await fetch('http://localhost:3001/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ userMessage: input }),
    });

    const data = await res.json();
    setReply(data.reply);
  };

  return (
    <div>
      <div style={{ padding: '2rem' }}>
        <h2>스마트팜 도우미 챗봇</h2>
        <textarea
          rows={5}
          style={{ width: '100%' }}
          placeholder="농장 관련 질문을 입력하세요"
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
        <button onClick={handleSend}>질문하기</button>
        <div style={{ marginTop: '1rem' }}>
          <ReactMarkdown>{reply}</ReactMarkdown>
        </div>
      </div>
        
      <div style={{ padding: '2rem' }}>
   
        {/* 다른 대시보드 위젯들 … */}
   
        {/* AI 분석 버튼 */}
        <AIButton farmId={farmId} />
   
        {/* 분석 결과를 표시하는 영역은 AIButton 내부에 포함되어 있으므로 따로 둘 필요 없음 */}
      </div>
    </div>
  );
}

export default App;

