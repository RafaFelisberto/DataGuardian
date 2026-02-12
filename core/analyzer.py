import os
import datetime
from typing import Any, Dict, List, Tuple, Optional

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


class AnomalyAnalyzer:
    """Detector de anomalias para logs de acesso.

    Importante:
    - Treino (fit) e detecção (predict) são separados.
    - Salva **modelo + scaler + ordem das features** no mesmo arquivo.
    """

    def __init__(self, model_path: str = "models/anomaly_model.pkl") -> None:
        self.model_path = model_path
        self.model = IsolationForest(contamination=0.1, random_state=42)
        self.scaler = StandardScaler()
        self.feature_names: List[str] = []
        self.is_fitted: bool = False
        self.load_model()

    def load_model(self) -> None:
        """Carrega modelo salvo (se existir)."""
        if not os.path.exists(self.model_path):
            return
        try:
            import joblib

            artifact = joblib.load(self.model_path)
            # compat: se for modelo antigo
            if isinstance(artifact, dict) and "model" in artifact:
                self.model = artifact["model"]
                self.scaler = artifact["scaler"]
                self.feature_names = artifact.get("feature_names", [])
                self.is_fitted = True
            else:
                # antigo: só o model
                self.model = artifact
                self.is_fitted = True
        except Exception as e:
            print(f"Erro ao carregar modelo: {e}. Continuando sem modelo treinado...")

    def save_model(self) -> None:
        """Salva modelo + scaler + metadata."""
        import joblib

        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        artifact = {
            "model": self.model,
            "scaler": self.scaler,
            "feature_names": self.feature_names,
            "saved_at": datetime.datetime.utcnow().isoformat() + "Z",
        }
        joblib.dump(artifact, self.model_path)
        print(f"Modelo salvo em {self.model_path}")

    # -------- Feature Engineering --------

    def _parse_timestamp(self, timestamp: Any) -> datetime.datetime:
        try:
            if isinstance(timestamp, (int, float)):
                return datetime.datetime.fromtimestamp(timestamp)
            return datetime.datetime.strptime(str(timestamp), "%Y-%m-%d %H:%M:%S")
        except Exception:
            return datetime.datetime.now()

    def _calculate_user_entropy(self, user: str) -> float:
        # Placeholder determinístico (MVP). Trocar por estatística real no futuro.
        return (hash(user) % 1000) / 1000.0

    def _calculate_location_entropy(self, ip: str) -> float:
        return (hash(ip) % 1000) / 1000.0

    def _get_data_sensitivity(self, data_type: str) -> float:
        sensitivity = {
            "CPF": 10,
            "CNPJ": 9,
            "SENHA": 10,
            "TOKEN": 9,
            "EMAIL": 5,
            "TELEFONE": 4,
        }
        return float(sensitivity.get(str(data_type).upper(), 3))

    def extract_feature_matrix(self, logs: List[Dict[str, Any]]) -> Tuple[np.ndarray, List[str]]:
        """Extrai matriz numérica + ordem de features."""
        rows: List[Dict[str, float]] = []
        for log in logs:
            try:
                ts = self._parse_timestamp(log.get("timestamp", ""))
                row = {
                    "hour": float(ts.hour),
                    "weekday": float(ts.weekday()),
                    "access_count": float(log.get("access_count", 1) or 1),
                    "data_size": float(len(str(log.get("data_accessed", "")))),
                    "user_entropy": float(self._calculate_user_entropy(str(log.get("user", "")))),
                    "location_entropy": float(self._calculate_location_entropy(str(log.get("ip", "")))),
                    "data_sensitivity": float(self._get_data_sensitivity(str(log.get("data_type", "")))),
                }
                rows.append(row)
            except Exception as e:
                print(f"Erro ao processar log: {e}")

        if not rows:
            return np.zeros((0, 0)), []

        feature_names = sorted(rows[0].keys())
        matrix = np.array([[r[k] for k in feature_names] for r in rows], dtype=float)
        return matrix, feature_names

    # -------- Training / Detection --------

    def train(self, access_logs: List[Dict[str, Any]]) -> None:
        X, names = self.extract_feature_matrix(access_logs)
        if X.size == 0:
            raise ValueError("Sem dados para treinar o modelo de anomalias")

        self.feature_names = names
        Xs = self.scaler.fit_transform(X)
        self.model.fit(Xs)
        self.is_fitted = True
        self.save_model()

    def detect_anomalies(self, logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        X, names = self.extract_feature_matrix(logs)
        if X.size == 0:
            return []

        # Se não há modelo treinado, faz um fit rápido no dataset atual (fallback),
        # mas deixa claro que é baseline local.
        if not self.is_fitted or not self.feature_names:
            self.feature_names = names
            Xs = self.scaler.fit_transform(X)
            self.model.fit(Xs)
            self.is_fitted = True
        else:
            # garante mesma ordem de features
            if names != self.feature_names:
                # reordena X para bater com o modelo salvo
                idx = {n: i for i, n in enumerate(names)}
                X = np.array([[row[idx[n]] for n in self.feature_names] for row in X], dtype=float)
            Xs = self.scaler.transform(X)

        preds = self.model.predict(Xs)
        scores = self.model.score_samples(Xs)

        results: List[Dict[str, Any]] = []
        for i, (pred, score) in enumerate(zip(preds, scores)):
            results.append(
                {
                    "log": logs[i],
                    "anomaly": bool(pred == -1),
                    "score": float(-score),  # maior => mais anômalo
                    "reason": self._explain_anomaly(X[i], self.feature_names),
                }
            )
        return results

    def _explain_anomaly(self, x_row: np.ndarray, names: List[str]) -> List[str]:
        """Heurística simples em valores *não normalizados* (coerente)."""
        v = {n: float(x_row[i]) for i, n in enumerate(names)}
        reasons: List[str] = []
        if v.get("hour", 0) >= 22 or v.get("hour", 0) <= 5:
            reasons.append("Acesso em horário incomum")
        if v.get("data_size", 0) >= 5000:
            reasons.append("Volume alto de dados acessados")
        if v.get("access_count", 0) >= 50:
            reasons.append("Número de acessos acima do normal")
        if v.get("data_sensitivity", 0) >= 9:
            reasons.append("Acesso a dado altamente sensível")
        return reasons or ["Sem heurística evidente"]
