"""
================================================================================
 File: orcaapi/app/graphql/schema.py
 Purpose:
   GraphQL integration surface for Orca. This sits alongside the REST API
   so external dashboards and integration clients can aggregate data through a
   single typed endpoint without duplicating service logic.
================================================================================
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

import strawberry
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from strawberry.fastapi import BaseContext, GraphQLRouter

from app.core.security import TokenPayload, require_role
from app.db.session import get_session
from app.schemas.control_plane import (
    ControlPlaneOverview,
    DataFlowStage,
    DeviceCategory,
    DeviceTrustLevel,
    ManagedDevice,
    OperatorControl,
    OperatorControlState,
    PipelineState,
    SecurityAlert,
    SecurityMonitorStatus,
)
from app.schemas.sensor import SensorKind, SensorReadingOut
from app.services.control_plane import control_plane_service
from app.services.ingestion import ingestion_service

SensorKindGQL = strawberry.enum(SensorKind, name="SensorKind")
DeviceCategoryGQL = strawberry.enum(DeviceCategory, name="DeviceCategory")
DeviceTrustLevelGQL = strawberry.enum(DeviceTrustLevel, name="DeviceTrustLevel")
OperatorControlStateGQL = strawberry.enum(OperatorControlState, name="OperatorControlState")
PipelineStateGQL = strawberry.enum(PipelineState, name="PipelineState")


@strawberry.type
class SensorReadingType:
    id: UUID
    sensor_id: str
    kind: SensorKindGQL
    value: float
    unit: str
    latitude: float | None
    longitude: float | None
    observed_at: datetime
    received_at: datetime
    metadata: strawberry.scalars.JSON


@strawberry.type
class ManagedDeviceType:
    id: str
    name: str
    category: DeviceCategoryGQL
    trust_level: DeviceTrustLevelGQL
    driver_container: str
    endpoint: str
    firmware_version: str
    authenticated: bool
    signed_driver: bool
    last_seen_at: datetime


@strawberry.type
class SecurityAlertType:
    id: str
    severity: str
    title: str
    status: str


@strawberry.type
class SecurityMonitorStatusType:
    encryption_status: str
    iam_status: str
    audit_pipeline_status: str
    quantum_safe_status: str
    intrusion_alerts: list[SecurityAlertType]


@strawberry.type
class DataFlowStageType:
    id: str
    name: str
    protocol: str
    state: PipelineStateGQL
    throughput_hint: str
    destination: str


@strawberry.type
class OperatorControlType:
    id: str
    name: str
    description: str
    state: OperatorControlStateGQL
    policy_mode: str
    action_label: str


@strawberry.type
class ControlPlaneOverviewType:
    devices: list[ManagedDeviceType]
    security: SecurityMonitorStatusType
    data_flow: list[DataFlowStageType]
    controls: list[OperatorControlType]


class GraphQLContext(BaseContext):
    def __init__(self, *, session: AsyncSession, user: TokenPayload) -> None:
        super().__init__()
        self.session = session
        self.user = user


ViewerUser = Annotated[TokenPayload, Depends(require_role("viewer"))]


async def build_context(
    session: AsyncSession = Depends(get_session),
    user: ViewerUser = None,
) -> GraphQLContext:
    return GraphQLContext(session=session, user=user)


def _sensor_reading_type(reading: SensorReadingOut) -> SensorReadingType:
    return SensorReadingType(**reading.model_dump())


def _managed_device_type(device: ManagedDevice) -> ManagedDeviceType:
    return ManagedDeviceType(**device.model_dump())


def _security_alert_type(alert: SecurityAlert) -> SecurityAlertType:
    return SecurityAlertType(**alert.model_dump())


def _security_status_type(status: SecurityMonitorStatus) -> SecurityMonitorStatusType:
    return SecurityMonitorStatusType(
        encryption_status=status.encryption_status,
        iam_status=status.iam_status,
        audit_pipeline_status=status.audit_pipeline_status,
        quantum_safe_status=status.quantum_safe_status,
        intrusion_alerts=[_security_alert_type(alert) for alert in status.intrusion_alerts],
    )


def _data_flow_stage_type(stage: DataFlowStage) -> DataFlowStageType:
    return DataFlowStageType(**stage.model_dump())


def _operator_control_type(control: OperatorControl) -> OperatorControlType:
    return OperatorControlType(**control.model_dump())


def _control_plane_overview_type(overview: ControlPlaneOverview) -> ControlPlaneOverviewType:
    return ControlPlaneOverviewType(
        devices=[_managed_device_type(device) for device in overview.devices],
        security=_security_status_type(overview.security),
        data_flow=[_data_flow_stage_type(stage) for stage in overview.data_flow],
        controls=[_operator_control_type(control) for control in overview.controls],
    )


@strawberry.type
class Query:
    @strawberry.field(
        description="Return recent sensor readings through the GraphQL integration surface"
    )
    async def recent_sensor_readings(
        self,
        info: strawberry.Info[GraphQLContext, Any],
        limit: int = 50,
    ) -> list[SensorReadingType]:
        bounded_limit = max(1, min(limit, 500))
        readings = list(ingestion_service.recent(limit=bounded_limit))
        return [_sensor_reading_type(reading) for reading in readings]

    @strawberry.field(description="Return the operator dashboard overview via GraphQL")
    async def control_plane_overview(
        self,
        info: strawberry.Info[GraphQLContext, Any],
    ) -> ControlPlaneOverviewType:
        overview = await control_plane_service.overview(info.context.session)
        return _control_plane_overview_type(overview)

    @strawberry.field(description="Echo the authenticated role used for this GraphQL request")
    async def viewer_role(self, info: strawberry.Info[GraphQLContext, Any]) -> str:
        return info.context.user.role


schema = strawberry.Schema(query=Query)
graphql_router = GraphQLRouter(schema=schema, context_getter=build_context)
