from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class VehicleCategory(str, Enum):
    TRUCK_HEAVY = "TRUCK_HEAVY"    # Carreta / Cavalo Mecânico (pesado)
    TRUCK_MEDIUM = "TRUCK_MEDIUM"  # Caminhão Médio (Toco / 3/4)
    VAN_LIGHT = "VAN_LIGHT"        # Van / Utilitário de Carga


class AnomalyLevel(str, Enum):
    NORMAL = "NORMAL"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class FuelLogCreate(BaseModel):
    vehicle_id: str = Field(..., examples=["BRA-2E19"], description="Placa ou identificador do veículo")
    driver_name: str = Field(..., examples=["Carlos Eduardo Silva"], description="Nome do motorista responsável")
    vehicle_type: VehicleCategory = Field(..., examples=[VehicleCategory.TRUCK_HEAVY], description="Categoria do veículo na frota")
    tank_capacity_liters: float = Field(..., gt=0, examples=[550.0], description="Capacidade máxima do tanque em litros")
    odometer_km: float = Field(..., gt=0, examples=[142500.0], description="Quilometragem total atual do odômetro")
    distance_traveled_km: float = Field(..., gt=0, examples=[650.0], description="Km rodados desde o último abastecimento")
    liters_filled: float = Field(..., gt=0, examples=[270.0], description="Quantidade de diesel abastecida em litros")
    fuel_cost_brl: float = Field(..., gt=0, examples=[1620.0], description="Valor total pago em R$")
    gas_station: str = Field(..., examples=["Posto Graal Rodovia SP-330"], description="Nome/Posto do abastecimento")


class FuelLogResponse(BaseModel):
    id: str
    created_at: datetime
    vehicle_id: str
    driver_name: str
    vehicle_type: VehicleCategory
    tank_capacity_liters: float
    odometer_km: float
    distance_traveled_km: float
    liters_filled: float
    fuel_cost_brl: float
    gas_station: str
    consumption_km_per_liter: float
    cost_per_km_brl: float
    anomaly_level: AnomalyLevel
    alert_message: str


class FleetMetrics(BaseModel):
    total_logs: int
    total_liters: float
    total_spent_brl: float
    average_km_per_liter: float
    anomalies_count: dict[str, int]
    system_status: str
