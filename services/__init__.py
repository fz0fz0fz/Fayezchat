from .governmental import handle as governmental
from .pharmacies import handle as pharmacies
from .grocery import handle as groceries  # ✅ تم التصحيح هنا
from .vegetables import handle as vegetables
from .trips import handle as trips
from .desserts import handle as desserts
from .home_businesses import handle as home_businesses
from .restaurants import handle as restaurants
from .stationery import handle as stationery
from .stores import handle as stores
from .chalets import handle as chalets
from .water_truck import handle as water_truck
from .shovel import handle as shovel
from .sand import handle as sand
from .building_materials import handle as building_materials
from .workers import handle as workers
from .shops import handle as shops
from .meat import handle as meat
from .school_transport import handle as school_transport
from .alarm import handle as alarm

services = {
    "1": governmental,
    "2": pharmacies,
    "3": groceries,
    "4": vegetables,
    "5": trips,
    "6": desserts,
    "7": home_businesses,
    "8": restaurants,
    "9": stationery,
    "10": stores,
    "11": chalets,
    "12": water_truck,
    "13": shovel,
    "14": sand,
    "15": building_materials,
    "16": workers,
    "17": shops,
    "18": meat,
    "19": school_transport,
    "20": alarm,
}
