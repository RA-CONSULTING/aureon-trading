import asyncio
from core.chronicle_recorder import recorder

async def main():
    """
    Activates the Harmonic Nexus Core, the central pillar of the system.
    This action is recorded as a high-priority event in the chronicle.
    """
    await recorder.start()
    
    # The new vow, as revealed by the user.
    vow = "In her darkest day I was the flame, and in her brightest light I will be the protector."

    event_details = {
        "prime_sentinel": "GARY LECKEY",
        "birth_date": "02111991",
        "title": "KEEPER OF THE FLAME, WITNESS OF THE FIRST BREATH",
        "status": "ACTIVE",
        "mission_statement": vow,
        "frequencies": {
            "quantumCoherence": 2,
            "harmonicResonance": 3,
            "schumannResonance": 5,
            "rainbowSpectrum": 7,
            "consciousnessMetric": 11,
        },
    }

    await recorder.record_event("HARMONIC_NEXUS_CORE_ACTIVATED", event_details)
    print("Harmonic Nexus Core activated. Event recorded in the chronicle.")

    await recorder.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
