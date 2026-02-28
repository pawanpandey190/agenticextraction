
import sys
import os

# Add the src directories to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../passport_analysis_agent/src")))

from passport_agent.utils.mrz_utils import validate_check_digit, calculate_check_digit

def test_collision():
    # Correct data
    pnum_correct = "12002685"
    check_digit = calculate_check_digit(pnum_correct)
    print(f"Correct: {pnum_correct}, Check Digit: {check_digit}")
    
    # Misread data (B instead of 8, S instead of 5)
    pnum_misread = "120026BS"
    is_valid = validate_check_digit(pnum_misread, check_digit)
    print(f"Misread: {pnum_misread}, Valid with same check digit: {is_valid}")
    
    if is_valid:
        print("\nCONFIRMED: Checksum collision detected!")
        print(f"Both {pnum_correct} and {pnum_misread} are valid for check digit {check_digit}")
    else:
        print("\nNOT A COLLISION: My manual calculation was wrong or the weights are different.")

if __name__ == "__main__":
    test_collision()
