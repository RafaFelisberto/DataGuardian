from sklearn.ensemble import IsolationForest
from datetime import datetime

class AnomalyAnalyzer:
    def __init__(self):
        self.model = IsolationForest(contamination=0.1)
    
    def train(self, access_logs):
        """Treina modelo com dados de acesso"""
        features = self._extract_features(access_logs)
        self.model.fit(features)
    
    def detect_access_anomalies(self, logs):
        features = self._extract_features(logs)
        return self.model.predict(features)
    
    def _extract_features(self, logs):
        """Extrai características dos logs de acesso"""
        features = []
        for log in logs:
            timestamp = datetime.strptime(log['timestamp'], "%Y-%m-%d %H:%M:%S")
            features.append([
                timestamp.hour,
                timestamp.weekday(),
                log['access_count'],
                len(log['data_accessed'])
            ])
        return features