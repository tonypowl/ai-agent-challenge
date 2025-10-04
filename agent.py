#take input -> --target _bank_name_ (in this case the icici files)
#check the files in data folder (.pdf) and generates a icic_parser.py with a parse() function 
#import the new parse funtion run it on the .pdf and compare the new csv with the old csv 
#if inaccurate then retry atmost of 3 times

#nodes : plan (check for files) - generate_code (obtain parse func) - run_tests (compare with old csv) - self_fix (if inaccurate and try<=3)