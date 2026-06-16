"""
Project: FinTech Risk Isolation Engine
Module: Core Modeling Layer (Indian Market Option Edition)
Author: Mohit Singh
Description: Features an explicit column-renaming step to cleanly separate 
             raw index features from FinBERT sentiment features during data merges.
"""

import os
import pandas as pd
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import xgboost as xgb

class FinTechPredictiveEngine:
    """Combines FinBERT sentiment streams with historic index weights to train gradient-boosted models."""
    
    def __init__(self, data_dir: str = "data", model_dir: str = "models"):
        # Points directly to the data and models directories inside FinTech_Risk_Engine
        self.data_dir = data_dir
        self.model_dir = model_dir
        os.makedirs(self.model_dir, exist_ok=True)
        
        # Hardware acceleration allocation
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"[*] Allocating Deep Learning Runtime Context onto Engine Core: {self.device}")
        self.tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
        self.nlp_model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert").to(self.device)

    def compute_sentiment(self, text: str) -> float:
        """Transforms text strings into a continuous numerical scale [-1, +1]."""
        if not text or pd.isna(text): return 0.0
        inputs = self.tokenizer(text, padding=True, truncation=True, return_tensors="pt").to(self.device)
        with torch.no_grad():
            outputs = self.nlp_model(**inputs)
        probs = torch.softmax(outputs.logits, dim=-1).squeeze()
        # Direct structural optimization mapping: Positive Probs minus Negative Probs
        return (probs[0] - probs[1]).item()

    def build_predictive_matrix(self) -> pd.DataFrame:
        """Merges index metrics with calculated NLP scores into a unified ML training matrix."""
        print("[*] Accessing structural data files for matrix alignment...")
        
        prices_path = os.path.join(self.data_dir, "clean_market_prices.csv")
        news_path = os.path.join(self.data_dir, "raw_news_headlines.csv")
        
        if not os.path.exists(prices_path) or not os.path.exists(news_path):
            raise FileNotFoundError("Raw matrix files missing. Ensure data/ folder contains generated CSVs.")
            
        prices_df = pd.read_csv(prices_path, index_col=0, parse_dates=True)
        news_df = pd.read_csv(news_path)
        
        # Primary Derivative Target Vector Setup (Nifty 50 Index Return Vectors)
        target_asset = '^NSEI'
        prices_df['Target_Returns'] = prices_df[target_asset].pct_change().shift(-1)
        prices_df['Rolling_Volatility'] = prices_df[target_asset].pct_change().rolling(window=5).std()
        
        print("[*] Running sentiment aggregation processing... (This will process via your CPU/GPU)")
        news_df['Sentiment'] = news_df['Headline'].apply(self.compute_sentiment)
        
        # Group daily headlines by ticker and unstack them
        daily_sentiment = news_df.groupby(['Date', 'Ticker'])['Sentiment'].mean().unstack(fill_value=0)
        daily_sentiment.index = pd.to_datetime(daily_sentiment.index)
        
        # CRITICAL FIX: Explicitly rename sentiment matrix columns to avoid name overlaps with index prices
        daily_sentiment = daily_sentiment.add_suffix('_Sentiment')
        
        print("[*] Merging datasets chronologically into final training array...")
        master_matrix = prices_df.join(daily_sentiment, how='left').fillna(0)
        master_matrix = master_matrix.dropna(subset=['Target_Returns'])
        return master_matrix

    def train_xgboost_engine(self, matrix: pd.DataFrame):
        """Preprocesses features and executes structural training on the XGBoost regressor."""
        print("\n[*] Initializing Supervised Machine Learning Pipeline...")
        
        # Aligned Feature space tracking Indian macro-indices explicitly
        feature_cols = ['^NSEI', '^NSEBANK', 'Rolling_Volatility', '^NSEI_Sentiment', '^NSEBANK_Sentiment']
        
        X = matrix[feature_cols].values
        y = matrix['Target_Returns'].values
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        print("[*] Fitting trees via Gradient Boosting Regressor (XGBoost)...")
        model = xgb.XGBRegressor(n_estimators=150, max_depth=6, learning_rate=0.03, random_state=42)
        model.fit(X_train_scaled, y_train)
        
        predictions = model.predict(X_test_scaled)
        rmse = np.sqrt(np.mean((y_test - predictions) ** 2))
        print(f"[+ SUCCESS] XGBoost Training Complete. Model Validation RMSE Error: {rmse:.5f}")
        
        # Serialize model configurations to the localized models/ directory
        model.save_model(os.path.join(self.model_dir, "xgboost_risk_model.json"))
        print(f"[+ SUCCESS] Trained mathematical models serialized to disk.")

if __name__ == "__main__":
    print("========================================================")
    print("🚀 FAST TRACK: MERGING INDIAN FEATURES & TRAINING XGBOOST")
    print("========================================================\n")
    
    pipeline = FinTechPredictiveEngine()
    master_data = pipeline.build_predictive_matrix()
    pipeline.train_xgboost_engine(master_data)
    
    print("\n========================================================")
    print("🎉 STEP 1 COMPLETE: Indian Core Predictive Engine is Baked and Blocked!")
    print("========================================================")