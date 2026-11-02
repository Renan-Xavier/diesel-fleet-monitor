import time
from datetime import UTC, datetime
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.responses import RedirectResponse

from app.database import get_all_logs, get_log_by_id, save_log
from app.models import (
    AnomalyLevel,
    FleetMetrics,
    FuelLogCreate,
    FuelLogResponse,
)
from app.services import analyze_fuel_entry

START_TIME = time.time()

app = FastAPI(
    title="Diesel Fleet Monitor API",
    description=(
        "API para auditoria e controle de consumo de diesel em frotas rodoviárias. "
        "Detecta anomalias de consumo, suspeitas de desvio/vazamento e fraudes em notas de abastecimento. "
        "Desenvolvido como projeto prático de automação DevOps e engenharia de software."
    ),
    version="1.0.0",
    contact={
        "name": "Renan Xavier",
        "url": "https://github.com/Renan-Xavier",
    },
)


@app.get("/", include_in_schema=False)
def root():
    """Redireciona para a documentação interativa Swagger."""
    return RedirectResponse(url="/docs")


@app.get(
    "/health",
    tags=["Observability & DevOps"],
    summary="Health Check / Readiness Probe",
    status_code=status.HTTP_200_OK,
)
def health_check():
    """
    Endpoint essencial para DevOps:
    Usado por orquestradores (Kubernetes, Docker Swarm, Render, AWS ECS)
    para verificar se a aplicação está viva e pronta para tráfego.
    """
    uptime_seconds = round(time.time() - START_TIME, 2)
    return {
        "status": "healthy",
        "service": "diesel-fleet-monitor",
        "version": "1.0.0",
        "uptime_seconds": uptime_seconds,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@app.get(
    "/metrics",
    response_model=FleetMetrics,
    tags=["Observability & DevOps"],
    summary="Métricas consolidadas da frota",
)
def fleet_metrics():
    """
    Retorna métricas agregadas do consumo de combustível da frota
    para alimentar dashboards de monitoramento (Grafana, Datadog ou Power BI).
    """
    logs = get_all_logs()
    total_logs = len(logs)
    total_liters = sum(l.liters_filled for l in logs)
    total_spent = sum(l.fuel_cost_brl for l in logs)
    total_distance = sum(l.distance_traveled_km for l in logs)

    avg_consumption = round(total_distance / total_liters, 2) if total_liters > 0 else 0.0

    counts = {
        AnomalyLevel.NORMAL.value: sum(1 for l in logs if l.anomaly_level == AnomalyLevel.NORMAL),
        AnomalyLevel.WARNING.value: sum(1 for l in logs if l.anomaly_level == AnomalyLevel.WARNING),
        AnomalyLevel.CRITICAL.value: sum(1 for l in logs if l.anomaly_level == AnomalyLevel.CRITICAL),
    }

    return FleetMetrics(
        total_logs=total_logs,
        total_liters=round(total_liters, 2),
        total_spent_brl=round(total_spent, 2),
        average_km_per_liter=avg_consumption,
        anomalies_count=counts,
        system_status="OPTIMAL" if counts[AnomalyLevel.CRITICAL.value] == 0 else "ATTENTION_REQUIRED",
    )


@app.post(
    "/api/v1/fuel-logs",
    response_model=FuelLogResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Fleet Operations"],
    summary="Registrar e auditar novo abastecimento",
)
def create_fuel_log(payload: FuelLogCreate):
    """
    Registra um novo abastecimento de diesel e roda a análise antifraude/desvio:
    - Calcula o rendimento em km/l
    - Calcula o custo por km rodado em R$
    - Avalia se o volume abastecido cabe no tanque do veículo
    - Compara o consumo com as faixas de normalidade da categoria
    """
    analyzed_log = analyze_fuel_entry(payload)
    saved = save_log(analyzed_log)
    return saved


@app.get(
    "/api/v1/fuel-logs",
    response_model=list[FuelLogResponse],
    tags=["Fleet Operations"],
    summary="Listar histórico de abastecimentos",
)
def list_fuel_logs(
    vehicle_id: Annotated[str | None, Query(description="Filtrar por placa do veículo")] = None,
    anomaly_level: Annotated[AnomalyLevel | None, Query(description="Filtrar por severidade de anomalia")] = None,
):
    """Retorna a lista de registros de abastecimento com filtros opcionais."""
    return get_all_logs(vehicle_id=vehicle_id, anomaly_level=anomaly_level)


@app.get(
    "/api/v1/fuel-logs/{log_id}",
    response_model=FuelLogResponse,
    tags=["Fleet Operations"],
    summary="Obter detalhes de um abastecimento por ID",
)
def get_fuel_log(log_id: str):
    """Busca um registro específico pelo seu identificador único."""
    log = get_log_by_id(log_id)
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Abastecimento com ID '{log_id}' não encontrado.",
        )
    return log
