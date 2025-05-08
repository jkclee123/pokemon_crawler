"""
Pokemon Crawler Main Script

This script runs the complete Pokemon data pipeline:
1. Scrapes Pokemon evolution chains to identify fully evolved Pokemon
2. Generates formatted PDF files for each Pokemon
"""

import os
import sys
import time
from pathlib import Path

# Import modules from the project files
import get_links
import write_pdf

def create_directories():
    """Create necessary directories if they don't exist."""
    pdf_dir = Path('pokemon_pdfs')
    pdf_dir.mkdir(exist_ok=True)

def main():
    """Main execution function that runs the complete pipeline."""
    print("Starting Pokemon Crawler...")
    
    # Create necessary directories
    create_directories()
    
    try:
        # # Step 1: Scrape and collect URLs of fully evolved Pokemon
        # print("\nStep 1: Collecting fully evolved Pokemon URLs...")
        # get_links.main()
        
        # # Check if the output file was created
        # if not Path(get_links.OUTPUT_FILE).exists():
        #     print(f"Error: {get_links.OUTPUT_FILE} file was not created. Exiting.")
        #     sys.exit(1)
            
        # # Add a small delay to ensure file is fully written
        # time.sleep(1)
        
        # Step 2: Generate PDF files for each Pokemon
        print("\nStep 2: Generating PDF files for Pokemon...")
        write_pdf.main()
        
        # Count generated PDF files
        pdf_count = len(list(Path(write_pdf.OUTPUT_DIR).glob('*.pdf')))
        print(f"\nCompleted! Generated {pdf_count} Pokemon PDF files.")
        print(f"PDF files are available in the '{write_pdf.OUTPUT_DIR}' directory.")
        
    except Exception as e:
        print(f"\nAn error occurred during execution: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
