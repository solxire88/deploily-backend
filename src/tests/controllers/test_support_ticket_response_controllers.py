# -*- coding: utf-8 -*-
import json
from datetime import timedelta
from typing import Optional, Union

import pytest
from flask_jwt_extended import create_access_token
from pydantic import BaseModel, ValidationError

support_ticket_response_data = {
    "message": "Test SupportTiketResponse",
    "support_ticket_id": 1,
}

updated_support_ticket_response_data = {"message": "Updated SupportTiketResponse"}


class UserSchema(BaseModel):
    id: int
    username: str


class SupportTiketResponse(BaseModel):
    message: str
    created_by: Optional[Union[int, UserSchema]] = None
    support_ticket_id: Optional[int] = None


class SupportTiketResponseResponse(BaseModel):
    id: Optional[int] = None
    result: SupportTiketResponse


class SupportTiketListResponse(BaseModel):
    count: int
    result: list[SupportTiketResponse]


def test_create_supportticketresponse(client, test_user, app, appbuilder):
    access_token = create_access_token(test_user.id, expires_delta=False, fresh=True)

    with app.app_context():
        from app.core.controllers.support_ticket_response_controllers import (
            SupportTicketResponseModelApi,
        )

        appbuilder.add_api(SupportTicketResponseModelApi)

        response = client.post(
            "/api/v1/support-ticket-response/",
            data=json.dumps(support_ticket_response_data),
            content_type="application/json",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 201
        try:
            SupportTiketResponseResponse.model_validate_json(response.text)
        except ValidationError as e:
            pytest.fail(f"ValidationError occurred on POST supportticketresponse : {e}")


def test_update_supportticket_response(client, test_user, app, appbuilder):
    access_token = create_access_token(test_user.id, expires_delta=False, fresh=True)

    with app.app_context():
        from app.core.controllers.support_ticket_response_controllers import (
            SupportTicketResponseModelApi,
        )

        appbuilder.add_api(SupportTicketResponseModelApi)

        response = client.put(
            f"/api/v1/support-ticket-response/{1}",
            data=json.dumps(updated_support_ticket_response_data),
            content_type="application/json",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        try:
            updated_supportticketresponse = SupportTiketResponseResponse.model_validate_json(
                response.text
            )
        except ValidationError as e:
            pytest.fail(f"ValidationError occurred on PUT supportticketresponse : {e}")

        assert (
            updated_supportticketresponse.result.message
            == updated_support_ticket_response_data["message"]
        )


def test_get_supportticket(client, test_user, app, appbuilder):
    access_token = create_access_token(test_user.id, expires_delta=False, fresh=True)

    with app.app_context():
        from app.core.controllers.support_ticket_response_controllers import (
            SupportTicketResponseModelApi,
        )

        appbuilder.add_api(SupportTicketResponseModelApi)

        response = client.get(
            "/api/v1/support-ticket-response/",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        try:
            SupportTiketListResponse.model_validate_json(response.text)
        except ValidationError as e:
            pytest.fail(f"ValidationError occurred on GET SupportTicketResponse : {e}")


def test_delete_supportticket(client, test_user, app, appbuilder):
    access_token = create_access_token(test_user.id, expires_delta=False, fresh=True)

    with app.app_context():
        from app.core.controllers.support_ticket_response_controllers import (
            SupportTicketResponseModelApi,
        )

        appbuilder.add_api(SupportTicketResponseModelApi)

        response = client.delete(
            f"/api/v1/support-ticket-response/{1}",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200


def test_authenticated_access(client, test_user, app, appbuilder):
    access_token = create_access_token(test_user.id, expires_delta=False, fresh=True)

    with app.app_context():
        from app.core.controllers.support_ticket_response_controllers import (
            SupportTicketResponseModelApi,
        )

        appbuilder.add_api(SupportTicketResponseModelApi)

        response = client.get(
            "/api/v1/support-ticket-response/",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200


def test_unauthenticated_access(client, app, appbuilder):
    with app.app_context():
        from app.core.controllers.support_ticket_response_controllers import (
            SupportTicketResponseModelApi,
        )

        appbuilder.add_api(SupportTicketResponseModelApi)

        response = client.get(
            "/api/v1/support-ticket-response/",
            headers={},
        )

        assert response.status_code == 401


def test_token_expired(client, app, test_user, appbuilder):
    expired_access_token = create_access_token(test_user.id, expires_delta=timedelta(seconds=-1))

    with app.app_context():
        from app.core.controllers.support_ticket_response_controllers import (
            SupportTicketResponseModelApi,
        )

        appbuilder.add_api(SupportTicketResponseModelApi)

        response = client.get(
            "/api/v1/support-ticket-response/",
            headers={"Authorization": f"Bearer {expired_access_token}"},
        )

        assert response.status_code == 401
