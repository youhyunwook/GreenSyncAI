import React, { useState } from 'react';
import axios from 'axios';

function AIButton({ farmId }) {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [crop, setCrop] = useState('tomato'); // 기본값 tomato

  const handleAnalyze = async () => {
    setLoading(true);
    setResult(null);
    try {
      const res = await axios.post('http://localhost:3001/predict', {
        farm_id: farmId,
        crop: crop, // crop 값 추가!
      });

      if (res.data.status === 'success' || res.data.YIELD_CNT) { // YIELD_CNT가 있으면 성공으로 간주
        setResult(res.data.predicted ? res.data.predicted : res.data);
      } else {
        alert('AI 분석 실패: ' + res.data.message);
      }
    } catch (err) {
      console.error(err);
      alert('서버 오류 발생');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: '8px' }}>
        <label>
          <input
            type="radio"
            value="tomato"
            checked={crop === 'tomato'}
            onChange={() => setCrop('tomato')}
          />
          토마토
        </label>
        <label style={{ marginLeft: '16px' }}>
          <input
            type="radio"
            value="paprika"
            checked={crop === 'paprika'}
            onChange={() => setCrop('paprika')}
          />
          파프리카
        </label>
      </div>

      <button onClick={handleAnalyze} disabled={loading}>
        {loading ? 'AI 분석 중...' : 'AI 분석'}
      </button>

      {result && (
        <div>
          <h3>최적 제어값 및 예측 수확수</h3>
          <ul>
            <li>급수량: {result.WTSPL_QTY} L</li>
            <li>난방 온도: {result.HTNG_TPRT_1} ℃</li>
            <li>배기 온도: {result.VNTILAT_TPRT_1} ℃</li>
            <li><strong>예측 수확수: {result.YIELD_CNT}</strong></li>
          </ul>
        </div>
      )}
    </div>
  );
}

export default AIButton;
