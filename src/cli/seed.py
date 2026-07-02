import click
from flask.cli import with_appcontext

from seeders.plan_seeder import seed_plans
from seeders.service_plan_option_seeder import seed_service_plan_options
from seeders.service_plan_seeder import seed_service_plans
from seeders.services_seeder import seed_api_services
from seeders.versions_seeder import seed_versions


@click.group()
def seed():
    """Database seed commands"""


@seed.command("plans")
@with_appcontext
def seed_plans_command():
    seed_plans()
    click.echo("✅ Plans seeded successfully")


@seed.command("plan-options")
@with_appcontext
def seed_plan_options_command():
    seed_service_plan_options()
    click.echo("✅ Service plan options seeded")


@seed.command("service-plans")
@with_appcontext
def seed_service_plans_command():
    seed_service_plans()
    click.echo("✅ Service plan  seeded")


@seed.command("api-service")
@with_appcontext
def seed_api_service_command():
    seed_api_services()
    click.echo("✅ Service plan  seeded")


@seed.command("versions")
@with_appcontext
def seed_versions_command():
    seed_versions()
    click.echo("✅ Versions seeded")


@seed.command("all")
@with_appcontext
def all_seed():
    """Seed all database data"""
    seed_plans()
    seed_versions()
    seed_service_plan_options()
    seed_api_services()
    seed_service_plans()
    click.echo("🚀 All seeders executed successfully")
