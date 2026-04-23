MAP_SLUGS = {
    "Azarov's Resting Place": "azarovs-resting-place",
    "Blood Lodge": "blood-lodge",
    "Gas Heaven": "gas-heaven",
    "Wreckers' Yard": "wreckers-yard",
    "Wretched Shop": "wretched-shop",

    "Badham Preschool I": "badham-preschool-i",
    "Badham Preschool II": "badham-preschool-ii",
    "Badham Preschool III": "badham-preschool-iii",
    "Badham Preschool IV": "badham-preschool-iv",
    "Badham Preschool V": "badham-preschool-v",

    "Fractured Cowshed": "fractured-cowshed",
    "Rancid Abattoir": "rancid-abattoir",
    "Rotten Fields": "rotten-fields",
    "Thompson House": "thompson-house",
    "Torment Creek": "torment-creek",

    "Disturbed Ward": "disturbed-ward",
    "Father Campbell's Chapel": "father-campbells-chapel",

    "Nostromo Wreckage": "nostromo-wreckage",
    "Toba Landing": "toba-landing",

    "Dead Sands": "dead-sands",
    "Eyrie of Crows": "eyrie-of-crows",

    "Coal Tower I": "coal-tower-i",
    "Coal Tower II": "coal-tower-ii",
    "Groaning Storehouse I": "groaning-storehouse-i",
    "Groaning Storehouse II": "groaning-storehouse-ii",
    "Ironworks of Misery I": "ironworks-of-misery-i",
    "Ironworks of Misery II": "ironworks-of-misery-ii",
    "Shelter Woods I": "shelter-woods-i",
    "Shelter Woods II": "shelter-woods-ii",
    "Suffocation Pit I": "suffocation-pit-i",
    "Suffocation Pit II": "suffocation-pit-ii",

    "Mount Ormond Resort I": "mount-ormond-resort-i",
    "Mount Ormond Resort II": "mount-ormond-resort-ii",
    "Mount Ormond Resort III": "mount-ormond-resort-iii",
    "Ormond Lake Mine": "ormond-lake-mine",

    "Dead Dawg Saloon": "dead-dawg-saloon",
    "Haddonfield": "haddonfield",
    "Hawkins National Laboratory": "hawkins-national-laboratory",
    "Lery's Memorial Institute": "lerys-memorial-institute",
    "Midwich Elementary School": "midwich-elementary-school",
    "The Game": "the-game",

    "Raccoon City Police Station East Wing": "raccoon-city-police-station-east-wing",
    "Raccoon City Police Station West Wing": "raccoon-city-police-station-west-wing",

    "Mother's Dwelling": "mothers-dwelling",
    "Temple of Purgation": "temple-of-purgation",

    "Trickster's Delusion": "tricksters-delusion",

    "Grim Pantry": "grim-pantry",
    "Pale Rose": "pale-rose",

    "Forgotten Ruins": "forgotten-ruins",
    "Shattered Square": "shattered-square",

    "Fallen Refuge": "fallen-refuge",
    "Freddy Fazbear's Pizza": "freddy-fazbears-pizza",
    "Garden of Joy": "garden-of-joy",
    "Greenville Square": "greenville-square",

    "Family Residence": "family-residence",
    "Sanctum of Wrath": "sanctum-of-wrath",
}

KNOWN_MAPS = list(MAP_SLUGS.keys())

ALIASES = {
    "TOBA LANDING": "Toba Landing",
    "DVARKA DEEPWOOD TOBA LANDING": "Toba Landing",
    "DVARKA DEEPWOOD TOBALANDING": "Toba Landing",

    "WITHERED ISLE GREENVILLE SQUARE": "Greenville Square",
    "WITHERED ISLE GARDEN OF JOY": "Garden of Joy",

    "ORMOND MOUNT ORMOND RESORT": "Mount Ormond Resort I",
    "AZAROVS RESTING PLACE": "Azarov's Resting Place",
    "AZAROV S RESTING PLACE": "Azarov's Resting Place",
    "WRECKERS": "Wreckers' Yard",
    "WRECKERS YARD": "Wreckers' Yard",

    "COAL TOWER": "Coal Tower I",
    "COAL TOWER 1": "Coal Tower I",
    "COAL TOWER I": "Coal Tower I",
    "COAL TOWER L": "Coal Tower I",
    "COAL TOWER 11": "Coal Tower II",
    "COAL TOWER 2": "Coal Tower II",
    "COAL TOWER II": "Coal Tower II",

    "GROANING STOREHOUSE": "Groaning Storehouse I",
    "GROANING STOREHOUSE 1": "Groaning Storehouse I",
    "GROANING STOREHOUSE I": "Groaning Storehouse I",
    "GROANING STOREHOUSE 11": "Groaning Storehouse II",
    "GROANING STOREHOUSE 2": "Groaning Storehouse II",
    "GROANING STOREHOUSE II": "Groaning Storehouse II",

    "IRONWORKS OF MISERY": "Ironworks of Misery I",
    "IRONWORKS OF MISERY 1": "Ironworks of Misery I",
    "IRONWORKS OF MISERY I": "Ironworks of Misery I",
    "IRONWORKS OF MISERY 11": "Ironworks of Misery II",
    "IRONWORKS OF MISERY 2": "Ironworks of Misery II",
    "IRONWORKS OF MISERY II": "Ironworks of Misery II",

    "SHELTER WOODS": "Shelter Woods I",
    "SHELTER WOODS 1": "Shelter Woods I",
    "SHELTER WOODS I": "Shelter Woods I",
    "SHELTER WOODS 11": "Shelter Woods II",
    "SHELTER WOODS 2": "Shelter Woods II",
    "SHELTER WOODS II": "Shelter Woods II",

    "SUFFOCATION PIT": "Suffocation Pit I",
    "SUFFOCATION PIT 1": "Suffocation Pit I",
    "SUFFOCATION PIT I": "Suffocation Pit I",
    "SUFFOCATION PIT 11": "Suffocation Pit II",
    "SUFFOCATION PIT 2": "Suffocation Pit II",
    "SUFFOCATION PIT II": "Suffocation Pit II",

    "FATHER CAMPBELLS CHAPEL": "Father Campbell's Chapel",
    "FATHER CAMPBELL S CHAPEL": "Father Campbell's Chapel",

    "DEAD DOG SALOON": "Dead Dawg Saloon",
    "DEAD DAWG SALOON": "Dead Dawg Saloon",

    "THE THOMPSON HOUSE": "Thompson House",
    "THOMPSON HOUSE": "Thompson House",

    "RANCID ABBATOIR": "Rancid Abattoir",
    "RANCID ABATTOIR": "Rancid Abattoir",

    "ORMOND": "Mount Ormond Resort I",
    "ORMOND II": "Mount Ormond Resort II",
    "ORMOND III": "Mount Ormond Resort III",
    "ORMOND LAKE MINE": "Ormond Lake Mine",

    "MIDWICH": "Midwich Elementary School",
    "MIDWICH ELEMENTARY SCHOOL": "Midwich Elementary School",

    "LERYS": "Lery's Memorial Institute",
    "LERYS MEMORIAL INSTITUTE": "Lery's Memorial Institute",

    "RPD EAST WING": "Raccoon City Police Station East Wing",
    "RPD WEST WING": "Raccoon City Police Station West Wing",

    "THE SHATTERED SQUARE": "Shattered Square",
    "SHATTERED SQUARE": "Shattered Square",

    "MOTHERS DWELLING": "Mother's Dwelling",
    "MOTHER S DWELLING": "Mother's Dwelling",

    "PALE ROSE": "Pale Rose",
    "GRIM PANTRY": "Grim Pantry",
    "NOSTROMO WRECKAGE": "Nostromo Wreckage",
    "GREENVILLE SQUARE": "Greenville Square",
    "FORGOTTEN RUINS": "Forgotten Ruins",
    "THE GAME": "The Game",
    "GARDEN OF JOY": "Garden of Joy",
    "EYRIE OF CROWS": "Eyrie of Crows",
    "TEMPLE OF PURGATION": "Temple of Purgation",
    "FAMILY RESIDENCE": "Family Residence",
    "SANCTUM OF WRATH": "Sanctum of Wrath",
    "HADDONFIELD": "Haddonfield",
    "HAWKINS": "Hawkins National Laboratory",
    "TOBA LANDING": "Toba Landing",
    "DEAD SANDS": "Dead Sands",
    "FALLEN REFUGE": "Fallen Refuge",
    "FREDDY FAZBEARS PIZZA": "Freddy Fazbear's Pizza",
    "TRICKSTERS DELUSION": "Trickster's Delusion",
}