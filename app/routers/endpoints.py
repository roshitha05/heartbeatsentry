from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.monitor import check_endpoint


router = APIRouter(
    prefix="/endpoints",
    tags=["Endpoints"],
)


@router.post(
    "",
    response_model=schemas.EndpointResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_endpoint(
    endpoint: schemas.EndpointCreate,
    db: Session = Depends(get_db),
):
    existing_endpoint = (
        db.query(models.Endpoint)
        .filter(models.Endpoint.url == str(endpoint.url))
        .first()
    )

    if existing_endpoint:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Endpoint is already registered.",
        )

    new_endpoint = models.Endpoint(
        name=endpoint.name.strip(),
        url=str(endpoint.url),
    )

    db.add(new_endpoint)
    db.commit()
    db.refresh(new_endpoint)

    return new_endpoint


@router.get(
    "",
    response_model=list[schemas.EndpointResponse],
)
def get_endpoints(db: Session = Depends(get_db)):
    return (
        db.query(models.Endpoint)
        .order_by(models.Endpoint.id.desc())
        .all()
    )


@router.post(
    "/{endpoint_id}/check",
    response_model=schemas.CheckResponse,
)
def run_endpoint_check(
    endpoint_id: int,
    db: Session = Depends(get_db),
):
    endpoint = (
        db.query(models.Endpoint)
        .filter(models.Endpoint.id == endpoint_id)
        .first()
    )

    if endpoint is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Endpoint not found.",
        )

    result = check_endpoint(endpoint.url)

    check = models.CheckResult(
        endpoint_id=endpoint.id,
        status=result["status"],
        status_code=result["status_code"],
        response_time_ms=result["response_time_ms"],
        error=result["error"],
    )

    db.add(check)
    db.commit()
    db.refresh(check)

    return check


@router.get(
    "/{endpoint_id}/checks",
    response_model=list[schemas.CheckResponse],
)
def get_endpoint_checks(
    endpoint_id: int,
    db: Session = Depends(get_db),
):
    endpoint = (
        db.query(models.Endpoint)
        .filter(models.Endpoint.id == endpoint_id)
        .first()
    )

    if endpoint is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Endpoint not found.",
        )

    return (
        db.query(models.CheckResult)
        .filter(models.CheckResult.endpoint_id == endpoint_id)
        .order_by(models.CheckResult.checked_at.desc())
        .all()
    )


@router.get(
    "/{endpoint_id}/stats",
    response_model=schemas.EndpointStatsResponse,
)
def get_endpoint_stats(
    endpoint_id: int,
    db: Session = Depends(get_db),
):
    endpoint = (
        db.query(models.Endpoint)
        .filter(models.Endpoint.id == endpoint_id)
        .first()
    )

    if endpoint is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Endpoint not found.",
        )

    checks = (
        db.query(models.CheckResult)
        .filter(models.CheckResult.endpoint_id == endpoint_id)
        .order_by(models.CheckResult.checked_at.desc())
        .all()
    )

    total_checks = len(checks)

    successful_checks = sum(
        1 for check in checks if check.status == "healthy"
    )

    failed_checks = total_checks - successful_checks

    if total_checks > 0:
        uptime_percentage = round(
            (successful_checks / total_checks) * 100,
            2,
        )

        average_response_time_ms = round(
            sum(check.response_time_ms for check in checks) / total_checks,
            2,
        )

        latest_status = checks[0].status

    else:
        uptime_percentage = 0.0
        average_response_time_ms = 0.0
        latest_status = None

    return {
        "endpoint_id": endpoint.id,
        "endpoint_name": endpoint.name,
        "total_checks": total_checks,
        "successful_checks": successful_checks,
        "failed_checks": failed_checks,
        "uptime_percentage": uptime_percentage,
        "average_response_time_ms": average_response_time_ms,
        "latest_status": latest_status,
    }