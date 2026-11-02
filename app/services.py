import uuid
from datetime import UTC, datetime

from app.models import (
    AnomalyLevel,
    FuelLogCreate,
    FuelLogResponse,
    VehicleCategory,
)

# Faixas normais de consumo de diesel (km/l) por tipo de veículo
CONSUMPTION_RULES = {
    VehicleCategory.TRUCK_HEAVY: {
        "min_critical": 1.6,   # Abaixo disso = forte suspeita de desvio/furto ou vazamento
        "min_normal": 1.9,
        "max_normal": 2.8,
        "max_warning": 3.8,    # Acima disso = possível fraude de odômetro
    },
    VehicleCategory.TRUCK_MEDIUM: {
        "min_critical": 2.8,
        "min_normal": 3.3,
        "max_normal": 5.2,
        "max_warning": 6.8,
    },
    VehicleCategory.VAN_LIGHT: {
        "min_critical": 6.0,
        "min_normal": 7.5,
        "max_normal": 12.0,
        "max_warning": 15.0,
    },
}


def analyze_fuel_entry(payload: FuelLogCreate) -> FuelLogResponse:
    """
    Processa o abastecimento, calcula indicadores-chave de eficiência
    e executa regras de auditoria para prevenção de fraudes e desvios de diesel.
    """
    km_per_liter = round(payload.distance_traveled_km / payload.liters_filled, 2)
    cost_per_km = round(payload.fuel_cost_brl / payload.distance_traveled_km, 2)

    anomaly_level = AnomalyLevel.NORMAL
    alert_message = "Consumo e abastecimento dentro dos limites operacionais normais."

    # Regra 1: Abastecimento maior que a capacidade física do tanque (fraude de nota/bomba)
    if payload.liters_filled > payload.tank_capacity_liters:
        anomaly_level = AnomalyLevel.CRITICAL
        alert_message = (
            f"[ALERTA CRÍTICO] Volume abastecido ({payload.liters_filled:.1f}L) "
            f"excede a capacidade do tanque ({payload.tank_capacity_liters:.1f}L). "
            f"Forte indício de fraude na nota fiscal ou bomba adulterada."
        )
        return _build_response(payload, km_per_liter, cost_per_km, anomaly_level, alert_message)

    # Regra 2: Análise de consumo por categoria de veículo
    rule = CONSUMPTION_RULES.get(payload.vehicle_type)
    if rule:
        if km_per_liter < rule["min_critical"]:
            anomaly_level = AnomalyLevel.CRITICAL
            alert_message = (
                f"[SUSPEITA DE DESVIO/VAZAMENTO] Consumo de {km_per_liter:.2f} km/l "
                f"muito abaixo do limite crítico ({rule['min_critical']} km/l). "
                f"Possível furto de combustível, vazamento no tanque ou motor desregulado."
            )
        elif km_per_liter < rule["min_normal"]:
            anomaly_level = AnomalyLevel.WARNING
            alert_message = (
                f"[ATENÇÃO] Consumo de {km_per_liter:.2f} km/l ligeiramente abaixo da média esperada "
                f"({rule['min_normal']} - {rule['max_normal']} km/l). Verificar condução do motorista."
            )
        elif km_per_liter > rule["max_warning"]:
            anomaly_level = AnomalyLevel.WARNING
            alert_message = (
                f"[INCONSISTÊNCIA] Consumo registrado de {km_per_liter:.2f} km/l é incomumente alto. "
                f"Verificar se o odômetro foi informado corretamente ou se houve abastecimento parcial."
            )

    return _build_response(payload, km_per_liter, cost_per_km, anomaly_level, alert_message)


def _build_response(
    payload: FuelLogCreate,
    km_per_liter: float,
    cost_per_km: float,
    anomaly_level: AnomalyLevel,
    alert_message: str,
) -> FuelLogResponse:
    return FuelLogResponse(
        id=str(uuid.uuid4())[:8],
        created_at=datetime.now(UTC),
        vehicle_id=payload.vehicle_id.upper(),
        driver_name=payload.driver_name,
        vehicle_type=payload.vehicle_type,
        tank_capacity_liters=payload.tank_capacity_liters,
        odometer_km=payload.odometer_km,
        distance_traveled_km=payload.distance_traveled_km,
        liters_filled=payload.liters_filled,
        fuel_cost_brl=payload.fuel_cost_brl,
        gas_station=payload.gas_station,
        consumption_km_per_liter=km_per_liter,
        cost_per_km_brl=cost_per_km,
        anomaly_level=anomaly_level,
        alert_message=alert_message,
    )
