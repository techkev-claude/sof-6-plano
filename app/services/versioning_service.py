import jsonpatch
import structlog

from app.extensions import db
from app.models import PlanVersion, Trip

log = structlog.get_logger()

SUB_VERSION_CLEANUP_AFTER_N_MAJOR = 2


def create_major_version(trip_id: int, user_id: int, message: str = "") -> PlanVersion:
    trip = db.session.get(Trip, trip_id)
    if not trip:
        raise ValueError(f"Trip {trip_id} not found")

    existing_major_count = PlanVersion.query.filter_by(trip_id=trip_id, is_major=True).count()
    version_string = f"{existing_major_count + 1}.0.0"

    version = PlanVersion(
        trip_id=trip_id,
        created_by_id=user_id,
        version_string=version_string,
        is_major=True,
        commit_message=message,
    )
    version.set_snapshot(trip.to_snapshot_dict())
    db.session.add(version)
    db.session.flush()

    _cleanup_old_sub_versions(trip_id, version.id)

    log.info("major_version_created", trip_id=trip_id, version=version_string)
    return version


def create_sub_version(trip_id: int, user_id: int) -> PlanVersion:
    trip = db.session.get(Trip, trip_id)
    if not trip:
        raise ValueError(f"Trip {trip_id} not found")

    parent_major = (
        PlanVersion.query.filter_by(trip_id=trip_id, is_major=True)
        .order_by(PlanVersion.id.desc())
        .first()
    )
    if not parent_major:
        return create_major_version(trip_id, user_id, "Auto-gespeichert")

    parent_snapshot = parent_major.get_snapshot() or {}
    current_snapshot = trip.to_snapshot_dict()

    try:
        patch = jsonpatch.make_patch(parent_snapshot, current_snapshot)
        patch_list = list(patch)
    except Exception as e:
        log.warning("patch_creation_failed", error=str(e))
        patch_list = []

    sub_count = PlanVersion.query.filter_by(
        trip_id=trip_id, is_major=False, parent_major_id=parent_major.id
    ).count()
    version_string = f"{parent_major.version_string.split('.')[0]}.0.{sub_count + 1}"

    version = PlanVersion(
        trip_id=trip_id,
        created_by_id=user_id,
        version_string=version_string,
        is_major=False,
        parent_major_id=parent_major.id,
        patch_data=patch_list,
    )
    db.session.add(version)
    log.info("sub_version_created", trip_id=trip_id, version=version_string)
    return version


def reconstruct_version(plan_version_id: int) -> dict | None:
    version = db.session.get(PlanVersion, plan_version_id)
    if not version:
        return None

    if version.is_major:
        return version.get_snapshot()

    parent = db.session.get(PlanVersion, version.parent_major_id)
    if not parent:
        return None

    base = parent.get_snapshot()
    if not base:
        return None

    try:
        patch = jsonpatch.JsonPatch(version.patch_data or [])
        return patch.apply(base)
    except Exception as e:
        log.error("reconstruct_failed", version_id=plan_version_id, error=str(e))
        return base


def _cleanup_old_sub_versions(trip_id: int, new_major_id: int):
    majors = (
        PlanVersion.query.filter_by(trip_id=trip_id, is_major=True)
        .order_by(PlanVersion.id.asc())
        .all()
    )
    if len(majors) <= SUB_VERSION_CLEANUP_AFTER_N_MAJOR:
        return

    old_majors = majors[: -(SUB_VERSION_CLEANUP_AFTER_N_MAJOR)]
    for major in old_majors:
        deleted = PlanVersion.query.filter_by(
            trip_id=trip_id, is_major=False, parent_major_id=major.id
        ).delete()
        if deleted:
            log.info("sub_versions_cleaned", major_id=major.id, count=deleted)
