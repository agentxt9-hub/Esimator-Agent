# seed_csi.py — Run this once to populate CSI division data in the database.
# From the VS Code terminal: python .\seed_csi.py

from app import app, db, CSILevel1, CSILevel2

# ─────────────────────────────────────────
# CSI MASTERFORMAT LEVEL 1 DIVISIONS
# ─────────────────────────────────────────

DIVISIONS = [
    ('00', 'Procurement and Contracting Requirements'),
    ('01', 'General Requirements'),
    ('02', 'Existing Conditions'),
    ('03', 'Concrete'),
    ('04', 'Masonry'),
    ('05', 'Metals'),
    ('06', 'Wood, Plastics, and Composites'),
    ('07', 'Thermal and Moisture Protection'),
    ('08', 'Openings'),
    ('09', 'Finishes'),
    ('10', 'Specialties'),
    ('11', 'Equipment'),
    ('12', 'Furnishings'),
    ('13', 'Special Construction'),
    ('14', 'Conveying Equipment'),
    ('21', 'Fire Suppression'),
    ('22', 'Plumbing'),
    ('23', 'Heating, Ventilating, and Air Conditioning (HVAC)'),
    ('26', 'Electrical'),
    ('27', 'Communications'),
    ('28', 'Electronic Safety and Security'),
    ('31', 'Earthwork'),
    ('32', 'Exterior Improvements'),
    ('33', 'Utilities'),
    ('34', 'Transportation'),
]

# ─────────────────────────────────────────
# CSI MASTERFORMAT LEVEL 2 SECTIONS
# Keyed by Level 1 code → list of (section_code, title)
# ─────────────────────────────────────────

SECTIONS = {
    '01': [
        ('01 10 00', 'Summary'),
        ('01 20 00', 'Price and Payment Procedures'),
        ('01 30 00', 'Administrative Requirements'),
        ('01 40 00', 'Quality Requirements'),
        ('01 50 00', 'Temporary Facilities and Controls'),
        ('01 60 00', 'Product Requirements'),
        ('01 70 00', 'Execution and Closeout Requirements'),
        ('01 80 00', 'Performance Requirements'),
    ],
    '02': [
        ('02 20 00', 'Assessment'),
        ('02 30 00', 'Subsurface Investigation'),
        ('02 40 00', 'Demolition and Structure Moving'),
        ('02 50 00', 'Site Remediation'),
        ('02 60 00', 'Contaminated Site Material Removal'),
        ('02 70 00', 'Water Remediation'),
        ('02 80 00', 'Facility Remediation'),
    ],
    '03': [
        ('03 10 00', 'Concrete Forming and Accessories'),
        ('03 15 00', 'Concrete Accessories'),
        ('03 20 00', 'Concrete Reinforcing'),
        ('03 30 00', 'Cast-in-Place Concrete'),
        ('03 35 00', 'Concrete Finishing'),
        ('03 37 00', 'Specialty Placed Concrete'),
        ('03 40 00', 'Precast Concrete'),
        ('03 45 00', 'Precast Architectural Concrete'),
        ('03 50 00', 'Cast Decks and Underlayment'),
        ('03 60 00', 'Grouting'),
        ('03 70 00', 'Mass Concrete'),
    ],
    '04': [
        ('04 20 00', 'Unit Masonry'),
        ('04 21 00', 'Clay Unit Masonry'),
        ('04 22 00', 'Concrete Unit Masonry'),
        ('04 40 00', 'Stone Assemblies'),
        ('04 50 00', 'Refractory Masonry'),
        ('04 60 00', 'Corrosion-Resistant Masonry'),
        ('04 70 00', 'Manufactured Masonry'),
    ],
    '05': [
        ('05 10 00', 'Structural Metal Framing'),
        ('05 12 00', 'Structural Steel Framing'),
        ('05 20 00', 'Metal Joists'),
        ('05 30 00', 'Metal Decking'),
        ('05 40 00', 'Cold-Formed Metal Framing'),
        ('05 50 00', 'Metal Fabrications'),
        ('05 51 00', 'Metal Stairs'),
        ('05 52 00', 'Metal Railings'),
        ('05 70 00', 'Decorative Metal'),
    ],
    '06': [
        ('06 10 00', 'Rough Carpentry'),
        ('06 11 00', 'Wood Framing'),
        ('06 16 00', 'Sheathing'),
        ('06 17 00', 'Shop-Fabricated Structural Wood'),
        ('06 20 00', 'Finish Carpentry'),
        ('06 22 00', 'Millwork'),
        ('06 40 00', 'Architectural Woodwork'),
        ('06 50 00', 'Structural Plastics'),
        ('06 60 00', 'Plastic Fabrications'),
    ],
    '07': [
        ('07 10 00', 'Dampproofing and Waterproofing'),
        ('07 11 00', 'Dampproofing'),
        ('07 13 00', 'Sheet Waterproofing'),
        ('07 14 00', 'Fluid-Applied Waterproofing'),
        ('07 20 00', 'Thermal Protection'),
        ('07 21 00', 'Thermal Insulation'),
        ('07 25 00', 'Weather Barriers'),
        ('07 30 00', 'Steep Slope Roofing'),
        ('07 31 00', 'Shingles and Shakes'),
        ('07 40 00', 'Roofing and Siding Panels'),
        ('07 50 00', 'Membrane Roofing'),
        ('07 54 00', 'Thermoplastic Membrane Roofing'),
        ('07 60 00', 'Flashing and Sheet Metal'),
        ('07 70 00', 'Roof and Wall Specialties and Accessories'),
        ('07 80 00', 'Fire and Smoke Protection'),
        ('07 90 00', 'Joint Protection'),
        ('07 92 00', 'Joint Sealants'),
    ],
    '08': [
        ('08 10 00', 'Doors and Frames'),
        ('08 11 00', 'Metal Doors and Frames'),
        ('08 14 00', 'Wood Doors'),
        ('08 30 00', 'Specialty Doors and Frames'),
        ('08 40 00', 'Entrances, Storefronts, and Curtain Walls'),
        ('08 41 00', 'Entrances and Storefronts'),
        ('08 44 00', 'Curtain Wall and Glazed Assemblies'),
        ('08 50 00', 'Windows'),
        ('08 51 00', 'Metal Windows'),
        ('08 60 00', 'Roof Windows and Skylights'),
        ('08 70 00', 'Hardware'),
        ('08 71 00', 'Door Hardware'),
        ('08 80 00', 'Glazing'),
        ('08 90 00', 'Louvers and Vents'),
    ],
    '09': [
        ('09 20 00', 'Plaster and Gypsum Board'),
        ('09 21 00', 'Gypsum Board Assemblies'),
        ('09 22 00', 'Supports for Plaster and Gypsum Board'),
        ('09 29 00', 'Gypsum Board'),
        ('09 30 00', 'Tiling'),
        ('09 50 00', 'Ceilings'),
        ('09 51 00', 'Acoustical Ceilings'),
        ('09 60 00', 'Flooring'),
        ('09 64 00', 'Wood Flooring'),
        ('09 65 00', 'Resilient Flooring'),
        ('09 67 00', 'Fluid-Applied Flooring'),
        ('09 68 00', 'Carpeting'),
        ('09 69 00', 'Access Flooring'),
        ('09 70 00', 'Wall Finishes'),
        ('09 72 00', 'Wall Coverings'),
        ('09 90 00', 'Paints and Coatings'),
        ('09 91 00', 'Painting'),
    ],
    '21': [
        ('21 10 00', 'Water-Based Fire Suppression Systems'),
        ('21 11 00', 'Facility Fire Suppression Water-Service Piping'),
        ('21 12 00', 'Fire Suppression Standpipes'),
        ('21 13 00', 'Wet-Pipe Sprinkler Systems'),
        ('21 20 00', 'Fire Extinguishing Systems'),
        ('21 30 00', 'Fire Pumps'),
    ],
    '22': [
        ('22 05 00', 'Common Work Results for Plumbing'),
        ('22 10 00', 'Plumbing Piping and Pumps'),
        ('22 11 00', 'Facility Water Distribution'),
        ('22 13 00', 'Facility Sanitary Sewerage'),
        ('22 14 00', 'Facility Storm Drainage'),
        ('22 30 00', 'Plumbing Equipment'),
        ('22 40 00', 'Plumbing Fixtures'),
        ('22 41 00', 'Residential Plumbing Fixtures'),
        ('22 42 00', 'Commercial Plumbing Fixtures'),
        ('22 50 00', 'Pool and Fountain Plumbing Systems'),
    ],
    '23': [
        ('23 05 00', 'Common Work Results for HVAC'),
        ('23 07 00', 'HVAC Insulation'),
        ('23 09 00', 'Instrumentation and Control for HVAC'),
        ('23 20 00', 'HVAC Piping and Pumps'),
        ('23 30 00', 'HVAC Air Distribution'),
        ('23 31 00', 'HVAC Ducts and Casings'),
        ('23 34 00', 'HVAC Fans'),
        ('23 37 00', 'Air Outlets and Inlets'),
        ('23 40 00', 'HVAC Air Cleaning Devices'),
        ('23 50 00', 'Central Heating Equipment'),
        ('23 60 00', 'Central Cooling Equipment'),
        ('23 70 00', 'Central HVAC Equipment'),
        ('23 80 00', 'Decentralized HVAC Equipment'),
    ],
    '26': [
        ('26 05 00', 'Common Work Results for Electrical'),
        ('26 05 19', 'Low-Voltage Electrical Power Conductors and Cables'),
        ('26 05 33', 'Raceways and Boxes for Electrical Systems'),
        ('26 09 00', 'Instrumentation and Control for Electrical Systems'),
        ('26 10 00', 'Medium-Voltage Electrical Distribution'),
        ('26 20 00', 'Low-Voltage Electrical Transmission'),
        ('26 22 00', 'Low-Voltage Transformers'),
        ('26 24 00', 'Switchboards, Switchgear, Panel Boards, and Metering'),
        ('26 27 00', 'Low-Voltage Distribution Equipment'),
        ('26 28 00', 'Low-Voltage Circuit Protective Devices'),
        ('26 40 00', 'Electrical and Cathodic Protection'),
        ('26 50 00', 'Lighting'),
        ('26 51 00', 'Interior Lighting'),
        ('26 56 00', 'Exterior Lighting'),
    ],
    '31': [
        ('31 10 00', 'Site Clearing'),
        ('31 11 00', 'Clearing and Grubbing'),
        ('31 14 00', 'Earth Stripping and Stockpiling'),
        ('31 20 00', 'Earth Moving'),
        ('31 22 00', 'Grading'),
        ('31 23 00', 'Excavation and Fill'),
        ('31 24 00', 'Embankments'),
        ('31 25 00', 'Erosion and Sedimentation Controls'),
        ('31 30 00', 'Earthwork Methods'),
        ('31 31 00', 'Soil Treatment'),
        ('31 40 00', 'Shoring and Underpinning'),
        ('31 50 00', 'Excavation Support and Protection'),
        ('31 60 00', 'Special Foundations and Load-Bearing Elements'),
        ('31 63 00', 'Concrete Piles'),
        ('31 68 00', 'Drilled Piers'),
    ],
    '32': [
        ('32 10 00', 'Bases, Ballasts, and Paving'),
        ('32 11 00', 'Base Courses'),
        ('32 12 00', 'Flexible Paving'),
        ('32 13 00', 'Rigid Paving'),
        ('32 14 00', 'Unit Paving'),
        ('32 16 00', 'Curbs and Gutters'),
        ('32 17 00', 'Paving Specialties'),
        ('32 30 00', 'Site Improvements'),
        ('32 31 00', 'Fences and Gates'),
        ('32 32 00', 'Retaining Walls'),
        ('32 80 00', 'Irrigation'),
        ('32 90 00', 'Planting'),
        ('32 91 00', 'Soil Preparation'),
        ('32 92 00', 'Turf and Grasses'),
        ('32 93 00', 'Plants'),
    ],
    '33': [
        ('33 10 00', 'Water Utilities'),
        ('33 11 00', 'Water Utility Distribution Piping'),
        ('33 12 00', 'Water Utility Distribution Equipment'),
        ('33 30 00', 'Sanitary Sewerage Utilities'),
        ('33 31 00', 'Sanitary Utility Sewerage Piping'),
        ('33 40 00', 'Storm Drainage Utilities'),
        ('33 41 00', 'Storm Utility Drainage Piping'),
        ('33 50 00', 'Fuel Distribution Utilities'),
        ('33 70 00', 'Electrical Utilities'),
        ('33 71 00', 'Electrical Utility Transmission and Distribution'),
        ('33 80 00', 'Communications Utilities'),
    ],
}


def seed():
    with app.app_context():
        inserted_l1 = 0
        inserted_l2 = 0

        for code, title in DIVISIONS:
            existing = CSILevel1.query.filter_by(code=code).first()
            if not existing:
                division = CSILevel1(code=code, title=title)
                db.session.add(division)
                db.session.flush()  # get the id before commit
                inserted_l1 += 1
            else:
                division = existing

            sections = SECTIONS.get(code, [])
            for sec_code, sec_title in sections:
                if not CSILevel2.query.filter_by(code=sec_code).first():
                    db.session.add(CSILevel2(
                        csi_level_1_id=division.id,
                        code=sec_code,
                        title=sec_title
                    ))
                    inserted_l2 += 1

        db.session.commit()
        print(f"Done. Inserted {inserted_l1} divisions and {inserted_l2} sections.")
        print("(Existing records were skipped — safe to run again.)")


if __name__ == '__main__':
    seed()
