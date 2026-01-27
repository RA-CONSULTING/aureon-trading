
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
try:
    from aureon_queen_hive_mind import QueenHiveMind
    print("Import successful")
    
    queen = QueenHiveMind()
    print("Instantiation successful")
    
    if hasattr(queen, 'metrics'):
        print(f"Metrics available: {queen.metrics.keys()}")
    else:
        print("ERROR: No metrics attribute found on queen instance")
        
except Exception as e:
    print(f"CRASH: {e}")
    import traceback
    traceback.print_exc()
