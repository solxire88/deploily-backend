# -*- coding: utf-8 -*-

from flask import request
from flask_appbuilder.api import BaseApi, expose
from flask_appbuilder.models.sqla.interface import SQLAInterface
from sqlalchemy import or_

from app import appbuilder, db
from app.core.controllers.service_controllers import ServiceModelApi
from app.service_apps.models.apps_services_model import AppService

api_columns = [
    "average_rating",
    "recommended_apps",
    "min_app_price",
    "minimal_cpu",
    "minimal_ram",
    "minimal_disk",
    "app_versions",
    "is_subscribed",
    "sequence",
    "demo_url",
]


class AppServiceModelApi(ServiceModelApi):
    resource_name = "app-service"
    datamodel = SQLAInterface(AppService)

    add_columns = ServiceModelApi.add_columns + api_columns
    list_columns = ServiceModelApi.list_columns + api_columns
    show_columns = ServiceModelApi.show_columns + api_columns
    edit_columns = ServiceModelApi.edit_columns + api_columns
    base_order = ("sequence", "asc")

    @expose("/all", methods=["GET"])
    def get_all_app_services(self):
        """
        ---
        get:
          summary: Get all APP services (base fields + service_plans + medias)
          description: Returns a list of AppService with name, short_description, description, service_plans and medias
          parameters:
            - in: query
              name: search_value
              schema:
                type: string
              required: false
          responses:
            200:
              description: List of AppServices
              content:
                application/json:
                  schema:
                    type: array
                    items:
                      type: object
                      properties:
                        name:
                          type: string
                        short_description:
                          type: string
                        description:
                          type: string
                        service_plans:
                          type: array
                          items:
                            type: object
                            additionalProperties: true
                        medias:
                          type: array
                          items:
                            type: object
                            additionalProperties: true
            500:
              description: Internal server error
        """
        # services = db.session.query(AppService).all()

        search_value = request.args.get("search_value")
        query = db.session.query(AppService)
        if search_value:
            query = query.filter(
                or_(
                    AppService.name.ilike(f"%{search_value}%"),
                    AppService.description.ilike(f"%{search_value}%"),
                )
            )

        # services = query.all()
        services = (
            query.filter(AppService.is_published.is_(True))
            .order_by(AppService.sequence.asc())
            .all()
        )

        def serialize_service(service):
            return {
                "id": service.id,
                "name": service.name,
                "price_category": service.price_category,
                "short_description": service.short_description,
                "image_service": service.image_service,
                "service_slug": service.service_slug,
                "unit_price": service.unit_price,
            }

        result = [serialize_service(s) for s in services]
        return self.response(200, result=result)


appbuilder.add_api(AppServiceModelApi)


class PublicAppServiceApi(BaseApi):  # public version
    resource_name = "app-service-public"

    @expose("/<int:id>", methods=["GET"])
    def get_app_service_by_id(self, id):  # <- Use the captured `id` parameter
        """
        ---
        get:
          summary: Get an APP service by ID (base fields + service_plans + medias)
          description: Returns a specific AppService with name, short_description, description, service_plans and medias
          parameters:
            - in: path
              name: id
              required: true
              schema:
                type: integer
          responses:
            200:
              description: AppService found
              content:
                application/json:
                  schema:
                    type: object
                    properties:
                      name:
                        type: string
                      short_description:
                        type: string
                      description:
                        type: string
                      service_plans:
                        type: array
                        items:
                          type: object
                          additionalProperties: true
                      medias:
                        type: array
                        items:
                          type: object
                          additionalProperties: true
            404:
              description: AppService not found
            500:
              description: Internal server error
        """
        service = db.session.query(AppService).get(id)
        if not service:
            return self.response(404, message="AppService not found")

        def serialize_service(service):
            return {
                "name": service.name,
                "price_category": service.price_category,
                "short_description": service.short_description,
                "description": service.description,
                "image_service": service.image_service,
                "specifications": service.specifications,
                "documentation_url": service.documentation_url,
                "demo_url": service.demo_url,
                "minimal_cpu": service.minimal_cpu,
                "minimal_ram": service.minimal_ram,
                "minimal_disk": service.minimal_disk,
                "service_slug": service.service_slug,
                "is_subscribed": service.is_subscribed,
                "app_versions": [
                    {"id": app.id, "version": app.name, "description": app.description}
                    for app in service.app_versions
                ],
                "average_rating": service.average_rating,
                "recommended_apps": [{"id": app.id} for app in service.recommended_apps],
                "service_plans": [
                    {
                        "id": plan.id,
                        "price": plan.price,
                        "name": plan.plan.name,
                        "subscription_category": plan.subscription_category,
                        "is_custom": plan.is_custom,
                        "options": [
                            {
                                "id": option.id,
                                "option_type": option.option_type,
                                "option_value": option.option_value,
                                "icon": option.icon,
                                "html_content": option.html_content,
                                "sequence": option.sequence,
                            }
                            for option in plan.options
                        ],
                        "preparation_time": plan.preparation_time,
                    }
                    for plan in sorted(service.service_plans, key=lambda p: p.price or 0)
                ],
                "medias": [
                    {
                        "id": media.id,
                        "name": media.title,
                        "image": media.image,
                    }
                    for media in service.medias
                ],
            }

        result = serialize_service(service)
        return self.response(200, result=result)

    @expose("/<string:slug>", methods=["GET"])
    def get_app_service_by_slug(self, slug):
        """
        ---
        get:
          summary: Get an APP service by slug (base fields + service_plans + medias)
          description: Returns a specific AppService by service_slug
          parameters:
            - in: path
              name: slug
              required: true
              schema:
                type: string
          responses:
            200:
              description: AppService found
            404:
              description: AppService not found
        """
        service = db.session.query(AppService).filter_by(service_slug=slug).first()
        if not service:
            return self.response(404, message="AppService not found")

        result = self.serialize_service(service)
        return self.response(200, result=result)

    def serialize_service(self, service):
        return {
            "id": service.id,
            "name": service.name,
            "price_category": service.price_category,
            "short_description": service.short_description,
            "description": service.description,
            "image_service": service.image_service,
            "specifications": service.specifications,
            "documentation_url": service.documentation_url,
            "demo_url": service.demo_url,
            "minimal_cpu": service.minimal_cpu,
            "minimal_ram": service.minimal_ram,
            "minimal_disk": service.minimal_disk,
            "service_slug": service.service_slug,
            "is_subscribed": service.is_subscribed,
            "app_versions": [
                {"id": app.id, "version": app.name, "description": app.description}
                for app in service.app_versions
            ],
            "average_rating": service.average_rating,
            "recommended_apps": [{"id": app.id} for app in service.recommended_apps],
            "service_plans": [
                {
                    "id": plan.id,
                    "price": plan.price,
                    "name": plan.plan.name,
                    "subscription_category": plan.subscription_category,
                    "is_custom": plan.is_custom,
                    "is_trial": plan.is_trial,
                    "options": [
                        {
                            "id": option.id,
                            "option_type": option.option_type,
                            "option_value": option.option_value,
                            "icon": option.icon,
                            "html_content": option.html_content,
                            "sequence": option.sequence,
                        }
                        for option in plan.options
                    ],
                    "preparation_time": plan.preparation_time,
                }
                for plan in sorted(
                    [p for p in service.service_plans if p.is_published],
                    key=lambda p: p.priority or 0,
                )
            ],
            "medias": [
                {
                    "id": media.id,
                    "name": media.title,
                    "image": media.image,
                }
                for media in service.medias
            ],
        }


# Register the API with Flask AppBuilder
appbuilder.add_api(PublicAppServiceApi)
