import openpyxl
import sys

def analyze_excel(file_path):
    try:
        wb = openpyxl.load_workbook(file_path, data_only=True)
        print(f"Sheet names: {wb.sheetnames}")
        
        for sheet_name in wb.sheetnames:
            print(f"\n--- Sheet: {sheet_name} ---")
            sheet = wb[sheet_name]
            
            # Print first 5 rows to identify headers
            print("First 5 rows:")
            for i, row in enumerate(sheet.iter_rows(values_only=True)):
                if i >= 5: break
                # Filter out None values for cleaner output
                cleaned_row = [str(cell).strip() if cell is not None else "" for cell in row]
                print(f"Row {i+1}: {cleaned_row}")
                
    except Exception as e:
        print(f"Error reading excel: {e}")

if __name__ == "__main__":
    analyze_excel(r"e:\MYPJ\HSC\01-تعمیرات شاسی و ساخت.xlsx")
