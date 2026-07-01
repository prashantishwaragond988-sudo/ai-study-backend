import logging

from flask import Blueprint, current_app

from app.common.responses import success_response
from app.services.firestore_service import FirestoreService

logger = logging.getLogger(__name__)
firestore_bp = Blueprint("firestore", __name__)


@firestore_bp.get("/firestore-test")
def firestore_test():
    firestore_service = FirestoreService()
    document = firestore_service.write_and_read_test_document()
    logger.info(
        "Firestore test completed for document %s.",
        document["id"],
    )
    return success_response(
        {
            "status": "firestore_connected",
            "projectId": current_app.config["FIREBASE_PROJECT_ID"],
            "collection": "test",
            "document": document,
        }
    )
