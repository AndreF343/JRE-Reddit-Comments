@echo off
cd "C:\Users\Administrator\Desktop\"
jupyter nbconvert --to script ec2_jre_dashboard.ipynb && python ec2_jre_dashboard.py
