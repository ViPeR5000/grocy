"""Grocy services."""
import asyncio
import voluptuous as vol
import iso8601
import logging

from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_component

from pygrocy import TransactionType
from datetime import datetime

from .const import DOMAIN

GROCY_SERVICES = "grocy_services"

SERVICE_PRODUCT_ID = "product_id"
SERVICE_AMOUNT = "amount"
SERVICE_PRICE = "price"
SERVICE_SPOILED = "spoiled"
SERVICE_TRANSACTION_TYPE = "transaction_type"
SERVICE_CHORE_ID = "chore_id"
SERVICE_TRACKED_TIME = "tracked_time"
SERVICE_DONE_BY = "done_by"
SERVICE_TASK_ID = "task_id"
SERVICE_DONE_TIME = "done_time"
SERVICE_ENTITY_TYPE = "entity_type"
SERVICE_DATA = "data"

SERVICE_ADD_PRODUCT = "add_product_to_stock"
SERVICE_CONSUME_PRODUCT = "consume_product_from_stock"
SERVICE_EXECUTE_CHORE = "execute_chore"
SERVICE_COMPLETE_TASK = "complete_task"
SERVICE_ADD_GENERIC = "add_generic"

SERVICE_ADD_PRODUCT_SCHEMA = vol.All(
    vol.Schema(
        {
            vol.Required(SERVICE_PRODUCT_ID): int,
            vol.Required(SERVICE_AMOUNT): int,
            vol.Optional(SERVICE_PRICE): str,
        }
    )
)

SERVICE_CONSUME_PRODUCT_SCHEMA = vol.All(
    vol.Schema(
        {
            vol.Required(SERVICE_PRODUCT_ID): int,
            vol.Required(SERVICE_AMOUNT): int,
            vol.Optional(SERVICE_SPOILED): bool,
            vol.Optional(SERVICE_TRANSACTION_TYPE): str,
        }
    )
)

SERVICE_EXECUTE_CHORE_SCHEMA = vol.All(
    vol.Schema(
        {
            vol.Required(SERVICE_CHORE_ID): int,
            vol.Optional(SERVICE_DONE_BY): int,
            vol.Optional(SERVICE_TRACKED_TIME): str,
        }
    )
)

SERVICE_COMPLETE_TASK_SCHEMA = vol.All(
    vol.Schema(
        {
            vol.Required(SERVICE_TASK_ID): int,
            vol.Optional(SERVICE_DONE_TIME): str,
        }
    )
)

SERVICE_ADD_GENERIC_SCHEMA = vol.All(
    vol.Schema(
        {
            vol.Required(SERVICE_ENTITY_TYPE): str,
            vol.Required(SERVICE_DATA): object,
        }
    )
)


async def async_setup_services(hass, entry):
    """Set up services for Grocy integration."""
    coordinator = hass.data[DOMAIN]
    if hass.data.get(GROCY_SERVICES, False):
        return

    hass.data[GROCY_SERVICES] = True

    async def async_call_grocy_service(service_call):
        """Call correct Grocy service."""
        service = service_call.service
        service_data = service_call.data

        if service == SERVICE_ADD_PRODUCT:
            await async_add_product_service(hass, coordinator, service_data)

        elif service == SERVICE_CONSUME_PRODUCT:
            await async_consume_product_service(hass, coordinator, service_data)

        elif service == SERVICE_EXECUTE_CHORE:
            await async_execute_chore_service(hass, coordinator, service_data)

        elif service == SERVICE_COMPLETE_TASK:
            await async_complete_task_service(hass, coordinator, service_data)

        elif service == SERVICE_ADD_GENERIC:
            await async_add_generic_service(hass, coordinator, service_data)

    hass.services.async_register(
        DOMAIN,
        SERVICE_ADD_PRODUCT,
        async_call_grocy_service,
        schema=SERVICE_ADD_PRODUCT_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_CONSUME_PRODUCT,
        async_call_grocy_service,
        schema=SERVICE_CONSUME_PRODUCT_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_EXECUTE_CHORE,
        async_call_grocy_service,
        schema=SERVICE_EXECUTE_CHORE_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_COMPLETE_TASK,
        async_call_grocy_service,
        schema=SERVICE_COMPLETE_TASK_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_ADD_GENERIC,
        async_call_grocy_service,
        schema=SERVICE_ADD_GENERIC_SCHEMA,
    )


async def async_unload_services(hass):
    """Unload Grocy services."""
    if not hass.data.get(GROCY_SERVICES):
        return

    hass.data[GROCY_SERVICES] = False

    hass.services.async_remove(DOMAIN, SERVICE_ADD_PRODUCT)
    hass.services.async_remove(DOMAIN, SERVICE_CONSUME_PRODUCT)
    hass.services.async_remove(DOMAIN, SERVICE_EXECUTE_CHORE)
    hass.services.async_remove(DOMAIN, SERVICE_COMPLETE_TASK)


async def async_add_product_service(hass, coordinator, data):
    """Add a product in Grocy."""
    product_id = data[SERVICE_PRODUCT_ID]
    amount = data[SERVICE_AMOUNT]
    price = data.get(SERVICE_PRICE, "")

    coordinator.api.add_product(product_id, amount, price)


async def async_consume_product_service(hass, coordinator, data):
    """Consume a product in Grocy."""
    product_id = data[SERVICE_PRODUCT_ID]
    amount = data[SERVICE_AMOUNT]
    spoiled = data.get(SERVICE_SPOILED, False)

    transaction_type_raw = data.get(SERVICE_TRANSACTION_TYPE, None)
    transaction_type = TransactionType.CONSUME

    if transaction_type_raw is not None:
        transaction_type = TransactionType[transaction_type_raw]
    coordinator.api.consume_product(
        product_id, amount, spoiled=spoiled, transaction_type=transaction_type
    )


async def async_execute_chore_service(hass, coordinator, data):
    """Execute a chore in Grocy."""
    chore_id = data[SERVICE_CHORE_ID]
    done_by = data.get(SERVICE_DONE_BY, "")
    tracked_time_str = data.get(SERVICE_TRACKED_TIME, "")

    tracked_time = datetime.now()
    if tracked_time_str is not None and tracked_time_str != "":
        tracked_time = iso8601.parse_date(tracked_time_str)

    coordinator.api.execute_chore(chore_id, done_by, tracked_time)
    asyncio.run_coroutine_threadsafe(
        entity_component.async_update_entity(hass, "sensor.grocy_chores"), hass.loop
    )


async def async_complete_task_service(hass, coordinator, data):
    """Complete a task in Grocy."""
    task_id = data[SERVICE_TASK_ID]
    done_time_str = data.get(SERVICE_DONE_TIME, None)

    done_time = datetime.now()
    if done_time_str is not None and done_time_str != "":
        done_time = iso8601.parse_date(done_time_str)

    coordinator.api.complete_task(task_id, done_time)
    asyncio.run_coroutine_threadsafe(
        entity_component.async_update_entity(hass, "sensor.grocy_tasks"), hass.loop
    )


async def async_add_generic_service(hass, coordinator, data):
    """Add a generic entity in Grocy."""
    entity_type = data[SERVICE_ENTITY_TYPE]
    data = data[SERVICE_DATA]

    coordinator.api.add_generic(entity_type, data)
