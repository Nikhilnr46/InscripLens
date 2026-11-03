"""Regression checks for location leakage through extended inscription names."""
from compare_training_scope import excluded_site

assert excluded_site('Begur Nagareshwara Temple 1400CE Inscription',{'begur'})
assert excluded_site('Begur 900CE Hero Stone',{'begur'})
assert not excluded_site('Begurana 900CE Inscription',{'begur'})
assert not excluded_site('Halmidi 450CE Inscription',{'begur'})
print('PASS exact site, extended site name, and unrelated prefix boundaries')
