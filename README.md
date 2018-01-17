# psdm_qs_cli
Python clients for interacting with the PCDS questionnaire

There are a couple of scripts for exporting the questionnaire data into JSON/Excel.
- QSGenerateJSON
- QSGenerateExcelSpreadSheet

The Excel export depends on `openpyxl`; which is not listed as a dependency as I am unclear as to how long this package will be supported. You will need to install it yourself.
