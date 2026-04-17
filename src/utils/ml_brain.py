import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class NeuralBrain:
    """Advanced NLP & ML logic for Data Pilot grounding."""
    
    @staticmethod
    def detect_anomalies(df: pd.DataFrame, column: str = "Total Amount") -> pd.DataFrame:
        """ML-based anomaly detection using Z-Score."""
        if df is None or df.empty or column not in df.columns:
            return pd.DataFrame()
            
        # Group by date to get daily series
        df_daily = df.copy()
        df_daily['date_eval'] = pd.to_datetime(df_daily['Date']).dt.date
        series = df_daily.groupby('date_eval')[column].sum()
        
        if len(series) < 5:
            return pd.DataFrame()
            
        mean = series.mean()
        std = series.std()
        if std == 0: std = 1
        
        z_scores = (series - mean) / std
        anomalies = series[np.abs(z_scores) > 1.5] # 1.5 sigma for "interesting" events
        
        res = []
        for d, val in anomalies.items():
            res.append({
                "date": d,
                "value": val,
                "type": "High" if val > mean else "Low",
                "score": abs(z_scores[d])
            })
        return pd.DataFrame(res)

    @staticmethod
    def semantic_query_intent(query: str) -> dict:
        """Enhanced NLP Intent Router."""
        q = query.lower()
        
        # 1. Forecasting Intent
        if any(w in q for w in ["forecast", "predict", "next week", "future", "outlook"]):
            return {"type": "ml_forecast", "target": "sales" if "sale" in q or "rev" in q else "orders"}
            
        # 2. Anomaly/Audit Intent
        if any(w in q for w in ["anomaly", "weird", "unusual", "audit", "spike", "drop"]):
            return {"type": "ml_anomaly", "target": "general"}
            
        # 3. Fulfillment Intent
        if any(w in q for w in ["when", "stock out", "out of stock", "reorder", "velocity"]):
            return {"type": "fulfillment_prediction", "target": "inventory"}
            
        return {"type": "llm_general", "target": "context"}
