# services/__init__.py

from .governmental import handle as governmental
from .pharmacies import handle as pharmacies
from .grocery import handle as grocery
from .vegetables import handle as vegetables
from .trips import handle as trips
from .desserts import handle as desserts
from .home_businesses import handle as home_businesses
from .restaurants import handle as restaurants
from .stationery import handle as stationery
from .shops import handle as shops
from .chalets import handle as chalets
from .water_truck import handle as water
from .shovel import handle as shovel
from .sand import handle as sand
from .building_materials import handle as building_materials
from .workers import handle as workers
from .stores import handle as stores
from .butchers import handle as butchers
from .transport import handle as school_transport
from .reminder import handle as reminder

__all__ = [
    "governmental", "pharmacies", "grocery", "vegetables", "trips", "desserts",
    "home_businesses", "restaurants", "stationery", "shops", "chalets", "water",
    "shovel", "sand", "building_materials", "workers", "stores", "butchers",
    "school_transport", "reminder"
]
