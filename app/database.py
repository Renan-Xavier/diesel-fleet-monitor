from datetime import UTC, datetime

from app.models import AnomalyLevel, FuelLogResponse, VehicleCategory

# Banco de dados em memória para simplicidade e portabilidade do projeto
_db: list[FuelLogResponse] = [
    FuelLogResponse(
        id="init-001",
        created_at=datetime.now(UTC),
        vehicle_id="SCN-4X20",
        driver_name="Marcos Vinicius",
        vehicle_type=VehicleCategory.TRUCK_HEAVY,
        tank_capacity_liters=600.0,
        odometer_km=180420.0,
        distance_traveled_km=820.0,
        liters_filled=360.0,
        fuel_cost_brl=2160.0,
        gas_station="Rede Arco-Íris Dutra",
        consumption_km_per_liter=2.28,
        cost_per_km_brl=2.63,
        anomaly_level=AnomalyLevel.NORMAL,
        alert_message="Consumo e abastecimento dentro dos limites operacionais normais.",
    ),
    FuelLogResponse(
        id="init-002",
        created_at=datetime.now(UTC),
        vehicle_id="VOL-8Z11",
        driver_name="Roberto Souza",
        vehicle_type=VehicleCategory.TRUCK_HEAVY,
        tank_capacity_liters=550.0,
        odometer_km=95200.0,
        distance_traveled_km=410.0,
        liters_filled=310.0,
        fuel_cost_brl=1860.0,
        gas_station="Posto Trevo BR-101",
        consumption_km_per_liter=1.32,
        cost_per_km_brl=4.54,
        anomaly_level=AnomalyLevel.CRITICAL,
        alert_message="[SUSPEITA DE DESVIO/VAZAMENTO] Consumo de 1.32 km/l muito abaixo do limite crítico (1.6 km/l). Possível furto de combustível, vazamento no tanque ou motor desregulado.",
    ),
]


def save_log(log: FuelLogResponse) -> FuelLogResponse:
    _db.append(log)
    return log


def get_all_logs(
    vehicle_id: str | None = None,
    anomaly_level: AnomalyLevel | None = None,
) -> list[FuelLogResponse]:
    results = _db
    if vehicle_id:
        results = [l for l in results if l.vehicle_id == vehicle_id.upper()]
    if anomaly_level:
        results = [l for l in results if l.anomaly_level == anomaly_level]
    return results


def get_log_by_id(log_id: str) -> FuelLogResponse | None:
    for l in _db:
        if l.id == log_id:
            return l
    return None
