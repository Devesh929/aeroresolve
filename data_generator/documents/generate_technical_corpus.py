"""
data_generator/documents/generate_technical_corpus.py
Generates synthetic technical documents for AeroResolve and loads them into
AERORESOLVE.KNOWLEDGE.TECHNICAL_DOCUMENTS.

ALL DOCUMENTS ARE SYNTHETIC TRAINING / DEMONSTRATION MATERIAL.
NOT REAL FLIGHT OR AIRWORTHINESS MANUALS.
"""

import os
import json
import snowflake.connector

DISCLAIMER_HEADER = (
    "================================================================================\n"
    "SYNTHETIC TRAINING / DEMONSTRATION MATERIAL - NOT FOR REAL FLIGHT USE\n"
    "AeroBharat Airlines (Synthetic Carrier) Decision-Support Platform Technical Corpus\n"
    "================================================================================\n\n"
)

DOCUMENTS = [
    {
        "doc_id": "DOC-TSM-21-2601",
        "title": "TSM 21-26-01: Avionics Ventilation Cooling Loop & Extraction Fan Degradation",
        "ata_chapter": "21",
        "doc_type": "TSM",
        "summary": "Isolation procedures for avionics cooling fan fault FC-21-204. Highlights connector X42 pin micro-fretting as root cause when fan unit replacement fails to eliminate intermittent faults.",
        "content": DISCLAIMER_HEADER + (
            "TASK 21-26-01-810-802: Isolation of Avionics Ventilation System Intermittent Degradation\n\n"
            "1. SYMPTOM DESCRIPTION:\n"
            "Intermittent ECAM alert 'VENT AVIONICS SYS FAULT' or BITE code FC-21-204 triggered during cruise phase.\n"
            "Telemetry shows avionics fan current fluctuating between 1.8A and 2.9A (nominal: 2.1A - 2.4A) with\n"
            "associated avionics rack temperature climb above 42°C. Ground BITE test on ramp typically passes\n"
            "(Ghost Fault signature).\n\n"
            "2. COMMON PITFALL / REPEAT DEFECT CAUTION:\n"
            "WARNING: Swapping the Avionics Extraction Fan unit (COMP-FAN-01) or resetting the Ventilation\n"
            "Controller Computer (VCC) often clears the BITE fault temporarily on the ground. However, if the underlying\n"
            "defect is intermittent micro-fretting on connector X42, the fault will reoccur within 1 to 3 cruise sectors.\n\n"
            "3. STEP-BY-STEP FAULT ISOLATION PROCEDURE:\n"
            "Step 1: Check Ventilation Computer BITE history buffer for code FC-21-204.\n"
            "Step 2: Inspect electrical connector X42 located on the rear interface of shelf 80VU (AeroBharat Narrowbody).\n"
            "Step 3: Perform pin withdrawal test on Pin 4 (Pulse Width Modulation fan control line).\n"
            "        - Required retention force: Minimum 1.2 Newtons.\n"
            "        - If pin retention is loose, micro-fretting corrosion has caused contact resistance under cold/vibration.\n"
            "Step 4: Measure contact resistance across connector X42 pin 4. If resistance > 0.45 Ohms, replace\n"
            "        connector assembly with PART-X42-CONN (Connector Pin Assembly - Silver/Gold Plated).\n"
            "Step 5: Inspect bonding stud ground strap for oxidization.\n\n"
            "4. REQUIRED PARTS & TOOLING:\n"
            "- Part: PART-X42-CONN (Connector Pin Assembly)\n"
            "- Tool: TOOL-CRIMP-01 (High-Density Mil-Spec Pin Extraction & Crimping Tool)\n"
            "- Skill Requirement: Avionics Line Technician (B2 License with ATA 21 endorsement)."
        ),
        "metadata": {
            "ata": "21",
            "system": "Air Conditioning & Ventilation",
            "target_fault_code": "FC-21-204",
            "root_cause_component": "PART-X42-CONN",
            "applicable_models": ["AB-320N", "AB-321XLR"],
            "difficulty_level": "MODERATE"
        }
    },
    {
        "doc_id": "DOC-WIG-24-3804",
        "title": "WIG 24-38-04: Wiring Inspection Guide: Avionics Bay Harness Connector Pin Micro-Fretting",
        "ata_chapter": "24",
        "doc_type": "WIG",
        "summary": "Technical guide on diagnosing intermittent contact resistance and pin micro-fretting caused by thermal cycling and airframe vibration in avionics bay wiring bundles.",
        "content": DISCLAIMER_HEADER + (
            "WIRING INSPECTION GUIDE WIG 24-38-04: Connector Pin Degradation in High-Vibration Envelopes\n\n"
            "1. MECHANISM OF DEFECT:\n"
            "In commercial transport aircraft operating multiple daily sectors, wiring harnesses routed through the\n"
            "forward avionics bay (racks 80VU and 90VU) experience repetitive thermal excursions from -52°C at cruise to\n"
            "+45°C on ramp, combined with low-amplitude structural vibration (frequencies 40Hz - 120Hz).\n"
            "This causes relative microscopic motion (micro-fretting) between mating pin contacts.\n\n"
            "2. PHYSICAL SYMPTOMS:\n"
            "- Tin-lead or gold plating transfer wear exposing copper-nickel alloy substrate.\n"
            "- Formation of non-conductive black/grey oxide film on contact interface.\n"
            "- Under warm ground conditions, static contact resistance appears normal (< 0.1 Ohm).\n"
            "- Under cruise vibration and sub-zero boundary layer temperatures, contact resistance spikes intermittently to 2-10 Ohms,\n"
            "  causing control signal dropout and triggering computer failsafe warnings.\n\n"
            "3. INSPECTION CRITERIA:\n"
            "- Use 10x optical loupe to inspect Pin 4 and Pin 6 on connector X42.\n"
            "- Check for darkened contact track or gold plating flaking.\n"
            "- Conduct push-pull pin retention test using calibrated gauge (minimum holding tension: 1.2N).\n\n"
            "4. REPAIR ACTION:\n"
            "- Cut back damaged wire segment by 15mm.\n"
            "- Install new gold-plated pin contact assembly PART-X42-CONN.\n"
            "- Verify 4-point Kelvin milliohm bridge reading across rebuilt junction."
        ),
        "metadata": {
            "ata": "24",
            "system": "Electrical Power & Wiring",
            "defect_mechanism": "Micro-fretting corrosion",
            "associated_part": "PART-X42-CONN"
        }
    },
    {
        "doc_id": "DOC-EAD-2026-2109",
        "title": "EAD-2026-21-09: Fleet Engineering Advisory: Preventing Recurring Avionics Cooling BITE Alarms",
        "ata_chapter": "21",
        "doc_type": "ENGINEERING_ADVISORY",
        "summary": "Engineering advisory highlighting repetitive unscheduled fan removals on ABR-series aircraft caused by intermittent connector X42 contact faults rather than defective blower fans.",
        "content": DISCLAIMER_HEADER + (
            "FLEET ENGINEERING ADVISORY EAD-2026-21-09\n"
            "SUBJECT: RECURRENT AVIONICS COOLING LOOP BITE FAULTS (ATA 21) & CONNECTOR PIN INTEGRITY\n"
            "APPLICABILITY: AeroBharat Airlines Fleet (ABR Narrowbody Fleet)\n\n"
            "1. BACKGROUND & PROBLEM STATEMENT:\n"
            "Fleet Reliability Engineering has observed an increasing incidence of repeat defects on aircraft\n"
            "exhibiting recurring ECAM fault 'VENT AVIONICS SYS FAULT'. In over 70% of reported cases across Indian stations,\n"
            "line stations replaced the avionics cooling fan (COMP-FAN-01) or swapped the computer. However, within\n"
            "48 operating hours (2 to 5 flight sectors), the same fault recurred on the same tail.\n\n"
            "2. ROOT CAUSE ANALYSIS:\n"
            "Detailed metallurgical and lab teardown revealed the extracted fans were fully serviceable with zero internal defects.\n"
            "The root cause was isolated to electrical connector X42, pin 4, which had developed micro-fretting corrosion\n"
            "and loss of spring tension. The fault only triggered when altitude exceeded 28,000 ft and outside air temperature\n"
            "dropped below -35°C, masking the defect during ground ramp tests.\n\n"
            "3. MANDATORY ACTION FOR LINE & BASE MAINTENANCE:\n"
            "- On any aircraft recording two or more occurrences of FC-21-204 within 30 days, DO NOT swap the fan unit\n"
            "  as a first action.\n"
            "- Line maintenance must immediately inspect Connector X42 and replace the pin contacts with PART-X42-CONN.\n"
            "- Ensure station stock of PART-X42-CONN is pre-positioned at primary line hubs (DEL, BOM, BLR).\n"
            "- Perform post-installation ground test followed by in-flight verification for 3 consecutive sectors."
        ),
        "metadata": {
            "ata": "21",
            "advisory_number": "EAD-2026-21-09",
            "effective_date": "2026-09-15",
            "urgency": "HIGH",
            "prevents_repeat_defect": True
        }
    },
    {
        "doc_id": "DOC-SBN-2026-21002",
        "title": "SBN-2026-21-002: Service Bulletin: Spares Pre-Positioning & Rapid Repositioning Guidelines",
        "ata_chapter": "21",
        "doc_type": "SERVICE_BULLETIN",
        "summary": "Logistics and materials dispatch bulletin establishing stock allocations for critical connector kits and expediting protocols between Mumbai (BOM) central stores and line stations.",
        "content": DISCLAIMER_HEADER + (
            "SERVICE BULLETIN SBN-2026-21-002\n"
            "LOGISTICS DISPATCH: AVIONICS CONNECTOR KITS & EXPEDITED INTER-STATION REPOSITIONING\n\n"
            "1. INVENTORY ALLOCATION:\n"
            "To mitigate AOG grounding risks resulting from recurring ATA 21 ventilation faults, the following minimum\n"
            "inventory levels of PART-X42-CONN (Connector Pin Assembly) must be maintained:\n"
            "- Mumbai Central Stores (BOM): Minimum 3 units (Central buffer)\n"
            "- Delhi Hub (DEL): Minimum 2 units\n"
            "- Bengaluru Hub (BLR): Minimum 1 unit\n\n"
            "2. EMERGENCY REPOSITIONING PROTOCOL:\n"
            "When a line station (such as DEL) experiences a zero-stock condition (stockout) with an inbound aircraft\n"
            "requiring connector repair:\n"
            "- Central Spares Control must immediately dispatch the required kit from BOM via the next scheduled commercial flight.\n"
            "- Estimated flight transit BOM-DEL: 2.2 hours.\n"
            "- Expedited ramp-side cargo handover buffer: 45 minutes.\n"
            "- Total repositioning cycle: Approximately 3.0 to 3.5 hours.\n"
            "- Part reservation must be placed prior to inbound aircraft touchdown."
        ),
        "metadata": {
            "ata": "21",
            "spares_logistics": True,
            "origin_hub": "BOM",
            "dest_hub": "DEL"
        }
    },
    {
        "doc_id": "DOC-LOG-DEL-20261005",
        "title": "LOG-DEL-20261005: Line Maintenance Handover Log: DEL Night Shift Tech Log Entry",
        "ata_chapter": "21",
        "doc_type": "SHIFT_HANDOVER",
        "summary": "Handover notes from Delhi maintenance crew regarding ABR-017 first cooling fault. Documents initial fan unit swap and inability to reproduce the fault on the ground.",
        "content": DISCLAIMER_HEADER + (
            "AEROBHARAT AIRLINES LINE MAINTENANCE SHIFT HANDOVER NOTE\n"
            "STATION: DEL (Indira Gandhi International Airport, New Delhi)\n"
            "DATE: 2026-10-05 | SHIFT: NIGHT (22:00 - 06:00 IST)\n"
            "LEAD ENGINEER: R. K. Sharma (License #DEL-ENG-1082)\n\n"
            "ENTRY FOR AIRCRAFT ABR-017 (FLIGHT AB-458 / AB-159):\n"
            "Pilot reported ECAM 'VENT AVIONICS SYS FAULT' occurred passing FL320 inbound to DEL.\n"
            "Ground inspection performed at Gate 32.\n"
            "- Ran onboard Ventilation Computer BITE test: RESULT NORMAL / NO CURRENT FAULT ACTIVE (Ghost fault).\n"
            "- Following Standard TSM step 1, removed extraction fan COMP-FAN-01 and installed replacement from DEL stock.\n"
            "- DEL stock for COMP-FAN-01 is now depleted (0 remaining).\n"
            "- Did not inspect connector X42 due to tight 45-minute turnaround window.\n"
            "- Aircraft released for morning schedule. Advised next station to monitor if fault reoccurs."
        ),
        "metadata": {
            "station": "DEL",
            "aircraft_id": "ABR-017",
            "ata": "21",
            "shift": "NIGHT"
        }
    },
    {
        "doc_id": "DOC-LOG-BOM-20261004",
        "title": "LOG-BOM-20261004: Line Maintenance Handover Log: BOM Line Station Tech Log Entry",
        "ata_chapter": "21",
        "doc_type": "SHIFT_HANDOVER",
        "summary": "Historical handover log from Mumbai Line Station for ABR-017 noting transient fan current warning and computer reset.",
        "content": DISCLAIMER_HEADER + (
            "AEROBHARAT AIRLINES LINE MAINTENANCE SHIFT HANDOVER NOTE\n"
            "STATION: BOM (Chhatrapati Shivaji Maharaj International Airport, Mumbai)\n"
            "DATE: 2026-10-04 | SHIFT: AFTERNOON (14:00 - 22:00 IST)\n"
            "LEAD ENGINEER: V. Menon (License #BOM-ENG-2401)\n\n"
            "ENTRY FOR AIRCRAFT ABR-017:\n"
            "Flight crew debrief noted brief amber ventilation alert during cruise descent.\n"
            "- Monitored avionics fan current telemetry: minor blip to 2.85A recorded at 31,000 ft.\n"
            "- Reset Ventilation Control Computer circuit breaker (CB 49VU/D02).\n"
            "- Built-in test executed cleanly. No further action taken at BOM.\n"
            "- Released for scheduled evening rotation."
        ),
        "metadata": {
            "station": "BOM",
            "aircraft_id": "ABR-017",
            "ata": "21",
            "shift": "AFTERNOON"
        }
    },
    {
        "doc_id": "DOC-TSM-24-3102",
        "title": "TSM 24-31-02: AC Generator Bus Switching Transients & Bus Tie Contactor Isolation",
        "ata_chapter": "24",
        "doc_type": "TSM",
        "summary": "Troubleshooting electrical power transients and bus voltage spikes during APU to Engine Generator transfer.",
        "content": DISCLAIMER_HEADER + (
            "TASK 24-31-02-810-801: Electrical Bus Switching Transient Analysis\n\n"
            "1. SYMPTOM DESCRIPTION:\n"
            "Bus tie contactor chattering or momentary voltage drop below 110VAC during engine start sequence.\n"
            "2. ISOLATION PROCEDURE:\n"
            "- Inspect Generator Control Unit (GCU) internal fault log.\n"
            "- Check auxiliary contacts on Bus Tie Contactor 1X.\n"
            "- Measure ground return bonding between GCU rack and aircraft frame (Max: 2.5 milliohms)."
        ),
        "metadata": {
            "ata": "24",
            "system": "Electrical Power"
        }
    },
    {
        "doc_id": "DOC-TSM-29-1105",
        "title": "TSM 29-11-05: Hydraulic Green System Low Quantity & Pressure Fluctuation",
        "ata_chapter": "29",
        "doc_type": "TSM",
        "summary": "Isolation procedures for Green hydraulic reservoir quantity loss under high aerodynamic loading.",
        "content": DISCLAIMER_HEADER + (
            "TASK 29-11-05-810-804: Hydraulic Reservoir Fluid Loss Isolation\n\n"
            "1. SYMPTOM DESCRIPTION:\n"
            "Fluid quantity drops by >8% during cruise altitude but stabilizes on ground.\n"
            "2. ISOLATION PROCEDURE:\n"
            "- Inspect case drain filter on Engine-Driven Pump (EDP 1).\n"
            "- Check bleed air pressurization manifold check valve.\n"
            "- If reservoir pressurization drops below 45 psi, fluid cavitates during high demand."
        ),
        "metadata": {
            "ata": "29",
            "system": "Hydraulic Power"
        }
    },
    {
        "doc_id": "DOC-TSM-73-2103",
        "title": "TSM 73-21-03: Fuel Flow Metering Valve Feedback Discrepancy",
        "ata_chapter": "73",
        "doc_type": "TSM",
        "summary": "Troubleshooting split fuel flow indication and FADEC channel cross-talk errors.",
        "content": DISCLAIMER_HEADER + (
            "TASK 73-21-03-810-802: Engine Fuel Metering Valve (FMV) Calibration\n\n"
            "1. SYMPTOM DESCRIPTION:\n"
            "Dual engine fuel flow differential exceeding 120 kg/h with matched N1 fan speeds.\n"
            "2. ISOLATION PROCEDURE:\n"
            "- Read FADEC channel A and B resolver angle signals.\n"
            "- Perform stepper motor calibration test via MCDU maintenance menu."
        ),
        "metadata": {
            "ata": "73",
            "system": "Engine Fuel and Control"
        }
    },
    {
        "doc_id": "DOC-TSM-32-4201",
        "title": "TSM 32-42-01: Main Landing Gear Brake Heat Dissipation & Return Line Inspection",
        "ata_chapter": "32",
        "doc_type": "TSM",
        "summary": "Isolation procedures for asymmetric brake temperatures following high gross weight turnaround.",
        "content": DISCLAIMER_HEADER + (
            "TASK 32-42-01-810-803: Carbon Brake Thermal Management\n\n"
            "1. SYMPTOM DESCRIPTION:\n"
            "Left main gear brake temperature exceeds right main gear brake by >65°C on taxi-in.\n"
            "2. ISOLATION PROCEDURE:\n"
            "- Inspect brake cooling fan fuse and wiring harness.\n"
            "- Check shuttle valve for sticking or return line restriction."
        ),
        "metadata": {
            "ata": "32",
            "system": "Landing Gear"
        }
    }
]

def load_technical_documents():
    print("Connecting to Snowflake to load synthetic technical documents...")
    token_path = os.path.expanduser('~/.snowflake/token.jwt')
    conn = snowflake.connector.connect(
        user='DEVESH929',
        account='YGUIPVK-XK89675',
        authenticator='PROGRAMMATIC_ACCESS_TOKEN',
        token_file_path=token_path,
        role='AERORESOLVE_DEV',
        warehouse='AERORESOLVE_WH',
        database='AERORESOLVE',
        schema='KNOWLEDGE'
    )
    cur = conn.cursor()

    print("Creating table AERORESOLVE.KNOWLEDGE.TECHNICAL_DOCUMENTS...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS AERORESOLVE.KNOWLEDGE.TECHNICAL_DOCUMENTS (
            doc_id VARCHAR(50) PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            ata_chapter VARCHAR(10) NOT NULL,
            doc_type VARCHAR(50) NOT NULL,
            summary VARCHAR(1000) NOT NULL,
            content VARCHAR(16777216) NOT NULL,
            metadata VARIANT,
            created_ts TIMESTAMP_NTZ NOT NULL DEFAULT CURRENT_TIMESTAMP()
        )
    """)

    insert_sql = """
        MERGE INTO AERORESOLVE.KNOWLEDGE.TECHNICAL_DOCUMENTS target
        USING (SELECT %s AS doc_id, %s AS title, %s AS ata_chapter, %s AS doc_type, %s AS summary, %s AS content, PARSE_JSON(%s) AS metadata) source
        ON target.doc_id = source.doc_id
        WHEN MATCHED THEN
            UPDATE SET target.title = source.title,
                       target.ata_chapter = source.ata_chapter,
                       target.doc_type = source.doc_type,
                       target.summary = source.summary,
                       target.content = source.content,
                       target.metadata = source.metadata
        WHEN NOT MATCHED THEN
            INSERT (doc_id, title, ata_chapter, doc_type, summary, content, metadata)
            VALUES (source.doc_id, source.title, source.ata_chapter, source.doc_type, source.summary, source.content, source.metadata)
    """

    for doc in DOCUMENTS:
        cur.execute(insert_sql, (
            doc["doc_id"],
            doc["title"],
            doc["ata_chapter"],
            doc["doc_type"],
            doc["summary"],
            doc["content"],
            json.dumps(doc["metadata"])
        ))
        print(f"Loaded: {doc['doc_id']} - {doc['title'][:50]}...")

    cur.execute("SELECT COUNT(*) FROM AERORESOLVE.KNOWLEDGE.TECHNICAL_DOCUMENTS")
    total = cur.fetchone()[0]
    print(f"\nSuccessfully loaded {total} technical documents into AERORESOLVE.KNOWLEDGE.TECHNICAL_DOCUMENTS!")

    cur.close()
    conn.close()

if __name__ == '__main__':
    load_technical_documents()
