from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import pairwise_distances
import numpy as np
import os
import datetime

class AnomalyAnalyzer:
    def __init__(self, model_path="models/anomaly_model.pkl"):
        self.model = IsolationForest(contamination=0.1)
        self.scaler = StandardScaler()
        self.model_path = model_path
        self.load_model()

    def load_model(self):
        """Carrega modelo salvo ou treina um novo se não existir"""
        if os.path.exists(self.model_path):
            try:
                import joblib
                self.model = joblib.load(self.model_path)
                print("Modelo carregado com sucesso.")
            except Exception as e:
                print(f"Erro ao carregar modelo: {e}. Treinando novo modelo...")
        else:
            print("Modelo não encontrado. Treinando novo...")

    def save_model(self):
        """Salva o modelo treinado em disco"""
        import joblib
        joblib.dump(self.model, self.model_path)
        print(f"Modelo salvo em {self.model_path}")

    def extract_features(self, logs):
        """Extrai características avançadas dos logs de acesso"""
        features = []
        for log in logs:
            try:
                timestamp = self._parse_timestamp(log.get('timestamp', ''))
                user_entropy = self._calculate_user_entropy(log.get('user', ''))
                location_entropy = self._calculate_location_entropy(log.get('ip', ''))
                
                features.append({
                    "hour": timestamp.hour,
                    "weekday": timestamp.weekday(),
                    "access_count": log.get("access_count", 1),
                    "data_size": len(log.get("data_accessed", "")),
                    "user_entropy": user_entropy,
                    "location_entropy": location_entropy,
                    "data_sensitivity": self._get_data_sensitivity(log.get("data_type", ""))
                })
            except Exception as e:
                print(f"Erro ao processar log: {e}")
        
        return self._normalize_features(features)

    def _parse_timestamp(self, timestamp):
        """Converte timestamp em objeto datetime"""
        try:
            if isinstance(timestamp, (int, float)):
                return datetime.datetime.fromtimestamp(timestamp)
            return datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        except:
            return datetime.datetime.now()

    def _calculate_user_entropy(self, user):
        """Calcula entropia do usuário (ex: acessos únicos)"""
        # Exemplo básico - pode ser substituído por dados reais
        return hash(user) % 10 / 10

    def _calculate_location_entropy(self, ip):
        """Calcula entropia da localização (ex: geolocalização)"""
        # Exemplo básico - pode ser substituído por geolocation API
        return hash(ip) % 10 / 10

    def _get_data_sensitivity(self, data_type):
        """Classificação de risco do tipo de dado"""
        sensitivity = {
            "CPF": 10,
            "SENHA": 9,
            "TOKEN": 8,
            "EMAIL": 5,
            "TELEFONE": 4
        }
        return sensitivity.get(data_type, 3)  # Padrão: médio risco

    def _normalize_features(self, features):
        """Normaliza features para o modelo"""
        feature_matrix = np.array([[f[key] for key in sorted(features[0].keys())] for f in features])
        return self.scaler.fit_transform(feature_matrix)

    def train(self, access_logs):
        """Treina modelo com dados de acesso"""
        features = self.extract_features(access_logs)
        self.model.fit(features)
        self.save_model()

    def detect_anomalies(self, logs):
        """Detecta anomalias e retorna com scores explicativos"""
        features = self.extract_features(access_logs)
        self.model.fit(features)  # Treina o modelo com os dados atuais
        predictions = self.model.predict(features)
        
        results = []
        for i, (pred, score) in enumerate(zip(predictions, scores)):
            results.append({
                "log": logs[i],
                "anomaly": bool(pred == -1),
                "score": float(-score),
                "reason": self._explain_anomaly(features[i], score)
            })
        return results

    def _explain_anomaly(self, features, score):
        """Explica brevemente porquê uma amostra é anômala"""
        reasons = []
        if features[0] > 20:  # Se for noite
            reasons.append("Acesso noturno incomum")
        if features[3] > 100:  # Se dados grandes foram acessados
            reasons.append("Acesso a dados extensos")
        if features[4] > 0.7:  # Alta entropia de usuário
            reasons.append("Padrão de usuário incomum")
        if features[5] > 0.7:  # Alta entropia de localização
            reasons.append("Localização incomum")
        return reasons or ["Comportamento normal"]