import psycopg2
import pandas as pd
import numpy as np
import joblib
import json
import sys
from datetime import datetime
from dotenv import load_dotenv
import os
load_dotenv()

# === DB 설정 ===
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
# FARM_ID = 1

if len(sys.argv) < 2:
    sys.stderr.write("No farmId passed")
    exit(1)

FARM_ID = sys.argv[1]
sys.stderr.write(f"Farm ID: {FARM_ID}")

FARM_ID = int(FARM_ID)

# === 모델 로딩 ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_models():
    try:
        models = {
            'qty': joblib.load(os.path.join(BASE_DIR,"Tomato","WTSPL_QTY_model.pkl")),
            'vnt': joblib.load(os.path.join(BASE_DIR,"Tomato","VNTILAT_TPRT_1_model.pkl")),
            'htg': joblib.load(os.path.join(BASE_DIR,"Tomato","HTNG_TPRT_1_model.pkl")),
            'yield': joblib.load(os.path.join(BASE_DIR,"Tomato","final_tomato_yield_model.pkl"))
        }
        sys.stderr.write("모든 모델 로딩 완료\n")
        return models
    except Exception as e:
        sys.stderr.write(json.dumps({"status": "error", "message": f"모델 로딩 실패: {e}"}))
        sys.exit(1)

def get_farm_data(farm_id):
    query = """
    SELECT 
        cd.co2 AS pfbs_ntro_cbdx_ctrn,
        t.temperature AS inner_tprt_1,
        h.humidity AS inner_hmdt_1,
        n.ph_level AS ntslt_spl_ph_lvl,
        n.elcdt AS ntslt_spl_elcdt,
        w.is_day AS dytm_night_cd,
        w.is_rain AS prcpt_yn,
        w.wind_direction AS wndrc,
        w.wind_speed AS wdsp,
        w.outside_temp AS extn_tprt,
        w.insolation AS extn_srqt
    FROM farm f
    LEFT JOIN carbon_dioxide cd ON f.id = cd.farm_id
    LEFT JOIN temperature t ON f.id = t.farm_id
    LEFT JOIN humidity h ON f.id = h.farm_id
    LEFT JOIN nutrient n ON f.id = n.farm_id
    LEFT JOIN weather w ON f.id = w.farm_id
    WHERE f.id = %s
    ORDER BY cd.id DESC NULLS LAST
    LIMIT 1;
    """
    try:
        conn = psycopg2.connect(
            host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
            user=DB_USER, password=DB_PASSWORD,
            options='-c client_encoding=UTF8'
        )
        cursor = conn.cursor()
        cursor.execute(query, (farm_id,))
        rows = cursor.fetchall()
        colnames = [desc[0] for desc in cursor.description]
        conn.close()
        if not rows:
            sys.stderr.write(json.dumps({"status": "error", "message": "데이터가 없습니다"}) + "\n")
            sys.exit(1)
        return pd.DataFrame(rows, columns=colnames)
    except Exception as e:
        sys.stderr.write(json.dumps({"status": "error", "message": f"DB 조회 오류: {e}"}) + "\n")
        sys.exit(1)

def preprocess_data(df):
    df.rename(columns={
        "pfbs_ntro_cbdx_ctrn": "PFBS_NTRO_CBDX_CTRN",
        "inner_tprt_1": "INNER_TPRT_1",
        "inner_hmdt_1": "INNER_HMDT_1",
        "ntslt_spl_ph_lvl": "NTSLT_SPL_PH_LVL",
        "ntslt_spl_elcdt": "NTSLT_SPL_ELCDT",
        "dytm_night_cd": "DYTM_NIGHT_CD",
        "prcpt_yn": "PRCPT_YN",
        "wndrc": "WNDRC",
        "wdsp": "WDSP",
        "extn_tprt": "EXTN_TPRT",
        "extn_srqt": "EXTN_SRQT",
    }, inplace=True)
    required_columns = ["INNER_TPRT_1", "INNER_HMDT_1"]
    for col in required_columns:
        if df[col].isnull().any():
            sys.stderr.write(json.dumps({"status": "error", "message": f"필수 컬럼 {col}에 NULL 값이 있습니다"}) + "\n")
            sys.exit(1)
    T = df["INNER_TPRT_1"].values[0]
    RH = df["INNER_HMDT_1"].values[0]
    AH = (6.112 * np.exp((17.67 * T) / (T + 243.5)) * RH * 2.1674) / (273.15 + T)
    df["ABSLT_HMDT"] = round(AH, 2)
    df["STRTN_WATER"] = round(0.622 * AH, 2)
    now = datetime.now()
    df["year"] = now.year
    df["month"] = now.month
    df["day"] = now.day
    df["hour"] = now.hour
    sys.stderr.write("데이터 전처리 완료\n")
    return df

def predict_control_values(df, models):
    results = {}
    try:
        sys.stderr.write("급수량 예측 중...\n")
        X_qty = df.reindex(columns=models['qty'].feature_names_in_)
        opt_qty = models['qty'].predict(X_qty)[0]
        results['WTSPL_QTY'] = round(opt_qty, 2)
        sys.stderr.write(f"예측 급수량(WTSPL_QTY): {opt_qty:.2f}\n")
    except Exception as e:
        sys.stderr.write(json.dumps({"status": "error", "message": f"급수량 예측 실패: {e}"}) + "\n")
        sys.exit(1)
    try:
        sys.stderr.write("배기온도 예측 중...\n")
        X_vnt = df.reindex(columns=models['vnt'].feature_names_in_)
        opt_vnt = models['vnt'].predict(X_vnt)[0]
        results['VNTILAT_TPRT_1'] = round(opt_vnt, 2)
        sys.stderr.write(f"예측 배기온도(VNTILAT_TPRT_1): {opt_vnt:.2f}\n")
    except Exception as e:
        sys.stderr.write(json.dumps({"status": "error", "message": f"배기온도 예측 실패: {e}"}) + "\n")
        sys.exit(1)
    try:
        sys.stderr.write("난방온도 예측 중...\n")
        X_htg = df.reindex(columns=models['htg'].feature_names_in_)
        opt_htg = models['htg'].predict(X_htg)[0]
        results['HTNG_TPRT_1'] = round(opt_htg, 2)
        sys.stderr.write(f"예측 난방온도(HTNG_TPRT_1): {opt_htg:.2f}\n")
    except Exception as e:
        sys.stderr.write(json.dumps({"status": "error", "message": f"난방온도 예측 실패: {e}"}) + "\n")
        sys.exit(1)
    return results

def predict_yield(df, control_values, model_yield):
    try:
        sys.stderr.write("수확량 예측 중...\n")
        df_input = df.copy()
        df_input["WTSPL_QTY"] = control_values['WTSPL_QTY']
        df_input["VNTILAT_TPRT_1"] = control_values['VNTILAT_TPRT_1']
        df_input["HTNG_TPRT_1"] = control_values['HTNG_TPRT_1']
        X_yield = df_input.reindex(columns=model_yield.feature_names_in_)
        pred_yield = model_yield.predict(X_yield)[0]
        sys.stderr.write(f"예측 수확량(YIELD_CNT): {pred_yield:.2f}\n")
        return round(pred_yield, 2)
    except Exception as e:
        sys.stderr.write(json.dumps({"status": "error", "message": f"수확량 예측 실패: {e}"}) + "\n")
        sys.exit(1)

def save_to_db(farm_id, control_values):
    try:
        conn = psycopg2.connect(
            host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
            user=DB_USER, password=DB_PASSWORD,
            options='-c client_encoding=UTF8'
        )
         # optimization 로 수정할것 
        cur = conn.cursor()
        insert_sql = """
        INSERT INTO optimalization (                          
            farm_id, heating, ventilation, water_supply
        ) VALUES (%s, %s, %s, %s)
        """
        cur.execute(insert_sql, (
            farm_id, 
            control_values['HTNG_TPRT_1'], 
            control_values['VNTILAT_TPRT_1'], 
            control_values['WTSPL_QTY']
        ))
        conn.commit()
        cur.close()
        conn.close()
        sys.stderr.write("DB 저장 완료\n")
    except Exception as e:
        sys.stderr.write(json.dumps({"status": "error", "message": f"DB 저장 오류: {e}"}) + "\n")
        sys.exit(1)

def main():
    sys.stderr.write("농장 최적화 예측 시작\n")
    models = load_models()
    sys.stderr.write("농장 데이터 조회 중...\n")
    df = get_farm_data(FARM_ID)
    df = preprocess_data(df)
    control_values = predict_control_values(df, models)
    predicted_yield = predict_yield(df, control_values, models['yield'])
    final_result = {**control_values, 'YIELD_CNT': predicted_yield}
    save_to_db(FARM_ID, control_values)
    # 결과만 표준출력(JSON)
    print(json.dumps({
        "status": "success",
        "predicted": final_result
    }, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
