from fastapi.testclient import TestClient

from app.main import app
from app.models import AnomalyLevel, VehicleCategory

client = TestClient(app)


def test_health_check_endpoint():
    """Garante que a probe /health responda com status HTTP 200 e 'healthy'."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "diesel-fleet-monitor"
    assert "uptime_seconds" in data
    assert "timestamp" in data


def test_create_normal_fuel_log():
    """Testa o registro de abastecimento com consumo perfeitamente normal."""
    payload = {
        "vehicle_id": "CAR-1010",
        "driver_name": "Antônio Fagundes",
        "vehicle_type": VehicleCategory.TRUCK_HEAVY.value,
        "tank_capacity_liters": 600.0,
        "odometer_km": 210000.0,
        "distance_traveled_km": 500.0,
        "liters_filled": 220.0,  # 500 / 220 = 2.27 km/l (normal para pesado)
        "fuel_cost_brl": 1320.0,
        "gas_station": "Posto Shell RodoAnel",
    }
    response = client.post("/api/v1/fuel-logs", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["vehicle_id"] == "CAR-1010"
    assert data["consumption_km_per_liter"] == 2.27
    assert data["anomaly_level"] == AnomalyLevel.NORMAL.value
    assert "limites operacionais normais" in data["alert_message"]


def test_detect_theft_or_leak_anomaly():
    """Testa a regra de detecção de desvio/furto de diesel (consumo extremamente baixo)."""
    payload = {
        "vehicle_id": "CAR-9999",
        "driver_name": "João Alerta",
        "vehicle_type": VehicleCategory.TRUCK_HEAVY.value,
        "tank_capacity_liters": 500.0,
        "odometer_km": 150000.0,
        "distance_traveled_km": 300.0,
        "liters_filled": 250.0,  # 300 / 250 = 1.20 km/l (crítico!)
        "fuel_cost_brl": 1500.0,
        "gas_station": "Posto KM 42",
    }
    response = client.post("/api/v1/fuel-logs", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["consumption_km_per_liter"] == 1.2
    assert data["anomaly_level"] == AnomalyLevel.CRITICAL.value
    assert "SUSPEITA DE DESVIO/VAZAMENTO" in data["alert_message"]


def test_detect_tank_overflow_fraud():
    """Testa quando os litros abastecidos na nota são maiores que a capacidade do tanque."""
    payload = {
        "vehicle_id": "TOCO-2020",
        "driver_name": "Pedro Posto",
        "vehicle_type": VehicleCategory.TRUCK_MEDIUM.value,
        "tank_capacity_liters": 200.0,  # Capacidade de 200L
        "odometer_km": 80000.0,
        "distance_traveled_km": 600.0,
        "liters_filled": 260.0,  # Abasteceu 260L em um tanque de 200L!
        "fuel_cost_brl": 1560.0,
        "gas_station": "Posto Ipiranga",
    }
    response = client.post("/api/v1/fuel-logs", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["anomaly_level"] == AnomalyLevel.CRITICAL.value
    assert "excede a capacidade do tanque" in data["alert_message"]


def test_get_metrics_summary():
    """Testa se o endpoint de métricas operacionais consolida dados corretamente."""
    response = client.get("/metrics")
    assert response.status_code == 200
    metrics = response.json()
    assert metrics["total_logs"] >= 2
    assert metrics["total_liters"] > 0
    assert metrics["average_km_per_liter"] > 0
    assert "anomalies_count" in metrics


def test_get_log_by_id_not_found():
    """Testa tratamento de erro HTTP 404 para ID inexistente."""
    response = client.get("/api/v1/fuel-logs/id-inexistente-12345")
    assert response.status_code == 404
