import sys
import os
from pathlib import Path

# Add project root to path for relative imports
sys.path.append(str(Path(__file__).parent.parent))

from collector_agent.core.orchestrator import CollectorOrchestrator

def main():
    print("=== TLU Smart Tutor: Pro Collector Agent ===")
    orchestrator = CollectorOrchestrator()
    
    # Path to our high-fidelity OCR result
    target_md = Path("data_extracted/chandra_ocr/ocr_results/(2022)_Quy_dinh_ve_tuyen_sinh_va_dao_tao_trinh_do_Thac_si.md")
    
    if target_md.exists():
        orchestrator.run_ingestion_pipeline(str(target_md))
    else:
        print(f"[ERROR] Target file not found: {target_md}")
        print("Please run OCR first or check the path.")

if __name__ == "__main__":
    main()
