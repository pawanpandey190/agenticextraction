
import logging
from passport_agent.services.mrz_service import MRZService

# Setup logging
logging.basicConfig(level=logging.INFO)

def test_collision_repair():
    service = MRZService()
    
    # Case: BS vs 85 collision
    # 120026BS -> 12002685
    # BS is common OCR error for 85
    
    # Let's say MRZ has 120026BS and it PASSES checksum (hypothetical collision)
    # But VIZ has 12002685.
    
    mrz_pnum = "120026BS"
    viz_pnum = "12002685"
    
    # We need a line 2 that has this passport number
    # TD3 line 2: 9 chars + 1 check + 3 iso + 6 dob + 1 check + 1 sex + 6 exp + 1 check + 14 personal + 1 check + 1 total
    # 120026BS< 8 ...
    
    # Simple check digit for 12002685:
    # 1(7) 2(3) 0(1) 0(7) 2(3) 6(1) 8(7) 5(3)
    # 7 + 6 + 0 + 0 + 6 + 6 + 56 + 15 = 96. 96 % 10 = 6.
    
    line2_viz = "12002685<6NGA9001011M2501017<<<<<<<<<<<<<<26"
    
    # Check digit for 120026BS (hypothetical collision)
    # B=11, S=28
    # 1(7) 2(3) 0(1) 0(7) 2(3) 6(1) B(7) S(3)
    # 7 + 6 + 0 + 0 + 6 + 6 + 77 + 84 = 186. 186 % 10 = 6.
    # IT IS A COLLISION! Both B/S and 8/5 with same check 6 pass.
    
    line2_mrz = "120026BS<6NGA9001011M2501017<<<<<<<<<<<<<<26"
    
    print(f"\nTesting collision repair:")
    print(f"MRZ Passport: {mrz_pnum} (Valid Checksum: 6)")
    print(f"VIZ Passport: {viz_pnum} (Valid Checksum: 6)")
    
    # Attempt repair with VIZ witness
    repaired = service._repair_line2(line2_mrz, viz_witness=viz_pnum)
    
    print(f"Repaired line2: {repaired}")
    
    if "12002685" in repaired:
        print("SUCCESS: MRZ was repaired to match VIZ witness!")
    else:
        print("FAILURE: MRZ was not repaired.")

if __name__ == "__main__":
    test_collision_repair()
