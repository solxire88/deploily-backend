# -*- coding: utf-8 -*-
import json
from datetime import timedelta
from typing import Optional

import pytest
from flask_jwt_extended import create_access_token
from pydantic import BaseModel, ValidationError

support_ticket_data = {
    "title": "Test SupportTiket",
    "description": "This is a test of support ticket",
    "status": "open",
    "support_ticket_responses": [{"message": "ss1"}, {"message": "ss2"}],
}

updated_support_ticket_data = {"title": "Updated SupportTiket", "status": "closed"}


class SupportTiket(BaseModel):
    title: str
    description: str
    status: str
    image: Optional[str] = None
    support_ticket_responses: Optional[list] = []


class SupportTiketResponse(BaseModel):
    id: Optional[int] = None
    result: SupportTiket


class SupportTiketListResponse(BaseModel):
    count: int
    result: list[SupportTiket]


def test_create_supportticket(client, test_user, app, appbuilder):
    access_token = create_access_token(test_user.id, expires_delta=False, fresh=True)

    with app.app_context():
        from app.core.controllers.support_ticket_controllers import (
            SupportTicketModelApi,
        )

        appbuilder.add_api(SupportTicketModelApi)

        response = client.post(
            "/api/v1/support-ticket/",
            data=json.dumps(support_ticket_data),
            content_type="application/json",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 201
        try:
            SupportTiketResponse.model_validate_json(response.text)
        except ValidationError as e:
            pytest.fail(f"ValidationError occurred on POST SupportTiket : {e}")


def test_update_supportticket(client, test_user, app, appbuilder):
    access_token = create_access_token(test_user.id, expires_delta=False, fresh=True)

    with app.app_context():
        from app.core.controllers.support_ticket_controllers import (
            SupportTicketModelApi,
        )

        appbuilder.add_api(SupportTicketModelApi)

        response = client.put(
            f"/api/v1/support-ticket/{1}",
            data=json.dumps(updated_support_ticket_data),
            content_type="application/json",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        try:
            updated_service = SupportTiketResponse.model_validate_json(response.text)
        except ValidationError as e:
            pytest.fail(f"ValidationError occurred on PUT Service : {e}")

        assert updated_service.result.title == updated_support_ticket_data["title"]


def test_get_supportticket(client, test_user, app, appbuilder):
    access_token = create_access_token(test_user.id, expires_delta=False, fresh=True)

    with app.app_context():
        from app.core.controllers.support_ticket_controllers import (
            SupportTicketModelApi,
        )

        appbuilder.add_api(SupportTicketModelApi)

        response = client.get(
            "/api/v1/support-ticket/",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        try:
            SupportTiketListResponse.model_validate_json(response.text)
        except ValidationError as e:
            pytest.fail(f"ValidationError occurred on GET Service : {e}")


def test_delete_supportticket(client, test_user, app, appbuilder):
    access_token = create_access_token(test_user.id, expires_delta=False, fresh=True)

    with app.app_context():
        from app.core.controllers.support_ticket_controllers import (
            SupportTicketModelApi,
        )

        appbuilder.add_api(SupportTicketModelApi)

        response = client.delete(
            f"/api/v1/support-ticket/{1}",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200


def test_authenticated_access(client, test_user, app, appbuilder):
    access_token = create_access_token(test_user.id, expires_delta=False, fresh=True)

    with app.app_context():
        from app.core.controllers.support_ticket_controllers import (
            SupportTicketModelApi,
        )

        appbuilder.add_api(SupportTicketModelApi)

        response = client.get(
            "/api/v1/support-ticket/",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200


def test_unauthenticated_access(client, app, appbuilder):
    with app.app_context():
        from app.core.controllers.support_ticket_controllers import (
            SupportTicketModelApi,
        )

        appbuilder.add_api(SupportTicketModelApi)

        response = client.get(
            "/api/v1/support-ticket/",
            headers={},
        )

        assert response.status_code == 401


def test_token_expired(client, app, test_user, appbuilder):
    expired_access_token = create_access_token(test_user.id, expires_delta=timedelta(seconds=-1))

    with app.app_context():
        from app.core.controllers.support_ticket_controllers import (
            SupportTicketModelApi,
        )

        appbuilder.add_api(SupportTicketModelApi)

        response = client.get(
            "/api/v1/support-ticket/",
            headers={"Authorization": f"Bearer {expired_access_token}"},
        )

        assert response.status_code == 401
